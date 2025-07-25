import random
from django.core.management.base import BaseCommand
from coreapplication.models import Course, Subject, Department
from django.db import transaction
from faker import Faker

class Command(BaseCommand):
    help = 'Generate subjects for all courses based on their duration and semesters'
    
    def __init__(self):
        super().__init__()
        self.fake = Faker()
    
    # Enhanced subject templates with more variety
    SUBJECT_TEMPLATES = {
        'diploma': {
            'IT': [
                'Introduction to Computing', 'Programming Fundamentals', 'Database Systems',
                'Web Development', 'Network Administration', 'Software Engineering',
                'Data Structures', 'Operating Systems', 'Cybersecurity Basics',
                'Mobile App Development', 'System Analysis', 'Project Management',
                'Computer Graphics', 'Artificial Intelligence', 'Cloud Computing',
                'Digital Marketing', 'E-commerce', 'IT Ethics', 'Hardware Maintenance',
                'Multimedia Technology', 'Internet of Things', 'Blockchain Technology',
                'Python Programming', 'Java Programming', 'C++ Programming',
                'Web Frameworks', 'API Development', 'Version Control Systems',
                'Software Testing', 'Agile Methodologies', 'UI/UX Design',
                'Computer Networks', 'Information Security', 'Data Mining',
                'Computer Architecture', 'Algorithms Analysis', 'Database Design',
                'System Administration', 'Cloud Platforms', 'DevOps Fundamentals'
            ],
            'Business': [
                'Business Mathematics', 'Principles of Management', 'Financial Accounting',
                'Business Communication', 'Marketing Principles', 'Human Resource Management',
                'Operations Management', 'Business Law', 'Entrepreneurship',
                'Business Statistics', 'Cost Accounting', 'International Business',
                'Strategic Management', 'Business Ethics', 'Supply Chain Management',
                'Digital Business', 'Customer Relations', 'Business Research Methods',
                'Organizational Behavior', 'Business Analytics', 'Financial Management',
                'Marketing Research', 'Sales Management', 'Business Development',
                'Corporate Strategy', 'Risk Management', 'Quality Management',
                'Business Intelligence', 'E-Business', 'Innovation Management',
                'Leadership Development', 'Project Management', 'Change Management'
            ],
            'Engineering': [
                'Engineering Mathematics', 'Engineering Drawing', 'Materials Science',
                'Thermodynamics', 'Fluid Mechanics', 'Electrical Circuits',
                'Mechanical Design', 'Control Systems', 'Manufacturing Processes',
                'Engineering Economics', 'Quality Control', 'Industrial Safety',
                'CAD/CAM', 'Project Engineering', 'Engineering Ethics',
                'Environmental Engineering', 'Renewable Energy', 'Automation',
                'Structural Analysis', 'Power Systems', 'Electronics',
                'Instrumentation', 'Process Control', 'Machine Design',
                'Heat Transfer', 'Maintenance Engineering', 'Industrial Engineering',
                'Production Planning', 'Operations Research', 'Systems Engineering'
            ]
        },
        'certificate': {
            'IT': [
                'Computer Basics', 'MS Office Applications', 'Internet Skills',
                'Basic Programming', 'Database Fundamentals', 'Web Design Basics',
                'Network Basics', 'Hardware Troubleshooting', 'Digital Literacy',
                'Data Entry', 'Computer Maintenance', 'Software Installation',
                'Email and Communication', 'Basic Cybersecurity', 'File Management',
                'Operating System Basics', 'Printing and Scanning', 'Basic Networking',
                'Social Media Basics', 'Online Safety', 'Digital Communication'
            ],
            'Business': [
                'Business Communication', 'Basic Accounting', 'Customer Service',
                'Sales Techniques', 'Office Administration', 'Business Writing',
                'Time Management', 'Team Work', 'Leadership Skills',
                'Financial Literacy', 'Marketing Basics', 'Business Ethics',
                'Record Keeping', 'Cash Handling', 'Inventory Management',
                'Basic Bookkeeping', 'Business Math', 'Phone Etiquette',
                'Meeting Management', 'Report Writing', 'Filing Systems'
            ]
        },
        'advanced_diploma': {
            'IT': [
                'Advanced Programming', 'Software Architecture', 'Database Administration',
                'Network Security', 'Cloud Computing', 'Big Data Analytics',
                'Machine Learning', 'DevOps Practices', 'Mobile Development',
                'Cybersecurity Advanced', 'System Integration', 'IT Governance',
                'Data Science', 'Blockchain Development', 'IoT Applications',
                'Advanced Web Technologies', 'Enterprise Systems', 'IT Consulting',
                'Research Methods', 'Industry Project', 'Emerging Technologies'
            ],
            'Business': [
                'Advanced Financial Management', 'Strategic Leadership', 'Business Analytics',
                'International Trade', 'Advanced Marketing', 'Operations Research',
                'Corporate Finance', 'Risk Management', 'Business Intelligence',
                'Supply Chain Optimization', 'Digital Transformation', 'Innovation Management',
                'Advanced Project Management', 'Organizational Behavior', 'Business Consulting',
                'Corporate Strategy', 'Advanced Economics', 'Business Research'
            ]
        }
    }
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing subjects before generating new ones',
        )
        parser.add_argument(
            '--use-faker',
            action='store_true',
            help='Use Faker to generate random subject names instead of predefined templates',
        )
    
    @transaction.atomic
    def handle(self, *args, **options):
        if options['clear_existing']:
            Subject.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all existing subjects'))
        
        courses = Course.objects.filter(is_active=True)
        
        if not courses.exists():
            self.stdout.write(self.style.ERROR('No active courses found'))
            return
        
        total_subjects_created = 0
        use_faker = options.get('use_faker', False)
        
        for course in courses:
            self.stdout.write(f"\nGenerating subjects for: {course.name} ({course.code})")
            self.stdout.write(f"  Course Duration: {course.duration_years} years")
            self.stdout.write(f"  Total Semesters: {course.total_semesters}")
            
            # Validate semester configuration
            if course.total_semesters < course.duration_years:
                self.stdout.write(self.style.ERROR(f"  ERROR: Course has {course.total_semesters} semesters but {course.duration_years} years - Invalid configuration!"))
                continue
            
            # Calculate and display semester distribution
            if course.duration_years == 1:
                sem_distribution = f"All {course.total_semesters} semesters in 1 year"
            elif course.total_semesters % course.duration_years == 0:
                sems_per_year = course.total_semesters // course.duration_years
                sem_distribution = f"{sems_per_year} semesters per year"
            else:
                sem_distribution = f"Uneven distribution: {course.total_semesters} semesters across {course.duration_years} years"
            
            self.stdout.write(f"  Semester Distribution: {sem_distribution}")
            
            # Get appropriate subject pool based on course type and name
            if not use_faker:
                subject_pool = self.get_subject_pool(course)
            else:
                subject_pool = []
            
            subjects_created = 0
            used_subjects = set()
            
            # Generate subjects for each semester
            for semester in range(1, course.total_semesters + 1):
                # Calculate which year this semester belongs to with better logic
                year = self.calculate_semester_year(semester, course.total_semesters, course.duration_years)
                
                # Generate 4-6 subjects per semester
                subjects_per_sem = random.randint(4, 6)
                
                self.stdout.write(f"  Semester {semester} (Year {year}): {subjects_per_sem} subjects")
                
                for i in range(subjects_per_sem):
                    # Get subject name (either from template or Faker)
                    if use_faker:
                        subject_name = self.generate_faker_subject_name(course, semester, year)
                    else:
                        subject_name = self.get_unique_subject_name(subject_pool, used_subjects)
                        
                    if not subject_name:
                        # Fallback to Faker if we run out of template subjects
                        subject_name = self.generate_faker_subject_name(course, semester, year)
                    
                    # Ensure unique subject name for this course
                    original_name = subject_name
                    counter = 1
                    while f"{subject_name}" in used_subjects:
                        subject_name = f"{original_name} {counter}"
                        counter += 1
                    
                    # Generate subject code
                    subject_code = self.generate_subject_code(course.code, semester, i + 1)
                    
                    # Ensure unique subject code globally
                    while Subject.objects.filter(code=subject_code).exists():
                        subject_code = self.generate_subject_code(course.code, semester, i + 1, random.randint(10, 99))
                    
                    # Create subject with realistic values
                    subject = Subject.objects.create(
                        name=subject_name,
                        code=subject_code,
                        course=course,
                        year=year,
                        semester=semester,
                        credits=self.get_credits_for_subject(course.course_type, semester),
                        theory_hours=random.randint(30, 50),  # 30-50 theory hours
                        practical_hours=self.get_practical_hours(course.course_type, subject_name),
                        is_elective=self.is_elective_subject(semester, course.total_semesters)
                    )
                    
                    subjects_created += 1
                    used_subjects.add(subject_name)
                    
                    self.stdout.write(f"    Created: {subject.name} ({subject.code}) - {subject.credits} credits")
            
            self.stdout.write(f"  Total subjects created for {course.name}: {subjects_created}")
            total_subjects_created += subjects_created
        
        self.stdout.write(
            self.style.SUCCESS(f"\nSuccessfully created {total_subjects_created} subjects for {courses.count()} courses")
        )
    
    def calculate_semester_year(self, semester, total_semesters, duration_years):
        """Calculate which academic year a semester belongs to"""
        if duration_years == 1:
            return 1
        elif total_semesters == duration_years * 2:
            # Standard 2 semesters per year
            return ((semester - 1) // 2) + 1
        elif total_semesters == duration_years * 3:
            # 3 semesters per year
            return ((semester - 1) // 3) + 1
        else:
            # Handle irregular distributions (e.g., 3 semesters over 2 years)
            if total_semesters == 3 and duration_years == 2:
                # Special case: 3 semesters over 2 years (2 in year 1, 1 in year 2)
                return 1 if semester <= 2 else 2
            elif total_semesters == 5 and duration_years == 2:
                # Special case: 5 semesters over 2 years (3 in year 1, 2 in year 2)
                return 1 if semester <= 3 else 2
            else:
                # General case: distribute as evenly as possible
                semesters_per_year = total_semesters / duration_years
                year = min(int((semester - 1) / semesters_per_year) + 1, duration_years)
                return year
    
    def generate_faker_subject_name(self, course, semester, year):
        """Generate realistic subject names using Faker"""
        course_type = course.course_type
        department_name = course.department.name if hasattr(course, 'department') else 'General'
        
        # Subject prefixes based on course type and department
        prefixes = {
            'IT': ['Computer', 'Software', 'Database', 'Network', 'Web', 'Mobile', 'System', 'Data', 'Cyber', 'Digital'],
            'Business': ['Business', 'Financial', 'Marketing', 'Management', 'Strategic', 'Operations', 'Human Resource', 'Corporate'],
            'Engineering': ['Engineering', 'Technical', 'Industrial', 'Mechanical', 'Electrical', 'Civil', 'Chemical'],
            'General': ['Applied', 'Professional', 'Advanced', 'Practical', 'Theoretical', 'Modern']
        }
        
        # Subject areas based on course type
        areas = {
            'IT': ['Programming', 'Analysis', 'Design', 'Development', 'Administration', 'Security', 'Architecture', 'Testing', 'Integration'],
            'Business': ['Management', 'Accounting', 'Marketing', 'Strategy', 'Operations', 'Economics', 'Finance', 'Leadership'],
            'Engineering': ['Design', 'Systems', 'Mechanics', 'Electronics', 'Materials', 'Manufacturing', 'Control', 'Automation'],
            'General': ['Studies', 'Principles', 'Fundamentals', 'Applications', 'Methods', 'Research', 'Practice']
        }
        
        # Determine category
        if 'IT' in department_name.upper() or 'COMPUTER' in department_name.upper():
            category = 'IT'
        elif 'BUSINESS' in department_name.upper() or 'COMMERCE' in department_name.upper():
            category = 'Business'
        elif 'ENGINEERING' in department_name.upper():
            category = 'Engineering'
        else:
            category = 'General'
        
        # Generate subject name
        prefix = random.choice(prefixes[category])
        area = random.choice(areas[category])
        
        # Add level indicators for advanced courses
        if course_type == 'advanced_diploma' or year > 2:
            level_indicators = ['Advanced', 'Professional', 'Expert', 'Senior']
            if random.random() > 0.5:
                prefix = random.choice(level_indicators) + ' ' + prefix
        
        # Add Roman numerals for continuation courses
        if random.random() > 0.7:
            romans = ['I', 'II', 'III', 'IV']
            area = area + ' ' + random.choice(romans)
        
        return f"{prefix} {area}"
    
    def get_credits_for_subject(self, course_type, semester):
        """Determine credits based on course type and semester"""
        if course_type == 'certificate':
            return random.randint(2, 3)
        elif course_type == 'diploma':
            return random.randint(3, 4)
        elif course_type == 'advanced_diploma':
            return random.randint(4, 5)
        else:
            return random.randint(2, 4)
    
    def get_practical_hours(self, course_type, subject_name):
        """Determine practical hours based on subject type"""
        practical_subjects = ['programming', 'lab', 'design', 'workshop', 'practical', 'project', 'development', 'testing']
        
        # Check if subject likely has practical component
        has_practical = any(word in subject_name.lower() for word in practical_subjects)
        
        if has_practical:
            return random.randint(20, 40)
        elif random.random() > 0.4:  # 60% chance for other subjects
            return random.randint(10, 25)
        else:
            return 0
    
    def is_elective_subject(self, semester, total_semesters):
        """Determine if subject should be elective based on semester"""
        # Later semesters more likely to have electives
        elective_probability = 0.1  # Base 10% chance
        
        if semester > total_semesters * 0.7:  # Last 30% of semesters
            elective_probability = 0.3
        elif semester > total_semesters * 0.5:  # Middle semesters
            elective_probability = 0.2
        
        return random.random() < elective_probability
    def get_subject_pool(self, course):
        """Get appropriate subject pool based on course type and department"""
        course_type = course.course_type
        department_name = course.department.name if hasattr(course, 'department') else 'IT'
        
        # Try to match department name with subject categories
        if 'IT' in department_name.upper() or 'COMPUTER' in department_name.upper():
            category = 'IT'
        elif 'BUSINESS' in department_name.upper() or 'COMMERCE' in department_name.upper():
            category = 'Business'
        elif 'ENGINEERING' in department_name.upper():
            category = 'Engineering'
        else:
            category = 'IT'  # Default fallback
        
        # Get subjects from the template
        if course_type in self.SUBJECT_TEMPLATES and category in self.SUBJECT_TEMPLATES[course_type]:
            return self.SUBJECT_TEMPLATES[course_type][category].copy()
        else:
            # Fallback to IT subjects
            return self.SUBJECT_TEMPLATES.get('diploma', {}).get('IT', []).copy()
    
    def get_unique_subject_name(self, subject_pool, used_subjects):
        """Get a unique subject name from the pool"""
        available_subjects = [s for s in subject_pool if s not in used_subjects]
        
        if not available_subjects:
            return None
        
        return random.choice(available_subjects)
    
    def generate_subject_code(self, course_code, semester, subject_num, suffix=None):
        """Generate a unique subject code"""
        if suffix:
            return f"{course_code}{semester:02d}{subject_num:02d}{suffix}"
        return f"{course_code}{semester:02d}{subject_num:02d}"

