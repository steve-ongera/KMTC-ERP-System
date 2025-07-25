from django.core.management.base import BaseCommand
from django.db.models import Q
from coreapplication.models import (
    Subject, Faculty, Classroom, TimeSlot, Semester, AcademicYear, Schedule
)
import random

class Command(BaseCommand):
    help = 'Generate class schedule for the current semester and academic year.'

    def handle(self, *args, **kwargs):
        # Get current semester and year
        try:
            current_year = AcademicYear.objects.get(is_current=True)
            current_semester = Semester.objects.get(is_current=True, academic_year=current_year)
        except AcademicYear.DoesNotExist:
            self.stdout.write(self.style.ERROR("No current academic year found."))
            return
        except Semester.DoesNotExist:
            self.stdout.write(self.style.ERROR("No current semester found."))
            return

        self.stdout.write(f"Generating schedule for {current_year.year} - Semester {current_semester.semester_number}")

        # Clear existing schedules for the semester
        Schedule.objects.filter(semester=current_semester).delete()

        # Get available resources
        time_slots = list(TimeSlot.objects.filter(is_active=True))
        classrooms = list(Classroom.objects.filter(is_active=True))
        faculty_members = list(Faculty.objects.filter(is_active=True))

        if not time_slots or not classrooms or not faculty_members:
            self.stdout.write(self.style.ERROR("Ensure TimeSlots, Classrooms, and Faculty are populated and active."))
            return

        used_slots = set()  # Track (classroom, timeslot) pairs to avoid clashes

        subjects = Subject.objects.filter(is_active=True, semester=current_semester.semester_number)

        for subject in subjects:
            attempts = 0
            assigned = False

            while attempts < 100 and not assigned:
                faculty = random.choice(faculty_members)
                classroom = random.choice(classrooms)
                timeslot = random.choice(time_slots)

                key = (classroom.id, timeslot.id)
                conflict = Schedule.objects.filter(
                    Q(classroom=classroom) | Q(faculty=faculty),
                    time_slot=timeslot,
                    semester=current_semester
                ).exists()

                if key not in used_slots and not conflict:
                    Schedule.objects.create(
                        subject=subject,
                        faculty=faculty,
                        classroom=classroom,
                        time_slot=timeslot,
                        semester=current_semester,
                        is_active=True
                    )
                    used_slots.add(key)
                    self.stdout.write(self.style.SUCCESS(f"Scheduled: {subject.code} -> {timeslot} in {classroom.name} by {faculty.user.get_full_name()}"))
                    assigned = True
                else:
                    attempts += 1

            if not assigned:
                self.stdout.write(self.style.WARNING(f"Could NOT schedule: {subject.code} (No available slot found)"))
