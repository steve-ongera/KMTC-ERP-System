from django.core.management.base import BaseCommand
from coreapplication.models import Department
from django.contrib.auth import get_user_model
from django.utils import timezone
import random
import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate 10 random departments for the polytechnic'

    def handle(self, *args, **kwargs):
        department_names = [
            'Computer Science',
            'Mechanical Engineering',
            'Electrical Engineering',
            'Civil Engineering',
            'Business Administration',
            'Information Technology',
            'Applied Sciences',
            'Architecture',
            'Hospitality Management',
            'Agricultural Engineering'
        ]

        existing_users = User.objects.all()
        if not existing_users.exists():
            self.stdout.write(self.style.WARNING('No users found. Please create at least one user first.'))
            return

        for i, name in enumerate(department_names):
            code = f'DEP{i+1:03d}'
            if Department.objects.filter(code=code).exists():
                self.stdout.write(self.style.WARNING(f'Skipping: Department with code {code} already exists.'))
                continue

            department = Department.objects.create(
                name=name,
                code=code,
                description=f"{name} Department focused on excellence in education and innovation.",
                head_of_department=random.choice(existing_users),
                established_date=timezone.now().date() - datetime.timedelta(days=random.randint(3650, 10000)),
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'Created Department: {department}'))
