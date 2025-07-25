from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from coreapplication.models import Faculty, Department
from django.utils import timezone
from faker import Faker
import random
import string
from decimal import Decimal

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Generate sample faculty data for each department'

    def handle(self, *args, **kwargs):
        departments = list(Department.objects.all())

        if not departments:
            self.stdout.write(self.style.WARNING("No departments found. Please create departments first."))
            return

        designations = ['professor', 'associate_professor', 'assistant_professor', 'lecturer', 'instructor']
        qualifications = [
            "PhD in Computer Science", "PhD in Electrical Engineering", "MSc in Mechanical Engineering",
            "MEd in Education Management", "MBA", "MSc in Civil Engineering", "PhD in Information Technology"
        ]

        created_count = 0

        for i in range(20):  # Generate 20 faculty members
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(100, 999)}@polytech.ac.ke"

            # Create user
            user = User.objects.create_user(
                username=f"{first_name.lower()}{last_name.lower()}{random.randint(1000,9999)}",
                first_name=first_name,
                last_name=last_name,
                email=email,
                password="faculty123"
            )

            department = random.choice(departments)
            employee_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

            faculty = Faculty.objects.create(
                user=user,
                employee_id=employee_id,
                department=department,
                designation=random.choice(designations),
                qualification=random.choice(qualifications),
                experience_years=random.randint(1, 30),
                specialization=fake.job(),
                salary=Decimal(random.randint(50000, 200000)),
                joining_date=fake.date_between(start_date='-10y', end_date='-1d'),
                is_active=True
            )

            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"Created Faculty: {faculty}"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Successfully created {created_count} faculty profiles."))
