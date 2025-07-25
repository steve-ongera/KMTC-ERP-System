from django.core.management.base import BaseCommand
from coreapplication.models import AcademicYear
from datetime import date

class Command(BaseCommand):
    help = 'Generate academic years for the Kenyan polytechnic in full year format (e.g., 2024-2025)'

    def handle(self, *args, **kwargs):
        start_year = 2021
        end_year = 2026  # Will generate 2021-2022 to 2025-2026

        created_count = 0

        # Optional: clear is_current from older years
        AcademicYear.objects.update(is_current=False)

        for y in range(start_year, end_year):
            year_label = f"{y}-{y + 1}"

            if AcademicYear.objects.filter(year=year_label).exists():
                self.stdout.write(self.style.WARNING(f"Academic year {year_label} already exists. Skipping."))
                continue

            start_date = date(y, 9, 1)      # Start in September
            end_date = date(y + 1, 8, 31)   # End in August of next year

            is_current = (y == end_year - 1)  # Mark last year as current

            AcademicYear.objects.create(
                year=year_label,
                start_date=start_date,
                end_date=end_date,
                is_current=is_current
            )

            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"Created Academic Year: {year_label}"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Successfully created {created_count} academic year(s) in full format."))
