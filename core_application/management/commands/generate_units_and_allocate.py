from django.core.management.base import BaseCommand
from core_application.models import Unit, Programme, ProgrammeUnit
from django.utils.text import slugify
from random import choice, randint, shuffle
from django.db import transaction

class Command(BaseCommand):
    help = 'Generate academic units and allocate them to programmes based on years and semesters.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing ProgrammeUnit allocations before creating new ones',
        )
        parser.add_argument(
            '--units-per-semester',
            type=int,
            default=6,
            help='Average number of units per semester (default: 6)',
        )

    def handle(self, *args, **options):
        UNIT_TYPES = ['core', 'elective', 'clinical', 'practical', 'theory']
        
        # Unit name templates for variety
        UNIT_TEMPLATES = [
            "Introduction to {subject}",
            "Advanced {subject}",
            "Clinical {subject}",
            "Research Methods in {subject}",
            "Applied {subject}",
            "Fundamentals of {subject}",
            "Professional {subject}",
            "Specialized {subject}",
        ]
        
        SUBJECTS = [
            "Health Science", "Medical Ethics", "Anatomy", "Physiology", 
            "Pharmacology", "Pathology", "Microbiology", "Biochemistry",
            "Psychology", "Nursing", "Public Health", "Epidemiology",
            "Health Management", "Medical Research", "Biostatistics"
        ]

        units_per_semester = options['units_per_semester']
        clear_existing = options['clear_existing']

        with transaction.atomic():
            # Clear existing allocations if requested
            if clear_existing:
                self.stdout.write("🧹 Clearing existing programme unit allocations...")
                ProgrammeUnit.objects.all().delete()
                self.stdout.write(self.style.SUCCESS("✅ Existing allocations cleared."))

            # 1. Create diverse units
            self.stdout.write("🔧 Creating units...")
            created_units = self.create_units(UNIT_TYPES, UNIT_TEMPLATES, SUBJECTS)
            self.stdout.write(self.style.SUCCESS(f"✅ {len(created_units)} units ready."))

            # 2. Fetch all programmes
            programmes = Programme.objects.all()
            if not programmes.exists():
                self.stdout.write(self.style.ERROR("❌ No programmes found. Please create programmes first."))
                return

            self.stdout.write("📚 Allocating units to programmes by year and semester...")

            # 3. Allocate units to each programme
            for programme in programmes:
                self.allocate_units_to_programme(programme, created_units, units_per_semester)

            self.stdout.write(self.style.SUCCESS("🎉 All units allocated to programmes successfully."))

    def create_units(self, unit_types, templates, subjects):
        """Create diverse academic units"""
        created_units = []
        existing_codes = set(Unit.objects.values_list('code', flat=True))
        
        # Generate units with variety
        unit_counter = 1
        for template in templates:
            for subject in subjects:
                if unit_counter > 150:  # Limit total units
                    break
                    
                name = template.format(subject=subject)
                code = f"UHS{unit_counter:03d}"
                
                # Skip if code already exists
                if code in existing_codes:
                    unit_counter += 1
                    continue

                # Determine unit characteristics based on type and level
                unit_type = choice(unit_types)
                credit_hours = self.get_credit_hours_by_type(unit_type)
                theory_hours, practical_hours, clinical_hours = self.get_hours_by_type(unit_type)

                unit = Unit.objects.create(
                    name=name,
                    code=code,
                    unit_type=unit_type,
                    credit_hours=credit_hours,
                    theory_hours=theory_hours,
                    practical_hours=practical_hours,
                    clinical_hours=clinical_hours,
                    description=f"Comprehensive study of {subject.lower()} concepts and applications.",
                    learning_outcomes=f"Students will develop competency in {subject.lower()} principles and practices.",
                    is_active=True,
                )
                created_units.append(unit)
                existing_codes.add(code)
                unit_counter += 1
                
        return created_units

    def get_credit_hours_by_type(self, unit_type):
        """Assign credit hours based on unit type"""
        credit_mapping = {
            'core': randint(3, 5),
            'elective': randint(2, 4),
            'clinical': randint(4, 6),
            'practical': randint(2, 4),
            'theory': randint(3, 4),
        }
        return credit_mapping.get(unit_type, 3)

    def get_hours_by_type(self, unit_type):
        """Assign contact hours based on unit type"""
        if unit_type == 'clinical':
            return randint(1, 2), randint(2, 4), randint(4, 8)
        elif unit_type == 'practical':
            return randint(1, 3), randint(3, 6), randint(0, 2)
        elif unit_type == 'theory':
            return randint(3, 5), randint(0, 1), 0
        else:  # core, elective
            return randint(2, 4), randint(1, 3), randint(0, 2)

    def allocate_units_to_programme(self, programme, available_units, units_per_semester):
        """Allocate units to a specific programme across all years and semesters"""
        years = programme.duration_years
        semesters = programme.semesters_per_year
        
        # Calculate total semesters needed
        total_semesters = years * semesters
        
        # Create a pool of units for this programme (allow reuse across different semesters)
        programme_units = available_units.copy()
        shuffle(programme_units)
        
        # Track allocations to avoid duplicates within the same programme
        allocated_combinations = set()
        
        unit_index = 0
        total_allocated = 0
        
        self.stdout.write(f"\n📖 Processing {programme.name} ({programme.code})")
        self.stdout.write(f"   Duration: {years} years, {semesters} semesters per year")
        
        for year in range(1, years + 1):
            for semester in range(1, semesters + 1):
                # Vary units per semester (±1 from average)
                semester_units = max(3, units_per_semester + randint(-1, 1))
                
                allocated_this_semester = 0
                attempts = 0
                max_attempts = len(programme_units) * 2
                
                while allocated_this_semester < semester_units and attempts < max_attempts:
                    if unit_index >= len(programme_units):
                        unit_index = 0  # Reset to beginning
                        shuffle(programme_units)  # Reshuffle for variety
                    
                    unit = programme_units[unit_index]
                    combination_key = (programme.id, unit.id, year, semester)
                    
                    # Check if this exact combination already exists
                    if combination_key not in allocated_combinations:
                        # Double-check database to be safe
                        if not ProgrammeUnit.objects.filter(
                            programme=programme, 
                            unit=unit, 
                            year=year, 
                            semester=semester
                        ).exists():
                            
                            # Determine if unit should be mandatory based on type and year
                            is_mandatory = self.determine_mandatory_status(unit, year, years)
                            
                            ProgrammeUnit.objects.create(
                                programme=programme,
                                unit=unit,
                                year=year,
                                semester=semester,
                                is_mandatory=is_mandatory,
                                is_active=True
                            )
                            
                            allocated_combinations.add(combination_key)
                            allocated_this_semester += 1
                            total_allocated += 1
                    
                    unit_index += 1
                    attempts += 1
                
                # Report allocation for this semester
                self.stdout.write(
                    f"   📝 Y{year}S{semester}: {allocated_this_semester} units allocated"
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"✅ {programme.code}: {total_allocated} total units allocated")
        )

    def determine_mandatory_status(self, unit, year, total_years):
        """Determine if a unit should be mandatory based on type and year level"""
        # Core units in early years are usually mandatory
        if unit.unit_type == 'core' and year <= 2:
            return True
        # Clinical units in later years are usually mandatory
        elif unit.unit_type == 'clinical' and year > (total_years // 2):
            return True
        # Electives are usually not mandatory
        elif unit.unit_type == 'elective':
            return choice([True, False])  # 50/50 chance
        else:
            return choice([True, True, False])  # 2/3 chance of being mandatory