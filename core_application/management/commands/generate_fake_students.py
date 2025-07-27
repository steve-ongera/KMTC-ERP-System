from django.core.management.base import BaseCommand
from core_application.models import User, Student, Programme
from django.utils import timezone
from faker import Faker
import random
from django.contrib.auth.hashers import make_password

fake = Faker()

class Command(BaseCommand):
    help = 'Generate 3000 fake student users with first name and last name'

    def handle(self, *args, **kwargs):
        total = 3000
        admission_years = [2021, 2023, 2024, 2025]
        password = make_password('cp7kvt')
        used_serials = set()
        created_users = []
        created_students = []

        programme = Programme.objects.order_by('?').first()
        if not programme:
            self.stdout.write(self.style.ERROR("❌ No programme found. Please create at least one programme."))
            return

        self.stdout.write("📦 Creating users...")

        for i in range(total):
            # Generate unique serial
            while True:
                serial = f"{random.randint(1000, 9999)}"
                year = str(random.choice(admission_years))
                username = f"EC211/{serial}/{year}"
                reg_number = f"EC211-{serial}-{year}"
                if username not in used_serials:
                    used_serials.add(username)
                    break

            gender = random.choice(['male', 'female'])
            dob = fake.date_of_birth(minimum_age=18, maximum_age=30)
            email = fake.email()
            phone = fake.phone_number()
            address = fake.address()
            national_id = fake.unique.random_number(digits=8, fix_len=True)

            first_name = fake.first_name_male() if gender == 'male' else fake.first_name_female()
            last_name = fake.last_name()

            # Create User instance (not saved yet)
            user = User(
                username=username,
                email=email,
                password=password,
                gender=gender,
                user_type='student',
                date_of_birth=dob,
                phone=phone,
                address=address,
                national_id=national_id,
                first_name=first_name,
                last_name=last_name,
            )
            created_users.append(user)

        # Bulk create users
        User.objects.bulk_create(created_users, batch_size=500)
        self.stdout.write(self.style.SUCCESS("✅ Users created. Now creating student profiles..."))

        # Fetch created users from DB
        created_users_db = User.objects.filter(username__in=[u.username for u in created_users])

        for user in created_users_db:
            year = user.username.split('/')[-1]
            serial = user.username.split('/')[1]
            reg_number = f"EC211-{serial}-{year}"
            student = Student(
                user=user,
                registration_number=reg_number,
                programme=programme,
                current_year=random.randint(1, programme.duration_years),
                current_semester=random.randint(1, programme.semesters_per_year),
                admission_date=f"{year}-09-01",
                guardian_name=fake.name(),
                guardian_phone=fake.phone_number(),
                guardian_relationship=random.choice(['Father', 'Mother', 'Brother', 'Sister', 'Uncle', 'Guardian']),
                guardian_address=fake.address(),
                emergency_contact=fake.phone_number(),
                blood_group=random.choice(['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+']),
                medical_conditions=random.choice(['None', 'Asthma', 'Diabetes', 'Epilepsy', '']),
                gpa=round(random.uniform(2.0, 4.0), 2),
            )
            created_students.append(student)

        # Bulk create students
        Student.objects.bulk_create(created_students, batch_size=500)

        self.stdout.write(self.style.SUCCESS(f"🎉 Successfully created {total} students with names."))
