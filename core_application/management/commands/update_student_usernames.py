from django.core.management.base import BaseCommand
from core_application.models import Student
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

class Command(BaseCommand):
    help = 'Update student usernames to their registration numbers with slashes replaced by hyphens'

    def handle(self, *args, **kwargs):
        updated_count = 0

        for student in Student.objects.all():
            if student.registration_number:
                new_username = student.registration_number.replace('/', '-')

                if student.user:
                    user = student.user
                    user.username = new_username
                    user.save()

                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'✅ Updated {user.username}'))

        self.stdout.write(self.style.SUCCESS(f'🎉 Done! {updated_count} usernames updated.'))
