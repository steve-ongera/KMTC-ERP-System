import random
from datetime import timedelta
from django.core.management.base import BaseCommand
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

from core_application.models import Student, Programme
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Create 300 demo students with unique registration numbers'

    def handle(self, *args, **kwargs):
        try:
            programme = Programme.objects.first()
            if not programme:
                self.stdout.write(self.style.ERROR('❌ No programme found. Please create one first.'))
                return

            year_of_admission = 2022
            password = 'cp7kvt'

            created_count = 0

            for i in range(1, 301):
                unique_number = str(i).zfill(4)
                reg_no = f"EH211/{unique_number}/{year_of_admission}"

                if Student.objects.filter(registration_number=reg_no).exists():
                    continue  # Avoid duplicates

                username = f"student{i}"
                email = f"student{i}@ktmc.ac.ke"

                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email,
                    first_name=f"First{i}",
                    last_name=f"Last{i}"
                )

                Student.objects.create(
                    user=user,
                    registration_number=reg_no,
                    programme=programme,
                    current_year=random.randint(1, 4),
                    current_semester=random.randint(1, 3),
                    admission_date=timezone.datetime(year_of_admission, 9, 1),
                    admission_type=random.choice(['direct', 'parallel', 'upgrading', 'transfer']),
                    sponsor_type=random.choice(['government', 'self', 'employer', 'scholarship', 'bursary']),
                    status='active',
                    guardian_name=f"Guardian {i}",
                    guardian_phone=f"07{random.randint(10000000, 99999999)}",
                    guardian_relationship='Parent',
                    guardian_address=f"Address {i}",
                    emergency_contact=f"07{random.randint(10000000, 99999999)}",
                    blood_group=random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']),
                    medical_conditions="None",
                    expected_graduation_date=timezone.datetime(year_of_admission + 4, 9, 1),
                    gpa=round(random.uniform(2.0, 4.0), 2)
                )

                created_count += 1

            self.stdout.write(self.style.SUCCESS(f"✅ Successfully created {created_count} students."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
