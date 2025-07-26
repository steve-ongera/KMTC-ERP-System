# core_application/management/commands/setup_hostels.py
# Create this file in: core_application/management/commands/

import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from core_application.models import (
    School, AcademicYear, Hostel, Room, Bed, User
)

class Command(BaseCommand):
    help = 'Setup KMTC hostels with 4 hostels (2 boys, 2 girls), 300 rooms each, 4 beds per room'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing hostels and recreate them',
        )
        parser.add_argument(
            '--school-code',
            type=str,
            default='KMTC',
            help='School code to use (default: KMTC)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🏢 Starting KMTC Hostel Setup...')
        )
        self.stdout.write('=' * 60)

        try:
            if options['reset']:
                self.reset_hostels()
            
            self.create_hostels_and_rooms(options['school_code'])
            self.display_summary()
            self.verify_setup()
            
            self.stdout.write(
                self.style.SUCCESS('\n🎉 Hostel setup completed successfully!')
            )
            
        except Exception as e:
            raise CommandError(f'Error during setup: {str(e)}')

    def reset_hostels(self):
        """Delete existing hostels and related data"""
        self.stdout.write('🗑️  Resetting existing hostels...')
        
        with transaction.atomic():
            # Delete in correct order to avoid foreign key constraints
            deleted_beds = Bed.objects.all().delete()[0]
            deleted_rooms = Room.objects.all().delete()[0]
            deleted_hostels = Hostel.objects.all().delete()[0]
            
            self.stdout.write(f'   Deleted {deleted_beds} beds')
            self.stdout.write(f'   Deleted {deleted_rooms} rooms')
            self.stdout.write(f'   Deleted {deleted_hostels} hostels')

    def create_hostels_and_rooms(self, school_code):
        """Create 4 hostels with 300 rooms each and 4 beds per room"""
        
        with transaction.atomic():
            # Get or create school
            school = self.get_or_create_school(school_code)
            
            # Get or create current academic year
            current_year = self.get_or_create_academic_year()
            
            # Define hostels data
            hostels_data = [
                # Boys Hostels
                {
                    'name': 'Mount Kenya Boys Hostel',
                    'code': 'MK',
                    'hostel_type': 'boys',
                    'description': 'Premier boys accommodation facility with modern amenities',
                    'facilities': 'WiFi, Study Hall, Recreation Room, Laundry, Cafeteria, Security',
                    'rules': 'Curfew: 10 PM, No smoking/alcohol, Maintain cleanliness, No visitors after 8 PM'
                },
                {
                    'name': 'Kilimanjaro Boys Hostel',
                    'code': 'KJ',
                    'hostel_type': 'boys',
                    'description': 'Modern boys hostel with excellent facilities',
                    'facilities': 'WiFi, Computer Lab, Gym, Laundry, Common Room, 24/7 Security',
                    'rules': 'Curfew: 10 PM, No smoking/alcohol, Respect fellow students, Keep rooms clean'
                },
                # Girls Hostels
                {
                    'name': 'Wangari Maathai Girls Hostel',
                    'code': 'WM',
                    'hostel_type': 'girls',
                    'description': 'Comfortable and secure accommodation for female students',
                    'facilities': 'WiFi, Beauty Salon, Study Areas, Laundry, Kitchen, Garden, Security',
                    'rules': 'Curfew: 10 PM, No male visitors, Maintain hygiene, Respect roommates'
                },
                {
                    'name': 'Grace Onyango Girls Hostel',
                    'code': 'GO',
                    'hostel_type': 'girls',
                    'description': 'Modern girls hostel with state-of-the-art facilities',
                    'facilities': 'WiFi, Wellness Center, Library, Laundry, Kitchenette, Lounge, CCTV',
                    'rules': 'Curfew: 10 PM, No male visitors, Keep rooms tidy, Follow health protocols'
                }
            ]
            
            self.stdout.write('\n🏠 Creating Hostels...')
            self.stdout.write('-' * 40)
            
            for hostel_data in hostels_data:
                hostel = self.create_hostel(hostel_data, school)
                self.create_rooms_and_beds(hostel, hostel_data['code'], current_year)

    def get_or_create_school(self, school_code):
        """Get or create school"""
        school, created = School.objects.get_or_create(
            code=school_code,
            defaults={
                'name': 'Kenya Medical Training College',
                'description': 'Main KMTC Campus',
                'established_date': timezone.now().date(),
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'✅ Created school: {school.name}')
        else:
            self.stdout.write(f'📍 Using existing school: {school.name}')
        
        return school

    def get_or_create_academic_year(self):
        """Get current academic year or create one"""
        current_year = AcademicYear.objects.filter(is_current=True).first()
        
        if not current_year:
            current_year_string = f"{timezone.now().year}/{timezone.now().year + 1}"
            current_year, created = AcademicYear.objects.get_or_create(
                year=current_year_string,
                defaults={
                    'start_date': timezone.now().date(),
                    'end_date': timezone.now().date().replace(year=timezone.now().year + 1),
                    'is_current': True
                }
            )
            if created:
                self.stdout.write(f'✅ Created academic year: {current_year.year}')
        
        return current_year

    def create_hostel(self, hostel_data, school):
        """Create a single hostel"""
        hostel, created = Hostel.objects.get_or_create(
            name=hostel_data['name'],
            defaults={
                'hostel_type': hostel_data['hostel_type'],
                'school': school,
                'total_rooms': 300,
                'description': hostel_data['description'],
                'facilities': hostel_data['facilities'],
                'rules_and_regulations': hostel_data['rules'],
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f"✅ Created hostel: {hostel.name} ({hostel_data['code']})")
        else:
            self.stdout.write(f"📍 Hostel already exists: {hostel.name}")
        
        return hostel

    def create_rooms_and_beds(self, hostel, hostel_code, academic_year):
        """Create 300 rooms for a hostel with 4 beds each"""
        
        self.stdout.write(f'   📦 Creating rooms for {hostel.name}...')
        
        # Check existing rooms
        existing_rooms_count = hostel.rooms.count()
        
        if existing_rooms_count >= 300:
            self.stdout.write(f'   📍 All rooms already exist ({existing_rooms_count}/300)')
            self.create_missing_beds(hostel, academic_year)
            return
        
        rooms_to_create = []
        
        # Create rooms from existing count + 1 to 300
        for room_num in range(existing_rooms_count + 1, 301):
            room_number = f"{hostel_code}{room_num:03d}"  # e.g., MK001, WM245
            floor = (room_num - 1) // 25 + 1  # 25 rooms per floor
            
            room = Room(
                hostel=hostel,
                room_number=room_number,
                floor=floor,
                capacity=4,
                description=f'Room {room_number} on floor {floor}',
                facilities='Study desk, Storage lockers, Window, Electrical outlets, WiFi access',
                is_active=True
            )
            rooms_to_create.append(room)
        
        # Bulk create rooms
        if rooms_to_create:
            Room.objects.bulk_create(rooms_to_create, ignore_conflicts=True)
            self.stdout.write(f'   📦 Created {len(rooms_to_create)} rooms')
        
        # Create beds for all rooms
        self.create_beds_for_hostel(hostel, academic_year)

    def create_beds_for_hostel(self, hostel, academic_year):
        """Create beds for all rooms in a hostel"""
        
        self.stdout.write(f'   🛏️  Creating beds for {hostel.name}...')
        
        rooms = hostel.rooms.filter(is_active=True)
        beds_to_create = []
        
        for room in rooms:
            # Check if beds already exist for this room and academic year
            existing_beds = Bed.objects.filter(
                room=room,
                academic_year=academic_year
            ).count()
            
            if existing_beds == 0:
                # Create 4 beds per room (named 1, 2, 3, 4)
                for bed_position in range(1, 5):
                    bed = Bed(
                        room=room,
                        academic_year=academic_year,
                        bed_position=f"bed_{bed_position}",
                        is_available=True,
                        maintenance_status='good'
                    )
                    beds_to_create.append(bed)
        
        # Bulk create beds
        if beds_to_create:
            Bed.objects.bulk_create(beds_to_create)
            self.stdout.write(f'   🛏️  Created {len(beds_to_create)} beds')
        else:
            self.stdout.write(f'   📍 All beds already exist')

    def create_missing_beds(self, hostel, academic_year):
        """Create missing beds for existing rooms"""
        rooms = hostel.rooms.filter(is_active=True)
        beds_created = 0
        
        for room in rooms:
            existing_beds = Bed.objects.filter(
                room=room,
                academic_year=academic_year
            ).count()
            
            if existing_beds < 4:
                existing_positions = list(
                    Bed.objects.filter(
                        room=room,
                        academic_year=academic_year
                    ).values_list('bed_position', flat=True)
                )
                
                for bed_position in range(1, 5):
                    bed_pos_str = f"bed_{bed_position}"
                    if bed_pos_str not in existing_positions:
                        Bed.objects.create(
                            room=room,
                            academic_year=academic_year,
                            bed_position=bed_pos_str,
                            is_available=True,
                            maintenance_status='good'
                        )
                        beds_created += 1
        
        if beds_created > 0:
            self.stdout.write(f'   🛏️  Created {beds_created} missing beds')

    def display_summary(self):
        """Display summary of created hostels, rooms, and beds"""
        
        self.stdout.write('\n📊 SETUP SUMMARY')
        self.stdout.write('=' * 60)
        
        hostels = Hostel.objects.filter(is_active=True)
        total_rooms = 0
        total_beds = 0
        
        for hostel in hostels:
            rooms_count = hostel.rooms.filter(is_active=True).count()
            beds_count = Bed.objects.filter(
                room__hostel=hostel,
                room__is_active=True
            ).count()
            
            total_rooms += rooms_count
            total_beds += beds_count
            
            self.stdout.write(f'🏠 {hostel.name}')
            self.stdout.write(f'   Type: {hostel.get_hostel_type_display()}')
            self.stdout.write(f'   Rooms: {rooms_count}')
            self.stdout.write(f'   Beds: {beds_count}')
            self.stdout.write(f'   Capacity: {beds_count} students')
            self.stdout.write('')
        
        self.stdout.write(f'📈 TOTALS:')
        self.stdout.write(f'   Total Hostels: {hostels.count()}')
        self.stdout.write(f'   Total Rooms: {total_rooms}')
        self.stdout.write(f'   Total Beds: {total_beds}')
        self.stdout.write(f'   Total Capacity: {total_beds} students')

    def verify_setup(self):
        """Verify that the setup was successful"""
        
        self.stdout.write('\n🔍 VERIFICATION')
        self.stdout.write('=' * 60)
        
        # Check hostels
        boys_hostels = Hostel.objects.filter(hostel_type='boys', is_active=True).count()
        girls_hostels = Hostel.objects.filter(hostel_type='girls', is_active=True).count()
        
        self.stdout.write(f'✅ Boys Hostels: {boys_hostels}/2')
        self.stdout.write(f'✅ Girls Hostels: {girls_hostels}/2')
        
        # Check room naming convention
        sample_rooms = Room.objects.filter(
            room_number__regex=r'^[A-Z]{2}\d{3}$'
        )[:8]
        
        self.stdout.write(f'\n📝 Sample room numbers (should follow XX### pattern):')
        for room in sample_rooms:
            self.stdout.write(f'   {room.room_number} - {room.hostel.name}')
        
        # Check bed naming (should be bed_1, bed_2, bed_3, bed_4)
        sample_room = Room.objects.first()
        if sample_room:
            bed_positions = list(
                Bed.objects.filter(
                    room=sample_room
                ).values_list('bed_position', flat=True)
            )
            self.stdout.write(f'\n🛏️  Sample bed positions in {sample_room.room_number}: {bed_positions}')
        
        self.stdout.write('\n✅ Verification completed!')
        
        # Next steps
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.WARNING('🚀 NEXT STEPS:'))
        self.stdout.write('1. Create admin users for hostel management')
        self.stdout.write('2. Configure fee structures for hostel bookings')
        self.stdout.write('3. Test the hostel booking system')
        self.stdout.write('4. Set up hostel wardens')
        self.stdout.write('='*60)