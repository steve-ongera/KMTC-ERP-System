from django.core.management.base import BaseCommand
from coreapplication.models import User
from faker import Faker

fake = Faker()

class Command(BaseCommand):
    help = 'Generate 10 students, 10 faculty, and 10 staff with detailed fields'

    def handle(self, *args, **kwargs):
        password = 'cp7kvt'

        def generate_user(username, user_type):
            if not User.objects.filter(username=username).exists():
                first_name = fake.first_name()
                last_name = fake.last_name()
                email = f"{username.replace('/', '').lower()}@example.com"
                phone = fake.phone_number()
                address = fake.address()

                User.objects.create_user(
                    username=username,
                    password=password,
                    user_type=user_type,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    address=address
                )
                self.stdout.write(self.style.SUCCESS(
                    f"Created {user_type.capitalize()}: {username} ({first_name} {last_name})"
                ))

        # Students
        for i in range(1, 11):
            username = f"H{i:02d}S/2025"
            generate_user(username, 'student')

        # Faculty
        for i in range(1, 11):
            username = f"F{i:02d}T/2025"
            generate_user(username, 'faculty')

        # Staff
        for i in range(1, 11):
            username = f"S{i:02d}F/2025"
            generate_user(username, 'staff')
