from django.core.management.base import BaseCommand
from core_application.models import Programme, School
from django.utils.text import slugify
import random

class Command(BaseCommand):
    help = 'Generate 10 sample KMTC programmes'

    def handle(self, *args, **kwargs):
        if not School.objects.exists():
            self.stdout.write(self.style.ERROR("❌ No schools found. Please create schools first."))
            return

        programme_data = [
            ("Diploma in Nursing", "diploma", "nursing"),
            ("Certificate in Medical Laboratory", "certificate", "medical_laboratory"),
            ("Higher Diploma in Clinical Medicine", "higher_diploma", "clinical_medicine"),
            ("Diploma in Pharmaceutical Technology", "diploma", "pharmaceutical"),
            ("Certificate in Dental Technology", "certificate", "dental"),
            ("Diploma in Medical Imaging", "diploma", "medical_imaging"),
            ("Diploma in Occupational Therapy", "diploma", "occupational_therapy"),
            ("Diploma in Physiotherapy", "diploma", "physiotherapy"),
            ("Certificate in Health Records", "certificate", "health_records"),
            ("Diploma in Community Health", "diploma", "community_health"),
        ]

        schools = list(School.objects.all())

        for name, p_type, category in programme_data:
            code = slugify(name)[:12].upper().replace("-", "")  # Generate a short code
            school = random.choice(schools)
            duration = random.randint(2, 4)
            semesters = duration * 2

            programme, created = Programme.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "programme_type": p_type,
                    "category": category,
                    "school": school,
                    "duration_years": duration,
                    "semesters_per_year": 2,
                    "total_semesters": semesters,
                    "description": f"{name} offered under {school.name}.",
                    "entry_requirements": "KCSE C plain and above in relevant subjects.",
                    "career_prospects": f"Opportunities in {category.replace('_', ' ').title()} field.",
                    "is_active": True,
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Created: {programme.name} ({programme.code})"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Already exists: {programme.name} ({programme.code})"))
