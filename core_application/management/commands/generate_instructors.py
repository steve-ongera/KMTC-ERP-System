from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from core_application.models import Instructor, School
import random
from datetime import timedelta
from faker import Faker
# Add this to the top with your other imports
from random import randint

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = "Generate 30 realistic instructors with user accounts"

    def handle(self, *args, **kwargs):
        if not School.objects.exists():
            self.stdout.write(self.style.ERROR("❌ No schools found. Please create schools first."))
            return

        designations = [
            'principal', 'deputy_principal', 'senior_lecturer', 'lecturer',
            'assistant_lecturer', 'clinical_instructor', 'tutor'
        ]
        employment_types = ['permanent', 'contract', 'part_time', 'visiting']

        schools = list(School.objects.all())
        created_count = 0

        for i in range(30):
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}"
            email = f"{first_name.lower()}.{last_name.lower()}@kmtc.ac.ke"

            # Ensure username is unique
            if User.objects.filter(username=username).exists():
                continue

            user = User.objects.create_user(
                username=username,
                email=email,
                password='cp7kvt',
                first_name=first_name,
                last_name=last_name,
                user_type='instructor',
                gender=random.choice(['male', 'female']),
                date_of_birth=fake.date_of_birth(minimum_age=30, maximum_age=60),
                national_id=fake.unique.msisdn()[:8],
                is_active=True,
            )

            employee_number = f"EMP{random.randint(10000, 99999)}"
            if Instructor.objects.filter(employee_number=employee_number).exists():
                continue

            Instructor.objects.create(
                user=user,
                employee_number=employee_number,
                school=random.choice(schools),
                designation=random.choice(designations),
                employment_type=random.choice(employment_types),
                qualifications=fake.sentence(nb_words=6),
                specialization=random.choice([
                    "Nursing", "Pharmacology", "Medical Imaging", "Public Health",
                    "Clinical Medicine", "Lab Sciences", "Physiology", "Nutrition"
                ]),
                professional_registration=f"REG-{random.randint(10000, 99999)}",
                experience_years=random.randint(3, 30),
                clinical_experience_years=random.randint(1, 10),
                salary=random.randint(60000, 180000),
                joining_date=timezone.now().date() - timedelta(days=random.randint(365, 3000)),
                contract_end_date=None if random.choice([True, False]) else timezone.now().date() + timedelta(days=randint(365, 1000)),
                is_active=True,
            )

            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"✅ Created Instructor: {first_name} {last_name} ({email})"))

        self.stdout.write(self.style.SUCCESS(f"\n🎯 Successfully created {created_count} instructors."))
