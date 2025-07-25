from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from coreapplication.models import Course, AcademicYear, FeeStructure
import random

class Command(BaseCommand):
    help = 'Generate fee structures for all courses and academic years'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating records',
        )
        parser.add_argument(
            '--year',
            type=str,
            help='Generate for specific academic year (e.g., 2024-25)',
        )
        parser.add_argument(
            '--course',
            type=str,
            help='Generate for specific course code',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_year = options['year']
        specific_course = options['course']

        self.stdout.write(self.style.SUCCESS('Starting fee structure generation...'))

        # Get all active courses
        courses = Course.objects.filter(is_active=True)
        if specific_course:
            courses = courses.filter(code=specific_course)
            if not courses.exists():
                self.stdout.write(
                    self.style.ERROR(f'Course with code "{specific_course}" not found!')
                )
                return

        # Get all academic years
        academic_years = AcademicYear.objects.all()
        if specific_year:
            academic_years = academic_years.filter(year=specific_year)
            if not academic_years.exists():
                self.stdout.write(
                    self.style.ERROR(f'Academic year "{specific_year}" not found!')
                )
                return

        if not courses.exists():
            self.stdout.write(self.style.ERROR('No active courses found!'))
            return

        if not academic_years.exists():
            self.stdout.write(self.style.ERROR('No academic years found!'))
            return

        # Fee structure templates based on course type
        fee_templates = {
            'certificate': {
                'tuition_fee': Decimal('15000.00'),
                'lab_fee': Decimal('2000.00'),
                'library_fee': Decimal('500.00'),
                'exam_fee': Decimal('1000.00'),
                'development_fee': Decimal('1500.00'),
                'other_fee': Decimal('500.00'),
            },
            'diploma': {
                'tuition_fee': Decimal('25000.00'),
                'lab_fee': Decimal('3000.00'),
                'library_fee': Decimal('750.00'),
                'exam_fee': Decimal('1500.00'),
                'development_fee': Decimal('2000.00'),
                'other_fee': Decimal('750.00'),
            },
            'advanced_diploma': {
                'tuition_fee': Decimal('35000.00'),
                'lab_fee': Decimal('4000.00'),
                'library_fee': Decimal('1000.00'),
                'exam_fee': Decimal('2000.00'),
                'development_fee': Decimal('2500.00'),
                'other_fee': Decimal('1000.00'),
            },
        }

        created_count = 0
        existing_count = 0
        
        with transaction.atomic():
            for course in courses:
                self.stdout.write(
                    self.style.WARNING(f'\nProcessing course: {course.name} ({course.code})')
                )
                self.stdout.write(f'  - Course type: {course.course_type}')
                self.stdout.write(f'  - Total semesters: {course.total_semesters}')
                
                # Get fee template for this course type
                fee_template = fee_templates.get(course.course_type, fee_templates['diploma'])
                
                for academic_year in academic_years:
                    self.stdout.write(f'  - Academic year: {academic_year.year}')
                    
                    # Create fee structure for each semester of this course
                    for semester in range(1, course.total_semesters + 1):
                        # Check if fee structure already exists
                        existing_fee = FeeStructure.objects.filter(
                            course=course,
                            academic_year=academic_year,
                            semester=semester
                        ).first()
                        
                        if existing_fee:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'    - Semester {semester}: Fee structure already exists (Total: {existing_fee.total_fee()})'
                                )
                            )
                            existing_count += 1
                            continue
                        
                        # Apply some variation to fees (±10%)
                        variation = Decimal(str(random.uniform(0.9, 1.1)))
                        
                        fee_data = {
                            'course': course,
                            'academic_year': academic_year,
                            'semester': semester,
                            'tuition_fee': (fee_template['tuition_fee'] * variation).quantize(Decimal('0.01')),
                            'lab_fee': fee_template['lab_fee'],
                            'library_fee': fee_template['library_fee'],
                            'exam_fee': fee_template['exam_fee'],
                            'development_fee': fee_template['development_fee'],
                            'other_fee': fee_template['other_fee'],
                        }
                        
                        if dry_run:
                            total_fee = sum([
                                fee_data['tuition_fee'],
                                fee_data['lab_fee'],
                                fee_data['library_fee'],
                                fee_data['exam_fee'],
                                fee_data['development_fee'],
                                fee_data['other_fee'],
                            ])
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'    - Semester {semester}: Would create fee structure (Total: {total_fee})'
                                )
                            )
                        else:
                            fee_structure = FeeStructure.objects.create(**fee_data)
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'    - Semester {semester}: Created fee structure (Total: {fee_structure.total_fee()})'
                                )
                            )
                        
                        created_count += 1
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('\n--- DRY RUN SUMMARY ---')
                )
                self.stdout.write(f'Would create: {created_count} fee structures')
                self.stdout.write(f'Already exist: {existing_count} fee structures')
                self.stdout.write(
                    self.style.WARNING('No changes made. Use without --dry-run to apply changes.')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('\n--- SUMMARY ---')
                )
                self.stdout.write(f'Created: {created_count} fee structures')
                self.stdout.write(f'Already existed: {existing_count} fee structures')
                self.stdout.write(
                    self.style.SUCCESS('Fee structure generation completed successfully!')
                )

    def get_course_summary(self):
        """Helper method to display course summary"""
        courses = Course.objects.filter(is_active=True)
        self.stdout.write('\n--- COURSE SUMMARY ---')
        for course in courses:
            self.stdout.write(
                f'{course.code}: {course.name} ({course.course_type}) - {course.total_semesters} semesters'
            )

# Additional utility command to show course summary
class Command2(BaseCommand):
    help = 'Show summary of all courses and their semesters'

    def handle(self, *args, **options):
        courses = Course.objects.filter(is_active=True)
        academic_years = AcademicYear.objects.all()
        
        self.stdout.write(self.style.SUCCESS('=== COURSE SUMMARY ==='))
        for course in courses:
            self.stdout.write(
                f'{course.code}: {course.name} ({course.course_type}) - {course.total_semesters} semesters'
            )
        
        self.stdout.write(self.style.SUCCESS('\n=== ACADEMIC YEARS ==='))
        for year in academic_years:
            current = ' (Current)' if year.is_current else ''
            self.stdout.write(f'{year.year}: {year.start_date} to {year.end_date}{current}')
        
        # Show existing fee structures
        existing_fees = FeeStructure.objects.count()
        self.stdout.write(self.style.SUCCESS(f'\n=== EXISTING FEE STRUCTURES ==='))
        self.stdout.write(f'Total existing fee structures: {existing_fees}')
        
        if existing_fees > 0:
            self.stdout.write('\nBreakdown by course:')
            for course in courses:
                count = FeeStructure.objects.filter(course=course).count()
                self.stdout.write(f'  {course.code}: {count} fee structures')