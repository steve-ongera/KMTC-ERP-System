import os
import django
import sys
from django.utils import timezone
from datetime import date

# Set up Django environment
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ktmc_erp.settings')  # Replace with your project name
django.setup()

from core_application.models import Hostel, Room, Bed, AcademicYear

def create_hostels():
    # Create or get current academic year with required fields
    current_year = timezone.now().year
    academic_year, created = AcademicYear.objects.get_or_create(
        year=f"{current_year}-{current_year+1}",
        defaults={
            'is_current': True,
            'start_date': date(current_year, 1, 1),  # January 1st of current year
            'end_date': date(current_year+1, 12, 31)  # December 31st of next year
        }
    )

    # Hostel data - 2 boys hostels and 2 girls hostels
    hostels_data = [
        {"name": "Mount Kenya", "type": "boys", "initials": "MK"},
        {"name": "Kilimanjaro", "type": "boys", "initials": "KL"},
        {"name": "Aberdare", "type": "girls", "initials": "AB"},
        {"name": "Elgon", "type": "girls", "initials": "EL"},
    ]

    for hostel_data in hostels_data:
        # Create hostel
        hostel = Hostel.objects.create(
            name=hostel_data["name"],
            hostel_type=hostel_data["type"],
            total_rooms=300,
            description=f"{hostel_data['name']} {hostel_data['type'].capitalize()} Hostel",
            facilities="Bed, Study table, Wardrobe, Shared bathroom",
            rules_and_regulations=f"Strictly for {hostel_data['type']} students only. Curfew at 10PM.",
            is_active=True
        )

        print(f"Created {hostel.name} Hostel")

        # Create rooms (300 per hostel)
        for floor in range(1, 6):  # 5 floors
            for room_num in range(1, 61):  # 60 rooms per floor
                room_number = f"{hostel_data['initials']}{floor}{room_num:02d}"
                room = Room.objects.create(
                    hostel=hostel,
                    room_number=room_number,
                    floor=floor,
                    capacity=4,
                    description=f"Room {room_number} on floor {floor}",
                    facilities="4 beds, shared study area",
                    is_active=True
                )

                # Create 4 beds per room
                for bed_pos in range(1, 5):
                    Bed.objects.create(
                        room=room,
                        academic_year=academic_year,
                        bed_position=f"bed_{bed_pos}",
                        bed_number=f"{room_number}B{bed_pos}",
                        is_available=True,
                        maintenance_status='good'
                    )

                print(f"Created room {room_number} with 4 beds", end='\r')
            
            print(f"\nCreated floor {floor} with 60 rooms")

        print(f"Completed {hostel.name} Hostel with {hostel.rooms.count()} rooms\n")

if __name__ == "__main__":
    print("Starting hostel data generation...")
    try:
        create_hostels()
        print("Hostel data generation completed successfully!")
    except Exception as e:
        print(f"Error generating hostels: {str(e)}")
        raise