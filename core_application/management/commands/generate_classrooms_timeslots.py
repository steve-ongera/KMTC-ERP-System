from django.core.management.base import BaseCommand
from coreapplication.models import Classroom, TimeSlot
from datetime import time

class Command(BaseCommand):
    help = 'Generate sample classrooms and time slots.'

    def handle(self, *args, **kwargs):
        self.generate_classrooms()
        self.generate_timeslots()

    def generate_classrooms(self):
        buildings = ['Science Block', 'Engineering Hall', 'IT Wing', 'Main Block']
        room_types = ['lecture', 'lab', 'workshop', 'seminar']

        Classroom.objects.all().delete()
        count = 0

        for building in buildings:
            for floor in ['G', '1', '2']:
                for i in range(1, 4):  # 3 rooms per floor
                    name = f"{building[:2].upper()}-{floor}{i}"
                    room_number = f"{building[:2].upper()}-{floor}{i:02d}"
                    room_type = room_types[count % len(room_types)]
                    Classroom.objects.create(
                        name=name,
                        room_number=room_number,
                        room_type=room_type,
                        capacity=30 + (count * 2),
                        floor=floor,
                        building=building,
                        has_projector=(count % 2 == 0),
                        has_computer=(room_type in ['lab', 'workshop']),
                        is_active=True
                    )
                    count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Created {count} classrooms."))

    def generate_timeslots(self):
        TimeSlot.objects.all().delete()
        start_times = [
            (time(8, 0), time(9, 0)),
            (time(9, 0), time(10, 0)),
            (time(10, 15), time(11, 15)),
            (time(11, 15), time(12, 15)),
            (time(2, 0), time(3, 0)),
            (time(3, 0), time(4, 0)),
        ]
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']

        count = 0
        for day in days:
            for start, end in start_times:
                TimeSlot.objects.create(
                    day_of_week=day,
                    start_time=start,
                    end_time=end,
                    is_active=True
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Created {count} time slots."))
