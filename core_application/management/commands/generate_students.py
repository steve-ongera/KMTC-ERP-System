from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core_application.models import Student, Course
from django.utils import timezone
from faker import Faker
import random
import string

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Generate 40–50 students per course with user accounts'

    def handle(self, *args, **kwargs):
        courses = Course.objects.all()

        if not courses.exists():
            self.stdout.write(self.style.WARNING("No courses found. Please create courses first."))
            return

        total_created = 0

        for course in courses:
            num_students = random.randint(40, 50)
            self.stdout.write(self.style.NOTICE(f"Generating {num_students} students for course: {course.name}"))

            for _ in range(num_students):
                # Generate user info
                first_name = fake.first_name()
                last_name = fake.last_name()
                username = f"{first_name.lower()}{last_name.lower()}{random.randint(1000, 9999)}"
                email = f"{first_name.lower()}.{last_name.lower()}{random.randint(10,99)}@gmail.com"

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='cp7kvt',
                    first_name=first_name,
                    last_name=last_name,
                    user_type='student',
                    phone=fake.phone_number(),
                    address=fake.address(),
                    date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=30),
                    is_active=True
                )

                student_id = f"STU{random.randint(100000, 999999)}"
                while Student.objects.filter(student_id=student_id).exists():
                    student_id = f"STU{random.randint(100000, 999999)}"

                student = Student.objects.create(
                    user=user,
                    student_id=student_id,
                    course=course,
                    current_semester=random.randint(1, course.total_semesters),
                    admission_date=fake.date_between(start_date='-3y', end_date='today'),
                    admission_type=random.choice(['regular', 'lateral_entry', 'transfer']),
                    status='active',
                    guardian_name=fake.name(),
                    guardian_phone=fake.phone_number(),
                    guardian_relation=random.choice(['Father', 'Mother', 'Uncle', 'Aunt', 'Sibling']),
                    emergency_contact=fake.phone_number(),
                    blood_group=random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'])
                )

                total_created += 1
                self.stdout.write(self.style.SUCCESS(f"Created student: {student.user.get_full_name()} - {student.student_id}"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Successfully created {total_created} student records."))
