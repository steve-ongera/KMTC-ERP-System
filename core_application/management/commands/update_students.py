from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core_application.models import Student
from faker import Faker

User = get_user_model()
faker = Faker()

class Command(BaseCommand):
    help = 'Use Faker to update student user profiles with realistic names and set user_type to student'

    def handle(self, *args, **kwargs):
        updated_count = 0

        for student in Student.objects.all():
            if student.user:
                user = student.user

                # Use Faker to generate first and last name
                first_name = faker.first_name()
                last_name = faker.last_name()

                user.first_name = first_name
                user.last_name = last_name
                user.user_type = 'student'  # Ensure user_type is set
                user.save()

                updated_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Updated {user.username}: {first_name} {last_name} (student)"
                ))

        self.stdout.write(self.style.SUCCESS(f"\n🎉 {updated_count} student profiles updated with fake names."))
