from django.core.management.base import BaseCommand
from core_application.models import AcademicYear, Semester  # Change if your app is named differently
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Seed academic years and semesters from 2021/2022 to 2025/2026 with 3 semesters each'

    def handle(self, *args, **options):
        base_year = 2021
        current_academic_year = '2024/2025'

        AcademicYear.objects.all().delete()
        Semester.objects.all().delete()

        for i in range(5):  # 2021/2022 to 2025/2026
            start = base_year + i
            end = start + 1
            year_str = f"{start}/{end}"

            academic_start_date = date(start, 9, 1)
            academic_end_date = date(end, 7, 31)

            academic_year = AcademicYear.objects.create(
                year=year_str,
                start_date=academic_start_date,
                end_date=academic_end_date,
                is_current=(year_str == current_academic_year)
            )

            # Semester 1: Sep - Dec
            Semester.objects.create(
                academic_year=academic_year,
                semester_number=1,
                start_date=date(start, 9, 1),
                end_date=date(start, 12, 20),
                registration_start_date=date(start, 8, 1),
                registration_end_date=date(start, 9, 5),
                is_current=(year_str == current_academic_year)
            )

            # Semester 2: Jan - Apr
            Semester.objects.create(
                academic_year=academic_year,
                semester_number=2,
                start_date=date(end, 1, 5),
                end_date=date(end, 4, 30),
                registration_start_date=date(end, 1, 1),
                registration_end_date=date(end, 1, 10),
                is_current=False
            )

            # Semester 3: May - Jul
            Semester.objects.create(
                academic_year=academic_year,
                semester_number=3,
                start_date=date(end, 5, 1),
                end_date=date(end, 7, 31),
                registration_start_date=date(end, 4, 15),
                registration_end_date=date(end, 5, 5),
                is_current=False
            )

        self.stdout.write(self.style.SUCCESS("✅ Academic years and 3 semesters per year created successfully."))
