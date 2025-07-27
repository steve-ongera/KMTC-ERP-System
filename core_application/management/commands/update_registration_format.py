from django.core.management.base import BaseCommand
from core_application.models import Student

class Command(BaseCommand):
    help = "Update registration numbers from 'EH211/0099/2022' to 'EH211-0099-2022' format"

    def handle(self, *args, **options):
        students_to_update = Student.objects.filter(registration_number__contains='/')
        count = 0

        for student in students_to_update:
            old_reg = student.registration_number

            # Check for format with exactly 2 slashes
            if old_reg.count('/') == 2:
                new_reg = old_reg.replace('/', '-')
                student.registration_number = new_reg
                student.save()
                self.stdout.write(self.style.SUCCESS(f"✅ Updated: {old_reg} → {new_reg}"))
                count += 1

        self.stdout.write(self.style.SUCCESS(f"\n🎉 Successfully updated {count} registration numbers."))
