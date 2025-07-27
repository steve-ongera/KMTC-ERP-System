import random
from django.core.management.base import BaseCommand
from core_application.models import Student, Programme

class Command(BaseCommand):
    help = 'Randomly assign programmes to students admitted in 2021, 2023, 2024, or 2025'

    def handle(self, *args, **kwargs):
        available_programmes = list(Programme.objects.all())

        if not available_programmes:
            self.stdout.write(self.style.ERROR("❌ No programmes found in the database."))
            return

        target_years = [2021, 2023, 2024, 2025]
        count = 0

        students = Student.objects.select_related('user').all()

        for student in students:
            user = student.user
            if user and user.date_joined.year in target_years:
                student.programme = random.choice(available_programmes)
                student.save()
                count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Assigned random programmes to {count} students admitted in {target_years}."))
