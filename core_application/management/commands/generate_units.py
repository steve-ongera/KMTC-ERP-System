from django.core.management.base import BaseCommand
from core_application.models import Unit
from random import choice, randint

class Command(BaseCommand):
    help = 'Generate 100 realistic medical academic units'

    def handle(self, *args, **kwargs):
        unit_titles = [
            # General Medical Sciences
            "Human Anatomy I", "Human Anatomy II", "Physiology I", "Physiology II", "Medical Biochemistry",
            "Pathophysiology", "Pharmacology I", "Pharmacology II", "Health Communication", "Medical Ethics",

            # Nursing
            "Fundamentals of Nursing", "Adult Health Nursing", "Mental Health Nursing", "Pediatric Nursing",
            "Midwifery", "Community Health Nursing", "Nursing Research", "Nursing Leadership",

            # Clinical Medicine
            "Clinical Examination Techniques", "Internal Medicine I", "Internal Medicine II",
            "Surgical Procedures", "Emergency Medicine", "Obstetrics & Gynaecology", "Pediatrics",

            # Medical Laboratory
            "Introduction to Laboratory Science", "Hematology I", "Hematology II", "Clinical Chemistry",
            "Microbiology", "Parasitology", "Blood Transfusion Science", "Laboratory Safety",

            # Radiography / Imaging
            "Radiographic Physics", "Radiographic Techniques", "Image Processing", "Patient Positioning",
            "Ultrasound Imaging", "Radiographic Anatomy",

            # Pharmacy
            "Pharmaceutical Chemistry", "Dispensing Practice", "Pharmacognosy", "Pharmaceutical Calculations",
            "Drug Regulation", "Pharmaceutical Microbiology",

            # Nutrition & Dietetics
            "Human Nutrition", "Clinical Nutrition", "Food Science", "Meal Planning", "Nutritional Assessment",

            # Physiotherapy & Rehab
            "Introduction to Physiotherapy", "Therapeutic Exercises", "Musculoskeletal Physiotherapy",
            "Neurological Rehabilitation", "Electrotherapy",

            # Public & Environmental Health
            "Epidemiology", "Biostatistics", "Water & Sanitation", "Health Education", "Occupational Health",

            # Shared/Theoretical Units
            "Basic Computer Skills", "Communication Skills", "Research Methods", "Professional Development",
            "Community Diagnosis", "Ethics & Law in Healthcare", "First Aid & CPR", "Disaster Preparedness",

            # Add filler to reach ~100
        ]

        # Generate more names if less than 100
        while len(unit_titles) < 100:
            unit_titles.append(f"Special Topic {len(unit_titles) + 1}")

        unit_types = ['core', 'elective', 'clinical', 'practical', 'theory']
        created_count = 0

        for index, title in enumerate(unit_titles[:100], start=1):
            code = f"MED{index:03d}"

            if Unit.objects.filter(code=code).exists():
                self.stdout.write(self.style.WARNING(f"⚠️ {code} already exists. Skipping..."))
                continue

            unit = Unit.objects.create(
                name=title,
                code=code,
                unit_type=choice(unit_types),
                credit_hours=randint(2, 5),
                theory_hours=randint(1, 3),
                practical_hours=randint(1, 3),
                clinical_hours=randint(0, 2),
                description=f"Study of {title.lower()}.",
                learning_outcomes=f"Understand core concepts of {title.lower()}.",
                is_active=True,
            )

            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"✅ Created: {unit.name} ({unit.code})"))

        self.stdout.write(self.style.SUCCESS(f"\n🎯 Total units created: {created_count}"))
