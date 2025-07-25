from django.core.management.base import BaseCommand
from coreapplication.models import Course, Department
from django.utils import timezone
import random
from decimal import Decimal

class Command(BaseCommand):
    help = 'Generate sample courses and assign them to departments'

    def handle(self, *args, **kwargs):
        courses_data = [
            ("Information Communication Technology", "ICT101", "diploma"),
            ("Electrical Installation", "ELEC201", "certificate"),
            ("Project Management", "PM301", "advanced_diploma"),
            ("Mechanical Engineering", "MECH401", "diploma"),
            ("Business Management", "BUS501", "certificate"),
            ("Accountancy", "ACC601", "advanced_diploma"),
            ("Food and Beverage", "FB701", "diploma"),
            ("Automotive Engineering", "AUTO801", "certificate"),
            ("Civil Engineering", "CIV901", "diploma"),
            ("Human Resource Management", "HRM1001", "certificate"),
        ]

        departments = list(Department.objects.all())
        if not departments:
            self.stdout.write(self.style.WARNING("No departments found. Please generate departments first."))
            return

        for name, code, course_type in courses_data:
            if Course.objects.filter(code=code).exists():
                self.stdout.write(self.style.WARNING(f"Course with code {code} already exists. Skipping..."))
                continue

            course = Course.objects.create(
                name=name,
                code=code,
                course_type=course_type,
                department=random.choice(departments),
                duration_years=random.randint(1, 3),
                total_semesters=random.randint(2, 6),
                description=f"{name} course offered in Kenyan polytechnics.",
                fees_per_semester=Decimal(random.randint(10000, 25000)),
                is_active=True
            )

            self.stdout.write(self.style.SUCCESS(f"Created Course: {course}"))
