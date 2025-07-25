from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from coreapplication.models import Hostel, HostelRoom, HostelBed


class Command(BaseCommand):
    help = 'Creates predefined hostels, rooms, and beds'

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # Create or get hostel warden
        warden, created = User.objects.get_or_create(
            username='hostel_warden',
            defaults={
                'email': 'warden@university.edu',
                'first_name': 'Hostel',
                'last_name': 'Warden',
                'is_staff': True,
                'is_superuser': True,
                'user_type': 'staff'
            }
        )
        if created:
            warden.set_password('warden123')
            warden.save()
            self.stdout.write(self.style.SUCCESS("Created hostel warden user."))
        else:
            self.stdout.write("Warden already exists.")

        hostels_data = [
            {
                'name': 'Kibaki Hostel',
                'hostel_type': 'boys',
                'initials': 'KI',
                'total_rooms': 400,
                'description': 'Premium boys hostel with modern amenities',
                'facilities': 'WiFi, Study Room, Gym, Laundry',
                'rules': 'Strict curfew at 10PM, No visitors after 8PM'
            },
            {
                'name': 'Obama Hostel',
                'hostel_type': 'boys',
                'initials': 'OB',
                'total_rooms': 400,
                'description': 'Standard boys hostel with basic amenities',
                'facilities': 'WiFi, Common Room',
                'rules': 'Curfew at 11PM, Limited visitors'
            },
            {
                'name': 'Thatcher Hostel',
                'hostel_type': 'girls',
                'initials': 'TH',
                'total_rooms': 400,
                'description': 'Premium girls hostel with security',
                'facilities': 'WiFi, Study Room, Salon, Laundry',
                'rules': 'Strict curfew at 9PM, No male visitors'
            },
            {
                'name': 'Wambui Hostel',
                'hostel_type': 'girls',
                'initials': 'WA',
                'total_rooms': 400,
                'description': 'Standard girls hostel',
                'facilities': 'WiFi, Common Room',
                'rules': 'Curfew at 10PM, Limited visitors'
            }
        ]

        for hostel_data in hostels_data:
            # Check if hostel already exists
            existing_hostel = Hostel.objects.filter(initials=hostel_data['initials']).first()
            if existing_hostel:
                self.stdout.write(self.style.WARNING(f"Hostel with initials {hostel_data['initials']} already exists. Skipping..."))
                continue

            self.stdout.write(f"Creating {hostel_data['name']}...")

            hostel = Hostel.objects.create(
                name=hostel_data['name'],
                hostel_type=hostel_data['hostel_type'],
                initials=hostel_data['initials'],
                total_rooms=hostel_data['total_rooms'],
                warden=warden,
                description=hostel_data['description'],
                facilities=hostel_data['facilities'],
                rules=hostel_data['rules'],
                is_active=True
            )

            rooms_created = 0
            beds_created = 0

            for room_num in range(1, hostel_data['total_rooms'] + 1):
                formatted_room_num = f"{room_num:03d}"
                room_name = f"{hostel.initials}{formatted_room_num}"
                floor = (room_num - 1) // 20 + 1

                # Check if room already exists
                existing_room = HostelRoom.objects.filter(
                    hostel=hostel,
                    room_number=formatted_room_num
                ).first()
                
                if existing_room:
                    self.stdout.write(self.style.WARNING(f"Room {room_name} already exists. Skipping..."))
                    continue

                room = HostelRoom.objects.create(
                    hostel=hostel,
                    room_number=formatted_room_num,
                    room_name=room_name,
                    floor=floor,
                    total_beds=4,
                    is_available=True,
                    facilities="Bed, Study Table, Wardrobe, Chair"
                )
                rooms_created += 1

                # Create beds for this room
                for bed_num in range(1, 5):
                    # Check if bed already exists
                    existing_bed = HostelBed.objects.filter(
                        room=room,
                        bed_number=bed_num
                    ).first()
                    
                    if existing_bed:
                        self.stdout.write(self.style.WARNING(f"Bed {bed_num} in room {room_name} already exists. Skipping..."))
                        continue

                    bed_type = 'bunk_top' if bed_num in [1, 3] else 'single'
                    HostelBed.objects.create(
                        room=room,
                        bed_number=bed_num,
                        bed_name=f"{room_name}-B{bed_num}",
                        is_available=True,
                        bed_type=bed_type,
                        facilities="Mattress, Pillow, Blanket"
                    )
                    beds_created += 1

            self.stdout.write(self.style.SUCCESS(
                f"Created {hostel.name} with {rooms_created} rooms and {beds_created} beds."
            ))

        self.stdout.write(self.style.SUCCESS("✅ Hostel creation completed successfully."))