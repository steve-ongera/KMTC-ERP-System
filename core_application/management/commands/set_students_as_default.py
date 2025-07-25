from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core_application.models import Instructor, School
import random
from datetime import timedelta
from faker import Faker
# Add this to the top with your other imports
from random import randint

User = get_user_model()

class Command(BaseCommand):
    help = 'Set user_type to student for users with no user_type'

    def handle(self, *args, **kwargs):
        users = User.objects.filter(user_type__isnull=True)
        count = users.count()

        for user in users:
            user.user_type = 'student'
            user.save()

        self.stdout.write(self.style.SUCCESS(f'✅ Updated {count} users to user_type="student".'))
