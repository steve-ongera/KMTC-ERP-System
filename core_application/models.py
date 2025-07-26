from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
import uuid

# Custom User Model
class User(AbstractUser):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    USER_TYPES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('clinical_instructor', 'Clinical Instructor'),
        ('staff', 'Staff'),
        ('registrar', 'Registrar'),
    )

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+\-/]+$',
                message="Username can contain letters, numbers, @, ., +, -, _, and / characters only."
            )
        ],
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_/ allowed."
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    national_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_student(self):
        return self.user_type == 'student' and hasattr(self, 'student_profile')

    def __str__(self):
        return f"{self.username} ({self.user_type})"

# Academic Structure Models
class School(models.Model):
    """KMTC Schools like School of Nursing, School of Medical Laboratory, etc."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    dean = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_schools')
    established_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Programme(models.Model):
    """Medical training programmes offered by KMTC"""
    PROGRAMME_TYPES = (
        ('diploma', 'Diploma'),
        ('certificate', 'Certificate'),
        ('higher_diploma', 'Higher Diploma'),
    )
    
    PROGRAMME_CATEGORIES = (
        ('nursing', 'Nursing'),
        ('medical_laboratory', 'Medical Laboratory'),
        ('clinical_medicine', 'Clinical Medicine'),
        ('pharmaceutical', 'Pharmaceutical'),
        ('dental', 'Dental'),
        ('medical_imaging', 'Medical Imaging'),
        ('occupational_therapy', 'Occupational Therapy'),
        ('physiotherapy', 'Physiotherapy'),
        ('health_records', 'Health Records'),
        ('community_health', 'Community Health'),
        ('environmental_health', 'Environmental Health'),
        ('nutrition', 'Nutrition'),
    )
    
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=15, unique=True)
    programme_type = models.CharField(max_length=20, choices=PROGRAMME_TYPES)
    category = models.CharField(max_length=30, choices=PROGRAMME_CATEGORIES)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='programmes')
    duration_years = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
    semesters_per_year = models.IntegerField(validators=[MinValueValidator(2), MaxValueValidator(3)], default=2)
    total_semesters = models.IntegerField(validators=[MinValueValidator(2), MaxValueValidator(12)])
    description = models.TextField(blank=True)
    entry_requirements = models.TextField()
    career_prospects = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Unit(models.Model):
    """Academic units/subjects - can be shared across programmes"""
    UNIT_TYPES = (
        ('core', 'Core Unit'),
        ('elective', 'Elective Unit'),
        ('clinical', 'Clinical Unit'),
        ('practical', 'Practical Unit'),
        ('theory', 'Theory Unit'),
    )
    
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=15, unique=True)
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPES, default='core')
    credit_hours = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(15)])
    theory_hours = models.IntegerField(default=0)
    practical_hours = models.IntegerField(default=0)
    clinical_hours = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    learning_outcomes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='prerequisite_for')
    
    def total_contact_hours(self):
        return self.theory_hours + self.practical_hours + self.clinical_hours
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class ProgrammeUnit(models.Model):
    """Junction table for Programme-Unit relationship with semester and year info"""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='programme_units')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='unit_programmes')
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    is_mandatory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['programme', 'unit', 'year', 'semester']
        ordering = ['year', 'semester', 'unit__name']
    
    def __str__(self):
        return f"{self.programme.code} - {self.unit.code} (Y{self.year}S{self.semester})"

# People Models
class Instructor(models.Model):
    """Teaching staff including clinical instructors"""
    DESIGNATION_CHOICES = (
        ('principal', 'Principal'),
        ('deputy_principal', 'Deputy Principal'),
        ('senior_lecturer', 'Senior Lecturer'),
        ('lecturer', 'Lecturer'),
        ('assistant_lecturer', 'Assistant Lecturer'),
        ('clinical_instructor', 'Clinical Instructor'),
        ('tutor', 'Tutor'),
    )
    
    EMPLOYMENT_TYPES = (
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
        ('part_time', 'Part Time'),
        ('visiting', 'Visiting'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    employee_number = models.CharField(max_length=20, unique=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='instructors')
    designation = models.CharField(max_length=30, choices=DESIGNATION_CHOICES)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='permanent')
    qualifications = models.TextField()
    specialization = models.CharField(max_length=200, blank=True)
    professional_registration = models.CharField(max_length=100, blank=True, help_text="Professional body registration number")
    experience_years = models.IntegerField(default=0)
    clinical_experience_years = models.IntegerField(default=0)
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    joining_date = models.DateField()
    contract_end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_number}"

class Student(models.Model):
    ADMISSION_TYPES = (
        ('direct', 'Direct Entry'),
        ('parallel', 'Parallel Programme'),
        ('upgrading', 'Upgrading'),
        ('transfer', 'Transfer'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('graduated', 'Graduated'),
        ('deferred', 'Deferred'),
        ('suspended', 'Suspended'),
        ('discontinued', 'Discontinued'),
        ('expelled', 'Expelled'),
    )
    
    SPONSOR_TYPES = (
        ('government', 'Government Sponsored'),
        ('self', 'Self Sponsored'),
        ('employer', 'Employer Sponsored'),
        ('scholarship', 'Scholarship'),
        ('bursary', 'Bursary'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    registration_number = models.CharField(max_length=20, unique=True)
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='students')
    current_year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
    current_semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    admission_date = models.DateField()
    admission_type = models.CharField(max_length=20, choices=ADMISSION_TYPES, default='direct')
    sponsor_type = models.CharField(max_length=20, choices=SPONSOR_TYPES, default='government')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Guardian/Next of Kin Information
    guardian_name = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=15)
    guardian_relationship = models.CharField(max_length=50)
    guardian_address = models.TextField()
    emergency_contact = models.CharField(max_length=15)
    
    # Medical Information
    blood_group = models.CharField(max_length=5, blank=True)
    medical_conditions = models.TextField(blank=True, help_text="Any medical conditions or allergies")
    
    # Academic Information
    expected_graduation_date = models.DateField(null=True, blank=True)
    gpa = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.registration_number}"

class Staff(models.Model):
    STAFF_CATEGORIES = (
        ('administrative', 'Administrative'),
        ('technical', 'Technical Support'),
        ('library', 'Library Staff'),
        ('laboratory', 'Laboratory Technician'),
        ('maintenance', 'Maintenance'),
        ('security', 'Security'),
        ('catering', 'Catering'),
        ('transport', 'Transport'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    employee_number = models.CharField(max_length=20, unique=True)
    staff_category = models.CharField(max_length=20, choices=STAFF_CATEGORIES)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.CharField(max_length=100)
    job_description = models.TextField(blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    joining_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_number}"

# Academic Records Models
class AcademicYear(models.Model):
    year = models.CharField(max_length=10, unique=True)  # e.g., "2024/2025"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if self.is_current:
            # Ensure only one academic year is marked as current
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.year

class Semester(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    semester_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    start_date = models.DateField()
    end_date = models.DateField()
    registration_start_date = models.DateField()
    registration_end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['academic_year', 'semester_number']
        ordering = ['academic_year', 'semester_number']
    
    def save(self, *args, **kwargs):
        if self.is_current:
            # Ensure only one semester is marked as current
            Semester.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.academic_year.year} - Semester {self.semester_number}"


class StudentReporting(models.Model):
    REPORTING_TYPES = (
        ('online', 'Online Reporting'),
        ('physical', 'Physical Reporting'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    reporting_type = models.CharField(max_length=10, choices=REPORTING_TYPES, default='online')
    reporting_date = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    processed_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True)
    processed_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('student', 'semester')
        ordering = ['-reporting_date']
        
    def __str__(self):
        return f"{self.student.registration_number} - {self.semester}"
    
class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='enrollments')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_repeat = models.BooleanField(default=False, help_text="Is this a repeat unit?")
    
    class Meta:
        unique_together = ['student', 'unit', 'semester']
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.unit.code} - {self.semester}"

# Grading System
class Grade(models.Model):
    GRADE_CHOICES = (
        ('A', 'A (80-100)'),
        ('B+', 'B+ (75-79)'),
        ('B', 'B (70-74)'),
        ('B-', 'B- (65-69)'),
        ('C+', 'C+ (60-64)'),
        ('C', 'C (55-59)'),
        ('C-', 'C- (50-54)'),
        ('D+', 'D+ (45-49)'),
        ('D', 'D (40-44)'),
        ('E', 'E (Below 40)'),
        ('I', 'Incomplete'),
        ('W', 'Withdrawn'),
    )
    
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='grade')
    theory_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    practical_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    clinical_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    continuous_assessment = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    final_exam_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True)
    grade_points = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    is_passed = models.BooleanField(default=False)
    exam_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        # Calculate total marks and determine grade
        if all([self.theory_marks is not None, self.practical_marks is not None, 
                self.continuous_assessment is not None, self.final_exam_marks is not None]):
            self.total_marks = (self.theory_marks + self.practical_marks + 
                              self.continuous_assessment + self.final_exam_marks) / 4
            
            # Determine grade based on total marks
            if self.total_marks >= 80:
                self.grade = 'A'
                self.grade_points = 4.0
                self.is_passed = True
            elif self.total_marks >= 75:
                self.grade = 'B+'
                self.grade_points = 3.5
                self.is_passed = True
            elif self.total_marks >= 70:
                self.grade = 'B'
                self.grade_points = 3.0
                self.is_passed = True
            elif self.total_marks >= 65:
                self.grade = 'B-'
                self.grade_points = 2.5
                self.is_passed = True
            elif self.total_marks >= 60:
                self.grade = 'C+'
                self.grade_points = 2.0
                self.is_passed = True
            elif self.total_marks >= 55:
                self.grade = 'C'
                self.grade_points = 1.5
                self.is_passed = True
            elif self.total_marks >= 50:
                self.grade = 'C-'
                self.grade_points = 1.0
                self.is_passed = True
            elif self.total_marks >= 45:
                self.grade = 'D+'
                self.grade_points = 0.5
                self.is_passed = False
            elif self.total_marks >= 40:
                self.grade = 'D'
                self.grade_points = 0.0
                self.is_passed = False
            else:
                self.grade = 'E'
                self.grade_points = 0.0
                self.is_passed = False
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.enrollment.student.registration_number} - {self.enrollment.unit.code} - {self.grade}"

# Fee Management Models
class FeeStructure(models.Model):
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='fee_structures')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='fee_structures')
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    
    # Different fee components
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    registration_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    examination_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    library_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    laboratory_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    clinical_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    accommodation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    meals_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    medical_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    insurance_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    activity_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    other_fees = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Government subsidy for sponsored students
    government_subsidy = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['programme', 'academic_year', 'year', 'semester']
    
    def total_fee(self):
        return (self.tuition_fee + self.registration_fee + self.examination_fee + 
                self.library_fee + self.laboratory_fee + self.clinical_fee + 
                self.accommodation_fee + self.meals_fee + self.medical_fee + 
                self.insurance_fee + self.activity_fee + self.other_fees)
    
    def net_fee(self):
        """Fee after government subsidy"""
        return self.total_fee() - self.government_subsidy
    
    def __str__(self):
        return f"{self.programme.code} - {self.academic_year.year} - Y{self.year}S{self.semester}"

class FeePayment(models.Model):
    PAYMENT_METHODS = (
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('bankers_cheque', 'Bankers Cheque'),
        ('online', 'Online Payment'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('reversed', 'Reversed'),
        ('refunded', 'Refunded'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='payments')
    receipt_number = models.CharField(max_length=50, unique=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_reference = models.CharField(max_length=100, blank=True)
    mpesa_receipt = models.CharField(max_length=50, blank=True)
    bank_slip_number = models.CharField(max_length=50, blank=True)
    remarks = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.receipt_number} - KES {self.amount_paid}"

# Clinical Training Models
class ClinicalSite(models.Model):
    """Hospitals and health facilities where students do clinical training"""
    FACILITY_TYPES = (
        ('national_referral', 'National Referral Hospital'),
        ('county_referral', 'County Referral Hospital'),
        ('sub_county', 'Sub-County Hospital'),
        ('health_centre', 'Health Centre'),
        ('dispensary', 'Dispensary'),
        ('private_hospital', 'Private Hospital'),
        ('specialized', 'Specialized Facility'),
    )
    
    name = models.CharField(max_length=200)
    facility_type = models.CharField(max_length=30, choices=FACILITY_TYPES)
    county = models.CharField(max_length=50)
    sub_county = models.CharField(max_length=50)
    address = models.TextField()
    contact_person = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=15)
    contact_email = models.EmailField(blank=True)
    capacity = models.IntegerField(help_text="Maximum number of students")
    specializations = models.ManyToManyField('Unit', blank=True, help_text="Units that can be done at this site")
    mou_start_date = models.DateField(help_text="MOU start date")
    mou_end_date = models.DateField(help_text="MOU end date")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.county}"

class ClinicalPlacement(models.Model):
    """Student clinical placements"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='clinical_placements')
    clinical_site = models.ForeignKey(ClinicalSite, on_delete=models.CASCADE, related_name='placements')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='clinical_placements')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='clinical_placements')
    start_date = models.DateField()
    end_date = models.DateField()
    supervisor_name = models.CharField(max_length=100, help_text="Clinical supervisor at the facility")
    supervisor_contact = models.CharField(max_length=15, blank=True)
    is_completed = models.BooleanField(default=False)
    completion_report = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student', 'unit', 'semester']
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.clinical_site.name} - {self.unit.code}"

# Attendance Models
class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused Absence'),
        ('sick', 'Sick Leave'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    session_type = models.CharField(max_length=20, choices=[('theory', 'Theory'), ('practical', 'Practical'), ('clinical', 'Clinical')])
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(Instructor, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'unit', 'date', 'session_type']
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.unit.code} - {self.date} - {self.status}"

# Timetable Models
class Venue(models.Model):
    """Classrooms, labs, clinical areas"""
    VENUE_TYPES = (
        ('classroom', 'Classroom'),
        ('laboratory', 'Laboratory'),
        ('skills_lab', 'Skills Laboratory'),
        ('computer_lab', 'Computer Laboratory'),
        ('workshop', 'Workshop'),
        ('auditorium', 'Auditorium'),
        ('clinical_area', 'Clinical Area'),
    )
    
    name = models.CharField(max_length=100)
    venue_code = models.CharField(max_length=20, unique=True)
    venue_type = models.CharField(max_length=20, choices=VENUE_TYPES)
    capacity = models.IntegerField()
    floor = models.CharField(max_length=10)
    building = models.CharField(max_length=50)
    has_projector = models.BooleanField(default=False)
    has_computer = models.BooleanField(default=False)
    has_internet = models.BooleanField(default=False)
    equipment_available = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.venue_code})"

class TimeSlot(models.Model):
    DAY_CHOICES = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )
    
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['day_of_week', 'start_time']
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

class Schedule(models.Model):
    """Timetable entries"""
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='schedules')
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='schedules')
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='schedules')
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='schedules')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='schedules')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='schedules')
    session_type = models.CharField(max_length=20, choices=[('theory', 'Theory'), ('practical', 'Practical'), ('clinical', 'Clinical')])
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['venue', 'time_slot', 'semester']
    
    def __str__(self):
        return f"{self.unit.code} - {self.programme.code} Y{self.year} - {self.time_slot} - {self.venue.name}"

# Examination Models
class Examination(models.Model):
    EXAM_TYPES = (
        ('continuous_assessment', 'Continuous Assessment'),
        ('mid_semester', 'Mid Semester'),
        ('end_semester', 'End Semester'),
        ('practical', 'Practical Exam'),
        ('clinical', 'Clinical Assessment'),
        ('supplementary', 'Supplementary Exam'),
        ('special', 'Special Exam'),
    )
    
    name = models.CharField(max_length=100)
    exam_type = models.CharField(max_length=25, choices=EXAM_TYPES)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='examinations')
    start_date = models.DateField()
    end_date = models.DateField()
    application_deadline = models.DateField(help_text="Deadline for exam application")
    max_marks = models.IntegerField(default=100)
    pass_marks = models.IntegerField(default=50)
    is_active = models.BooleanField(default=True)
    instructions = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.semester}"

class ExamSchedule(models.Model):
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='schedules')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='exam_schedules')
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='exam_schedules')
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='exam_schedules')
    max_marks = models.IntegerField(default=100)
    duration_minutes = models.IntegerField(default=180)
    invigilators = models.ManyToManyField(Instructor, blank=True, related_name='invigilated_exams')
    special_instructions = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.examination.name} - {self.unit.code} - {self.programme.code} Y{self.year} - {self.exam_date}"

# Library Management Models
class Book(models.Model):
    BOOK_CATEGORIES = (
        ('nursing', 'Nursing'),
        ('medical', 'Medical'),
        ('pharmacy', 'Pharmacy'),
        ('laboratory', 'Laboratory Medicine'),
        ('clinical_medicine', 'Clinical Medicine'),
        ('public_health', 'Public Health'),
        ('reference', 'Reference'),
        ('research', 'Research'),
        ('general', 'General'),
    )
    
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=20, unique=True, blank=True)
    publisher = models.CharField(max_length=100)
    publication_year = models.IntegerField()
    edition = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=20, choices=BOOK_CATEGORIES, default='general')
    related_units = models.ManyToManyField(Unit, blank=True, related_name='recommended_books')
    total_copies = models.IntegerField(default=1)
    available_copies = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    location_code = models.CharField(max_length=20, blank=True, help_text="Library shelf location")
    
    def __str__(self):
        return f"{self.title} by {self.author}"

class BookIssue(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='issues')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='book_issues')
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    renewal_count = models.IntegerField(default=0)
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_returned = models.BooleanField(default=False)
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='issued_books')
    returned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='returned_books')
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.book.title}"

# Hostel/Accommodation Models
class Hostel(models.Model):
    """Hostel buildings for accommodation"""
    HOSTEL_TYPES = (
        ('boys', 'Boys Hostel'),
        ('girls', 'Girls Hostel'),
    )
    
    name = models.CharField(max_length=100)
    hostel_type = models.CharField(max_length=10, choices=HOSTEL_TYPES)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='hostels')
    warden = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_hostels')
    total_rooms = models.IntegerField(validators=[MinValueValidator(1)])
    description = models.TextField(blank=True)
    facilities = models.TextField(blank=True, help_text="Available facilities like WiFi, laundry, etc.")
    rules_and_regulations = models.TextField( null=True, blank=True,)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True,)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True,)
    
    class Meta:
        ordering = ['hostel_type', 'name']

    
    
    def __str__(self):
        return f"{self.name} ({self.get_hostel_type_display()})"
    
    def get_available_rooms_count(self, academic_year):
        """Get count of rooms with available beds for the academic year"""
        return self.rooms.filter(
            beds__academic_year=academic_year,
            beds__is_available=True,
            is_active=True
        ).distinct().count()
    
    def get_total_beds_count(self, academic_year):
        """Get total beds in hostel for academic year"""
        return self.rooms.filter(
            beds__academic_year=academic_year,
            is_active=True
        ).aggregate(
            total=models.Count('beds')
        )['total'] or 0
    
    def get_occupied_beds_count(self, academic_year):
        """Get count of occupied beds for academic year"""
        return self.rooms.filter(
            beds__academic_year=academic_year,
            beds__is_available=False,
            is_active=True
        ).aggregate(
            occupied=models.Count('beds')
        )['occupied'] or 0


class Room(models.Model):
    """Individual rooms in hostels"""
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=10)
    floor = models.IntegerField(validators=[MinValueValidator(0)], help_text="Floor number (0 for ground floor)")
    capacity = models.IntegerField(default=4, validators=[MinValueValidator(1), MaxValueValidator(8)])
    description = models.TextField(blank=True)
    facilities = models.TextField(blank=True, help_text="Room-specific facilities")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True , blank=True , null=True)
    
    class Meta:
        unique_together = ['hostel', 'room_number']
        ordering = ['hostel', 'floor', 'room_number']
    
    def __str__(self):
        return f"{self.hostel.name} - Room {self.room_number}"
    
    def get_available_beds_count(self, academic_year):
        """Get count of available beds in this room for academic year"""
        return self.beds.filter(
            academic_year=academic_year,
            is_available=True
        ).count()
    
    def get_occupied_beds_count(self, academic_year):
        """Get count of occupied beds in this room for academic year"""
        return self.beds.filter(
            academic_year=academic_year,
            is_available=False
        ).count()
    
    def is_full(self, academic_year):
        """Check if room is fully occupied for academic year"""
        return self.get_available_beds_count(academic_year) == 0

class Bed(models.Model):
    """Individual beds in rooms for each academic year"""
    BED_POSITIONS = (
        ('bed_1', 'Bed 1'),
        ('bed_2', 'Bed 2'),
        ('bed_3', 'Bed 3'),
        ('bed_4', 'Bed 4'),
    )
    
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='beds')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='hostel_beds')
    bed_position = models.CharField(max_length=10, choices=BED_POSITIONS)
    bed_number = models.CharField(max_length=20, help_text="Unique bed identifier")
    is_available = models.BooleanField(default=True)
    maintenance_status = models.CharField(
        max_length=20,
        choices=(
            ('good', 'Good Condition'),
            ('needs_repair', 'Needs Repair'),
            ('under_maintenance', 'Under Maintenance'),
            ('out_of_order', 'Out of Order'),
        ),
        default='good'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['room', 'academic_year', 'bed_position']
        ordering = ['room', 'bed_position']
    
    def __str__(self):
        return f"{self.room} - {self.bed_number} ({self.academic_year})"
    
    def save(self, *args, **kwargs):
        if not self.bed_number:
            # Auto-generate bed number: HOSTEL_ROOM_BED_YEAR
            hostel_code = self.room.hostel.name[:3].upper()
            year_code = self.academic_year.year.split('/')[0][-2:]  # Last 2 digits of start year
            self.bed_number = f"{hostel_code}{self.room.room_number}{self.bed_position[-1]}{year_code}"
        super().save(*args, **kwargs)


class HostelBooking(models.Model):
    """Student hostel booking records"""
    BOOKING_STATUS = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Payment Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
        ('refunded', 'Refunded'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='hostel_bookings')
    bed = models.ForeignKey(Bed, on_delete=models.CASCADE, related_name='bookings')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='hostel_bookings')
    
    booking_date = models.DateTimeField(auto_now_add=True)
    check_in_date = models.DateField(null=True, blank=True)
    check_out_date = models.DateField(null=True, blank=True)
    expected_checkout_date = models.DateField(null=True, blank=True)
    
    booking_status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    booking_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Approval workflow
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bookings')
    approval_date = models.DateTimeField(null=True, blank=True)
    approval_remarks = models.TextField(blank=True)
    
    # Check-in/out details
    checked_in_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_in_students')
    checked_out_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_out_students')
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'academic_year']  # One booking per student per academic year
        ordering = ['-booking_date']
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.bed} ({self.academic_year})"
    
    def save(self, *args, **kwargs):
        # Update bed availability based on booking status
        if self.pk:  # If updating existing booking
            old_booking = HostelBooking.objects.get(pk=self.pk)
            if old_booking.booking_status != self.booking_status:
                if self.booking_status in ['approved', 'checked_in']:
                    self.bed.is_available = False
                    self.bed.save()
                elif self.booking_status in ['rejected', 'cancelled', 'checked_out']:
                    self.bed.is_available = True
                    self.bed.save()
        else:  # New booking
            if self.booking_status in ['approved', 'checked_in']:
                self.bed.is_available = False
                self.bed.save()
        
        super().save(*args, **kwargs)
    
    @property
    def balance_due(self):
        """Calculate remaining balance"""
        return self.booking_fee - self.amount_paid
    
    @property
    def is_fully_paid(self):
        """Check if booking is fully paid"""
        return self.amount_paid >= self.booking_fee

class HostelPayment(models.Model):
    """Track hostel fee payments"""
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('cheque', 'Cheque'),
        ('card', 'Credit/Debit Card'),
    )
    
    booking = models.ForeignKey(HostelBooking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_number = models.CharField(max_length=50, blank=True)
    receipt_number = models.CharField(max_length=50, unique=True)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.booking.student.registration_number} - {self.amount} ({self.payment_date})"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Auto-generate receipt number
            year = timezone.now().year
            count = HostelPayment.objects.filter(
                created_at__year=year
            ).count() + 1
            self.receipt_number = f"HPR{year}{count:05d}"
        
        super().save(*args, **kwargs)
        
        # Update booking payment status
        booking = self.booking
        total_paid = booking.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        booking.amount_paid = total_paid
        
        if total_paid >= booking.booking_fee:
            booking.payment_status = 'paid'
        elif total_paid > 0:
            booking.payment_status = 'partial'
        else:
            booking.payment_status = 'pending'
        
        booking.save()

class HostelIncident(models.Model):
    """Track incidents and disciplinary issues in hostels"""
    INCIDENT_TYPES = (
        ('damage', 'Property Damage'),
        ('noise', 'Noise Complaint'),
        ('theft', 'Theft'),
        ('violence', 'Violence/Fighting'),
        ('drugs', 'Drug/Alcohol Related'),
        ('curfew', 'Curfew Violation'),
        ('cleanliness', 'Cleanliness Issue'),
        ('other', 'Other'),
    )
    
    SEVERITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    STATUS_CHOICES = (
        ('reported', 'Reported'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('escalated', 'Escalated'),
    )
    
    booking = models.ForeignKey(HostelBooking, on_delete=models.CASCADE, related_name='incidents')
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='low')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reported')
    
    incident_date = models.DateTimeField()
    description = models.TextField()
    action_taken = models.TextField(blank=True)
    
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_incidents')
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_incidents')
    
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fine_paid = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-incident_date']
    
    def __str__(self):
        return f"{self.booking.student.registration_number} - {self.get_incident_type_display()} ({self.incident_date.date()})"

# Student Services Models
class StudentService(models.Model):
    SERVICE_TYPES = (
        ('medical', 'Medical Services'),
        ('counseling', 'Counseling Services'),
        ('chaplaincy', 'Chaplaincy Services'),
        ('sports', 'Sports & Recreation'),
        ('career', 'Career Guidance'),
        ('financial_aid', 'Financial Aid'),
        ('disability', 'Disability Support'),
    )
    
    name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    description = models.TextField()
    contact_person = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=15)
    contact_email = models.EmailField(blank=True)
    location = models.CharField(max_length=100)
    operating_hours = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class ServiceRequest(models.Model):
    REQUEST_STATUS = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='service_requests')
    service = models.ForeignKey(StudentService, on_delete=models.CASCADE, related_name='requests')
    request_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    status = models.CharField(max_length=15, choices=REQUEST_STATUS, default='pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    response = models.TextField(blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.service.name}"

# Notification Models
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('general', 'General Announcement'),
        ('academic', 'Academic Notice'),
        ('fee', 'Fee Related'),
        ('exam', 'Examination'),
        ('clinical', 'Clinical Training'),
        ('hostel', 'Hostel/Accommodation'),
        ('emergency', 'Emergency'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    target_programmes = models.ManyToManyField(Programme, blank=True, related_name='notifications')
    target_years = models.CharField(max_length=20, blank=True, help_text="Comma separated years e.g., 1,2,3")
    target_users = models.ManyToManyField(User, blank=True, related_name='notifications')
    is_global = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class NotificationRead(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='reads')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_reads')
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['notification', 'user']

# Research & Projects Models
class ResearchProject(models.Model):
    PROJECT_TYPES = (
        ('final_year', 'Final Year Project'),
        ('research', 'Research Project'),
        ('case_study', 'Case Study'),
        ('community', 'Community Health Project'),
    )
    
    title = models.CharField(max_length=200)
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES)
    description = models.TextField()
    students = models.ManyToManyField(Student, related_name='research_projects')
    supervisor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='supervised_projects')
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    submission_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    grade = models.CharField(max_length=2, blank=True)
    
    def __str__(self):
        return self.title

# Professional Bodies & Licensing Models
class ProfessionalBody(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=20)
    description = models.TextField()
    website = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)
    registration_requirements = models.TextField()
    annual_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Professional Bodies"
    
    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

class ProfessionalRegistration(models.Model):
    REGISTRATION_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='professional_registrations')
    professional_body = models.ForeignKey(ProfessionalBody, on_delete=models.CASCADE, related_name='registrations')
    registration_number = models.CharField(max_length=50, blank=True)
    application_date = models.DateField()
    approval_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=REGISTRATION_STATUS, default='pending')
    certificate_file = models.FileField(upload_to='professional_certificates/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.professional_body.abbreviation}"

# Alumni Models
class Alumni(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='alumni_profile')
    graduation_date = models.DateField()
    current_employer = models.CharField(max_length=200, blank=True)
    current_position = models.CharField(max_length=100, blank=True)
    work_phone = models.CharField(max_length=15, blank=True)
    work_email = models.EmailField(blank=True)
    achievements = models.TextField(blank=True)
    is_willing_mentor = models.BooleanField(default=False)
    professional_registrations = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Alumni"
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.graduation_date.year}"

# Quality Assurance Models
class QualityAssessment(models.Model):
    ASSESSMENT_TYPES = (
        ('unit_evaluation', 'Unit Evaluation'),
        ('instructor_evaluation', 'Instructor Evaluation'),
        ('clinical_site_evaluation', 'Clinical Site Evaluation'),
        ('facility_evaluation', 'Facility Evaluation'),
    )
    
    assessment_type = models.CharField(max_length=25, choices=ASSESSMENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='quality_assessments')
    target_unit = models.ForeignKey(Unit, on_delete=models.CASCADE, null=True, blank=True)
    target_instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, null=True, blank=True)
    target_clinical_site = models.ForeignKey(ClinicalSite, on_delete=models.CASCADE, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} - {self.semester}"

class QualityAssessmentResponse(models.Model):
    assessment = models.ForeignKey(QualityAssessment, on_delete=models.CASCADE, related_name='responses')
    respondent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quality_responses')
    responses = models.JSONField()  # Store questionnaire responses
    additional_comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['assessment', 'respondent']
    
    def __str__(self):
        return f"{self.assessment.title} - {self.respondent.username}"

# Student Support Models
class StudentComment(models.Model):
    COMMENT_CATEGORIES = (
        ('academic', 'Academic Issue'),
        ('fee', 'Fee Related'),
        ('hostel', 'Hostel/Accommodation'),
        ('clinical', 'Clinical Training'),
        ('general', 'General Query'),
        ('complaint', 'Complaint'),
        ('suggestion', 'Suggestion'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='comments')
    category = models.CharField(max_length=20, choices=COMMENT_CATEGORIES, default='general')
    subject = models.CharField(max_length=200)
    comment = models.TextField()
    priority = models.CharField(max_length=10, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default=False)
    admin_response = models.TextField(blank=True, null=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='responded_comments')
    response_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Comment'
        verbose_name_plural = 'Student Comments'
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.subject}"

# Medical Records (for student health)
class StudentMedicalRecord(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='medical_record')
    medical_history = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    emergency_medical_contact = models.CharField(max_length=100)
    emergency_medical_phone = models.CharField(max_length=15)
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_number = models.CharField(max_length=50, blank=True)
    last_medical_checkup = models.DateField(null=True, blank=True)
    vaccinations = models.TextField(blank=True, help_text="Record of vaccinations")
    
    def __str__(self):
        return f"Medical Record - {self.student.registration_number}"

class MedicalVisit(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='medical_visits')
    visit_date = models.DateField()
    symptoms = models.TextField()
    diagnosis = models.TextField()
    treatment = models.TextField()
    prescribed_medication = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    medical_officer = models.CharField(max_length=100)
    
    class Meta:
        ordering = ['-visit_date']
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.visit_date}"

# System Configuration Models
class SystemConfiguration(models.Model):
    CONFIG_TYPES = (
        ('academic', 'Academic Settings'),
        ('fee', 'Fee Settings'),
        ('notification', 'Notification Settings'),
        ('general', 'General Settings'),
    )
    
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPES)
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.key} = {self.value}"



# Hostel Management Models 

# class Hostel(models.Model):
#     """Hostel buildings for accommodation"""
#     HOSTEL_TYPES = (
#         ('boys', 'Boys Hostel'),
#         ('girls', 'Girls Hostel'),
#     )
    
#     name = models.CharField(max_length=100)
#     hostel_type = models.CharField(max_length=10, choices=HOSTEL_TYPES)
#     school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='hostels')
#     warden = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_hostels')
#     total_rooms = models.IntegerField(validators=[MinValueValidator(1)])
#     description = models.TextField(blank=True)
#     facilities = models.TextField(blank=True, help_text="Available facilities like WiFi, laundry, etc.")
#     rules_and_regulations = models.TextField(blank=True)
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         ordering = ['hostel_type', 'name']
    
#     def __str__(self):
#         return f"{self.name} ({self.get_hostel_type_display()})"
    
#     def get_available_rooms_count(self, academic_year):
#         """Get count of rooms with available beds for the academic year"""
#         return self.rooms.filter(
#             beds__academic_year=academic_year,
#             beds__is_available=True,
#             is_active=True
#         ).distinct().count()
    
#     def get_total_beds_count(self, academic_year):
#         """Get total beds in hostel for academic year"""
#         return self.rooms.filter(
#             beds__academic_year=academic_year,
#             is_active=True
#         ).aggregate(
#             total=models.Count('beds')
#         )['total'] or 0
    
#     def get_occupied_beds_count(self, academic_year):
#         """Get count of occupied beds for academic year"""
#         return self.rooms.filter(
#             beds__academic_year=academic_year,
#             beds__is_available=False,
#             is_active=True
#         ).aggregate(
#             occupied=models.Count('beds')
#         )['occupied'] or 0

# class Room(models.Model):
#     """Individual rooms in hostels"""
#     hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='rooms')
#     room_number = models.CharField(max_length=10)
#     floor = models.IntegerField(validators=[MinValueValidator(0)], help_text="Floor number (0 for ground floor)")
#     capacity = models.IntegerField(default=4, validators=[MinValueValidator(1), MaxValueValidator(8)])
#     description = models.TextField(blank=True)
#     facilities = models.TextField(blank=True, help_text="Room-specific facilities")
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     class Meta:
#         unique_together = ['hostel', 'room_number']
#         ordering = ['hostel', 'floor', 'room_number']
    
#     def __str__(self):
#         return f"{self.hostel.name} - Room {self.room_number}"
    
#     def get_available_beds_count(self, academic_year):
#         """Get count of available beds in this room for academic year"""
#         return self.beds.filter(
#             academic_year=academic_year,
#             is_available=True
#         ).count()
    
#     def get_occupied_beds_count(self, academic_year):
#         """Get count of occupied beds in this room for academic year"""
#         return self.beds.filter(
#             academic_year=academic_year,
#             is_available=False
#         ).count()
    
#     def is_full(self, academic_year):
#         """Check if room is fully occupied for academic year"""
#         return self.get_available_beds_count(academic_year) == 0

# class Bed(models.Model):
#     """Individual beds in rooms for each academic year"""
#     BED_POSITIONS = (
#         ('bed_1', 'Bed 1'),
#         ('bed_2', 'Bed 2'),
#         ('bed_3', 'Bed 3'),
#         ('bed_4', 'Bed 4'),
#     )
    
#     room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='beds')
#     academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='hostel_beds')
#     bed_position = models.CharField(max_length=10, choices=BED_POSITIONS)
#     bed_number = models.CharField(max_length=20, help_text="Unique bed identifier")
#     is_available = models.BooleanField(default=True)
#     maintenance_status = models.CharField(
#         max_length=20,
#         choices=(
#             ('good', 'Good Condition'),
#             ('needs_repair', 'Needs Repair'),
#             ('under_maintenance', 'Under Maintenance'),
#             ('out_of_order', 'Out of Order'),
#         ),
#         default='good'
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     class Meta:
#         unique_together = ['room', 'academic_year', 'bed_position']
#         ordering = ['room', 'bed_position']
    
#     def __str__(self):
#         return f"{self.room} - {self.bed_number} ({self.academic_year})"
    
#     def save(self, *args, **kwargs):
#         if not self.bed_number:
#             # Auto-generate bed number: HOSTEL_ROOM_BED_YEAR
#             hostel_code = self.room.hostel.name[:3].upper()
#             year_code = self.academic_year.year.split('/')[0][-2:]  # Last 2 digits of start year
#             self.bed_number = f"{hostel_code}{self.room.room_number}{self.bed_position[-1]}{year_code}"
#         super().save(*args, **kwargs)

# class HostelBooking(models.Model):
#     """Student hostel booking records"""
#     BOOKING_STATUS = (
#         ('pending', 'Pending Approval'),
#         ('approved', 'Approved'),
#         ('rejected', 'Rejected'),
#         ('cancelled', 'Cancelled'),
#         ('checked_in', 'Checked In'),
#         ('checked_out', 'Checked Out'),
#     )
    
#     PAYMENT_STATUS = (
#         ('pending', 'Payment Pending'),
#         ('partial', 'Partially Paid'),
#         ('paid', 'Fully Paid'),
#         ('refunded', 'Refunded'),
#     )
    
#     student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='hostel_bookings')
#     bed = models.ForeignKey(Bed, on_delete=models.CASCADE, related_name='bookings')
#     academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='hostel_bookings')
    
#     booking_date = models.DateTimeField(auto_now_add=True)
#     check_in_date = models.DateField(null=True, blank=True)
#     check_out_date = models.DateField(null=True, blank=True)
#     expected_checkout_date = models.DateField(null=True, blank=True)
    
#     booking_status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
#     payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
#     booking_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
#     amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
#     # Approval workflow
#     approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bookings')
#     approval_date = models.DateTimeField(null=True, blank=True)
#     approval_remarks = models.TextField(blank=True)
    
#     # Check-in/out details
#     checked_in_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_in_students')
#     checked_out_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_out_students')
    
#     remarks = models.TextField(blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         unique_together = ['student', 'academic_year']  # One booking per student per academic year
#         ordering = ['-booking_date']
    
#     def __str__(self):
#         return f"{self.student.registration_number} - {self.bed} ({self.academic_year})"
    
#     def save(self, *args, **kwargs):
#         # Update bed availability based on booking status
#         if self.pk:  # If updating existing booking
#             old_booking = HostelBooking.objects.get(pk=self.pk)
#             if old_booking.booking_status != self.booking_status:
#                 if self.booking_status in ['approved', 'checked_in']:
#                     self.bed.is_available = False
#                     self.bed.save()
#                 elif self.booking_status in ['rejected', 'cancelled', 'checked_out']:
#                     self.bed.is_available = True
#                     self.bed.save()
#         else:  # New booking
#             if self.booking_status in ['approved', 'checked_in']:
#                 self.bed.is_available = False
#                 self.bed.save()
        
#         super().save(*args, **kwargs)
    
#     @property
#     def balance_due(self):
#         """Calculate remaining balance"""
#         return self.booking_fee - self.amount_paid
    
#     @property
#     def is_fully_paid(self):
#         """Check if booking is fully paid"""
#         return self.amount_paid >= self.booking_fee

# class HostelPayment(models.Model):
#     """Track hostel fee payments"""
#     PAYMENT_METHODS = (
#         ('cash', 'Cash'),
#         ('bank_transfer', 'Bank Transfer'),
#         ('mobile_money', 'Mobile Money'),
#         ('cheque', 'Cheque'),
#         ('card', 'Credit/Debit Card'),
#     )
    
#     booking = models.ForeignKey(HostelBooking, on_delete=models.CASCADE, related_name='payments')
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     payment_date = models.DateField()
#     payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
#     reference_number = models.CharField(max_length=50, blank=True)
#     receipt_number = models.CharField(max_length=50, unique=True)
#     received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
#     remarks = models.TextField(blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     class Meta:
#         ordering = ['-payment_date']
    
#     def __str__(self):
#         return f"{self.booking.student.registration_number} - {self.amount} ({self.payment_date})"
    
#     def save(self, *args, **kwargs):
#         if not self.receipt_number:
#             # Auto-generate receipt number
#             year = timezone.now().year
#             count = HostelPayment.objects.filter(
#                 created_at__year=year
#             ).count() + 1
#             self.receipt_number = f"HPR{year}{count:05d}"
        
#         super().save(*args, **kwargs)
        
#         # Update booking payment status
#         booking = self.booking
#         total_paid = booking.payments.aggregate(
#             total=models.Sum('amount')
#         )['total'] or 0
#         booking.amount_paid = total_paid
        
#         if total_paid >= booking.booking_fee:
#             booking.payment_status = 'paid'
#         elif total_paid > 0:
#             booking.payment_status = 'partial'
#         else:
#             booking.payment_status = 'pending'
        
#         booking.save()

# class HostelIncident(models.Model):
#     """Track incidents and disciplinary issues in hostels"""
#     INCIDENT_TYPES = (
#         ('damage', 'Property Damage'),
#         ('noise', 'Noise Complaint'),
#         ('theft', 'Theft'),
#         ('violence', 'Violence/Fighting'),
#         ('drugs', 'Drug/Alcohol Related'),
#         ('curfew', 'Curfew Violation'),
#         ('cleanliness', 'Cleanliness Issue'),
#         ('other', 'Other'),
#     )
    
#     SEVERITY_LEVELS = (
#         ('low', 'Low'),
#         ('medium', 'Medium'),
#         ('high', 'High'),
#         ('critical', 'Critical'),
#     )
    
#     STATUS_CHOICES = (
#         ('reported', 'Reported'),
#         ('investigating', 'Under Investigation'),
#         ('resolved', 'Resolved'),
#         ('escalated', 'Escalated'),
#     )
    
#     booking = models.ForeignKey(HostelBooking, on_delete=models.CASCADE, related_name='incidents')
#     incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPES)
#     severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='low')
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reported')
    
#     incident_date = models.DateTimeField()
#     description = models.TextField()
#     action_taken = models.TextField(blank=True)
    
#     reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_incidents')
#     handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_incidents')
    
#     fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
#     fine_paid = models.BooleanField(default=False)
    
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         ordering = ['-incident_date']
    
#     def __str__(self):
#         return f"{self.booking.student.registration_number} - {self.get_incident_type_display()} ({self.incident_date.date()})"

# # Signal to create beds when academic year is created
# from django.db.models.signals import post_save
# from django.dispatch import receiver

# @receiver(post_save, sender=AcademicYear)
# def create_beds_for_new_academic_year(sender, instance, created, **kwargs):
#     """Automatically create beds for all active rooms when a new academic year is created"""
#     if created:
#         rooms = Room.objects.filter(is_active=True)
#         beds_to_create = []
        
#         for room in rooms:
#             for i in range(1, room.capacity + 1):
#                 bed_position = f"bed_{i}"
#                 beds_to_create.append(
#                     Bed(
#                         room=room,
#                         academic_year=instance,
#                         bed_position=bed_position,
#                         is_available=True
#                     )
#                 )
        
#         if beds_to_create:
#             Bed.objects.bulk_create(beds_to_create)

# # Management command helper function
# def setup_hostel_beds_for_existing_academic_years():
#     """
#     Helper function to create beds for existing academic years.
#     Run this as a management command after adding these models.
#     """
#     from django.db import transaction
    
#     with transaction.atomic():
#         academic_years = AcademicYear.objects.all()
#         rooms = Room.objects.filter(is_active=True)
        
#         for academic_year in academic_years:
#             for room in rooms:
#                 # Check if beds already exist for this room and academic year
#                 existing_beds = Bed.objects.filter(
#                     room=room,
#                     academic_year=academic_year
#                 ).count()
                
#                 if existing_beds == 0:
#                     beds_to_create = []
#                     for i in range(1, room.capacity + 1):
#                         bed_position = f"bed_{i}"
#                         beds_to_create.append(
#                             Bed(
#                                 room=room,
#                                 academic_year=academic_year,
#                                 bed_position=bed_position,
#                                 is_available=True
#                             )
#                         )
                    
#                     if beds_to_create:
#                         Bed.objects.bulk_create(beds_to_create)