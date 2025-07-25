from django.core.management.base import BaseCommand
from django.utils import timezone
from core_application.models import School
from django.contrib.auth import get_user_model
import random
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate 5 sample KMTC schools'

    def handle(self, *args, **kwargs):
        sample_schools = [
            {"name": "School of Nursing", "code": "SON"},
            {"name": "School of Pharmacy", "code": "SOP"},
            {"name": "School of Medical Laboratory", "code": "SML"},
            {"name": "School of Public Health", "code": "SPH"},
            {"name": "School of Clinical Medicine", "code": "SCM"},
        ]

        # Pick any existing user to act as dean or set it as None
        deans = list(User.objects.all())
        today = timezone.now().date()

        for data in sample_schools:
            school, created = School.objects.get_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "description": f"This is the {data['name']}.",
                    "dean": random.choice(deans) if deans else None,
                    "established_date": today - timedelta(days=random.randint(1000, 8000)),
                    "is_active": True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Created: {school}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Already exists: {school}"))
