from django.core.management.base import BaseCommand
from coreapplication.models import AcademicYear, Semester
from datetime import date

class Command(BaseCommand):
    help = 'Generate 3 semesters per academic year (Jan-Apr, May-Aug, Sept-Dec) for the polytechnic'

    def handle(self, *args, **kwargs):
        academic_years = AcademicYear.objects.all()
        if not academic_years.exists():
            self.stdout.write(self.style.WARNING("No academic years found. Please create academic years first."))
            return

        Semester.objects.update(is_current=False)  # Reset current flag

        created_count = 0

        for year in academic_years:
            year1 = int(year.year.split('-')[0])
            year2 = int(year.year.split('-')[1])

            semesters_data = [
                (1, date(year1, 1, 1), date(year1, 4, 30)),
                (2, date(year1, 5, 1), date(year1, 8, 31)),
                (3, date(year1, 9, 1), date(year1, 12, 31)),
            ]

            for sem_number, start_date, end_date in semesters_data:
                semester, created = Semester.objects.get_or_create(
                    academic_year=year,
                    semester_number=sem_number,
                    defaults={
                        'start_date': start_date,
                        'end_date': end_date,
                        'is_current': False
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Created: {semester}"))

        # Mark most recent year’s Semester 3 as current
        latest_year = AcademicYear.objects.order_by('-start_date').first()
        current_semester = Semester.objects.filter(academic_year=latest_year, semester_number=3).first()
        if current_semester:
            current_semester.is_current = True
            current_semester.save()
            self.stdout.write(self.style.SUCCESS(f"\n✅ Marked {current_semester} as current semester."))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Total semesters created: {created_count}"))
