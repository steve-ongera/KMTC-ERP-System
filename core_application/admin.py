from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import *

# Custom User Admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'date_joined', 'gender')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'national_id', 'phone')
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Personal Information', {
            'fields': ('user_type', 'phone', 'address', 'gender', 'date_of_birth', 
                      'profile_picture', 'national_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('created_at', 'updated_at')
        return self.readonly_fields

# Academic Structure Admins
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'dean', 'established_date', 'is_active', 'programme_count')
    list_filter = ('is_active', 'established_date')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('programme_count',)
    
    def programme_count(self, obj):
        return obj.programmes.count()
    programme_count.short_description = 'Number of Programmes'

@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'programme_type', 'category', 'school', 'duration_years', 'total_semesters', 'is_active', 'student_count')
    list_filter = ('programme_type', 'category', 'school', 'is_active', 'duration_years')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at', 'student_count')
    
    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = 'Enrolled Students'

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'unit_type', 'credit_hours', 'total_contact_hours', 'is_active')
    list_filter = ('unit_type', 'is_active', 'credit_hours')
    search_fields = ('name', 'code', 'description')
    filter_horizontal = ('prerequisites',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'unit_type', 'description', 'learning_outcomes')
        }),
        ('Credit & Contact Hours', {
            'fields': ('credit_hours', 'theory_hours', 'practical_hours', 'clinical_hours')
        }),
        ('Prerequisites', {
            'fields': ('prerequisites',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

@admin.register(ProgrammeUnit)
class ProgrammeUnitAdmin(admin.ModelAdmin):
    list_display = ('programme', 'unit', 'year', 'semester', 'is_mandatory', 'is_active')
    list_filter = ('year', 'semester', 'is_mandatory', 'is_active', 'programme__school')
    search_fields = ('programme__name', 'unit__name', 'programme__code', 'unit__code')

# People Admins
@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_number', 'school', 'designation', 'employment_type', 'experience_years', 'is_active')
    list_filter = ('school', 'designation', 'employment_type', 'is_active')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_number', 'specialization')
    readonly_fields = ('joining_date',)
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'employee_number', 'school')
        }),
        ('Employment Details', {
            'fields': ('designation', 'employment_type', 'joining_date', 'contract_end_date', 'salary')
        }),
        ('Professional Information', {
            'fields': ('qualifications', 'specialization', 'professional_registration', 
                      'experience_years', 'clinical_experience_years')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'registration_number', 'programme', 'current_year', 'current_semester', 'status', 'gpa')
    list_filter = ('programme', 'current_year', 'current_semester', 'status', 'sponsor_type', 'admission_type')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'registration_number', 'guardian_name')
    readonly_fields = ('admission_date', 'expected_graduation_date')
    
    fieldsets = (
        ('Student Information', {
            'fields': ('user', 'registration_number', 'programme')
        }),
        ('Academic Status', {
            'fields': ('current_year', 'current_semester', 'status', 'gpa', 'expected_graduation_date')
        }),
        ('Admission Details', {
            'fields': ('admission_date', 'admission_type', 'sponsor_type')
        }),
        ('Guardian Information', {
            'fields': ('guardian_name', 'guardian_phone', 'guardian_relationship', 'guardian_address', 'emergency_contact')
        }),
        ('Medical Information', {
            'fields': ('blood_group', 'medical_conditions')
        }),
    )

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_number', 'staff_category', 'school', 'designation', 'is_active')
    list_filter = ('staff_category', 'school', 'is_active')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_number', 'designation')

# Academic Records Admins
@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('year',)

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'semester_number', 'start_date', 'end_date', 'is_current')
    list_filter = ('academic_year', 'semester_number', 'is_current')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'unit', 'semester', 'enrollment_date', 'is_active', 'is_repeat')
    list_filter = ('semester', 'is_active', 'is_repeat', 'unit__unit_type')
    search_fields = ('student__registration_number', 'unit__name', 'unit__code')

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'grade', 'total_marks', 'grade_points', 'is_passed', 'exam_date')
    list_filter = ('grade', 'is_passed', 'exam_date')
    search_fields = ('enrollment__student__registration_number', 'enrollment__unit__code')
    readonly_fields = ('total_marks', 'grade', 'grade_points', 'is_passed')

# Fee Management Admins
@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('programme', 'academic_year', 'year', 'semester', 'total_fee', 'net_fee')
    list_filter = ('programme', 'academic_year', 'year', 'semester')
    search_fields = ('programme__name', 'programme__code')
    readonly_fields = ('total_fee', 'net_fee')

@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'receipt_number', 'amount_paid', 'payment_date', 'payment_method', 'payment_status')
    list_filter = ('payment_status', 'payment_method', 'payment_date')
    search_fields = ('student__registration_number', 'receipt_number', 'transaction_reference', 'mpesa_receipt')
    readonly_fields = ('receipt_number',)

# Clinical Training Admins
@admin.register(ClinicalSite)
class ClinicalSiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'facility_type', 'county', 'sub_county', 'capacity', 'is_active')
    list_filter = ('facility_type', 'county', 'is_active')
    search_fields = ('name', 'county', 'sub_county', 'contact_person')
    filter_horizontal = ('specializations',)

@admin.register(ClinicalPlacement)
class ClinicalPlacementAdmin(admin.ModelAdmin):
    list_display = ('student', 'clinical_site', 'unit', 'semester', 'start_date', 'end_date', 'is_completed')
    list_filter = ('clinical_site', 'semester', 'is_completed', 'unit')
    search_fields = ('student__registration_number', 'clinical_site__name', 'unit__code', 'supervisor_name')

# Attendance Admins
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'unit', 'date', 'session_type', 'status', 'marked_by')
    list_filter = ('status', 'session_type', 'date', 'unit')
    search_fields = ('student__registration_number', 'unit__code')
    date_hierarchy = 'date'

# Timetable Admins
@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'venue_code', 'venue_type', 'capacity', 'building', 'floor', 'is_active')
    list_filter = ('venue_type', 'building', 'is_active', 'has_projector', 'has_computer', 'has_internet')
    search_fields = ('name', 'venue_code', 'building')

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('day_of_week', 'start_time', 'end_time', 'is_active')
    list_filter = ('day_of_week', 'is_active')

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('unit', 'instructor', 'programme', 'year', 'venue', 'time_slot', 'session_type', 'is_active')
    list_filter = ('programme', 'year', 'session_type', 'semester', 'is_active')
    search_fields = ('unit__code', 'instructor__user__username', 'programme__code', 'venue__name')

# Examination Admins
@admin.register(Examination)
class ExaminationAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_type', 'semester', 'start_date', 'end_date', 'is_active')
    list_filter = ('exam_type', 'semester', 'is_active')
    search_fields = ('name',)

@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ('examination', 'unit', 'programme', 'year', 'exam_date', 'start_time', 'venue')
    list_filter = ('examination', 'programme', 'year', 'exam_date')
    search_fields = ('unit__code', 'programme__code', 'venue__name')
    filter_horizontal = ('invigilators',)

# Library Management Admins
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'category', 'total_copies', 'available_copies', 'publication_year')
    list_filter = ('category', 'publication_year', 'publisher')
    search_fields = ('title', 'author', 'isbn', 'publisher')
    filter_horizontal = ('related_units',)

@admin.register(BookIssue)
class BookIssueAdmin(admin.ModelAdmin):
    list_display = ('student', 'book', 'issue_date', 'due_date', 'return_date', 'is_returned', 'fine_amount')
    list_filter = ('is_returned', 'issue_date', 'due_date')
    search_fields = ('student__registration_number', 'book__title', 'book__isbn')
    date_hierarchy = 'issue_date'

# Hostel Management Admins
@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ('name', 'hostel_type', 'total_rooms', 'capacity', 'available_capacity', 'warden_name', 'is_active')
    list_filter = ('hostel_type', 'is_active')
    search_fields = ('name', 'warden_name')

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('hostel', 'room_number', 'room_type', 'capacity', 'floor', 'monthly_rent', 'is_available')
    list_filter = ('hostel', 'room_type', 'floor', 'is_available')
    search_fields = ('room_number', 'hostel__name')

@admin.register(RoomAllocation)
class RoomAllocationAdmin(admin.ModelAdmin):
    list_display = ('student', 'room', 'academic_year', 'allocation_date', 'checkout_date', 'is_active')
    list_filter = ('academic_year', 'is_active', 'room__hostel')
    search_fields = ('student__registration_number', 'room__room_number')

# Student Services Admins
@admin.register(StudentService)
class StudentServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type', 'contact_person', 'contact_phone', 'location', 'is_active')
    list_filter = ('service_type', 'is_active')
    search_fields = ('name', 'contact_person', 'location')

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'service', 'request_date', 'status', 'assigned_to')
    list_filter = ('status', 'service', 'request_date')
    search_fields = ('student__registration_number', 'service__name', 'description')
    date_hierarchy = 'request_date'

# Notification Admins
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'priority', 'is_global', 'is_active', 'created_by', 'created_at')
    list_filter = ('notification_type', 'priority', 'is_global', 'is_active', 'created_at')
    search_fields = ('title', 'message')
    filter_horizontal = ('target_programmes', 'target_users')
    date_hierarchy = 'created_at'

@admin.register(NotificationRead)
class NotificationReadAdmin(admin.ModelAdmin):
    list_display = ('notification', 'user', 'read_at')
    list_filter = ('read_at',)
    search_fields = ('notification__title', 'user__username')

# Research & Projects Admins
@admin.register(ResearchProject)
class ResearchProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'project_type', 'supervisor', 'start_date', 'submission_date', 'is_completed', 'grade')
    list_filter = ('project_type', 'is_completed', 'supervisor', 'unit')
    search_fields = ('title', 'supervisor__user__username')
    filter_horizontal = ('students',)

# Professional Bodies Admins
@admin.register(ProfessionalBody)
class ProfessionalBodyAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'annual_fee', 'contact_email')
    search_fields = ('name', 'abbreviation')

@admin.register(ProfessionalRegistration)
class ProfessionalRegistrationAdmin(admin.ModelAdmin):
    list_display = ('student', 'professional_body', 'registration_number', 'status', 'application_date', 'approval_date')
    list_filter = ('professional_body', 'status', 'application_date')
    search_fields = ('student__registration_number', 'registration_number', 'professional_body__name')

# Alumni Admins
@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):
    list_display = ('student', 'graduation_date', 'current_employer', 'current_position', 'is_willing_mentor')
    list_filter = ('graduation_date', 'is_willing_mentor')
    search_fields = ('student__user__username', 'current_employer', 'current_position')

# Quality Assurance Admins
@admin.register(QualityAssessment)
class QualityAssessmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'assessment_type', 'semester', 'start_date', 'end_date', 'is_active')
    list_filter = ('assessment_type', 'semester', 'is_active')
    search_fields = ('title', 'description')

@admin.register(QualityAssessmentResponse)
class QualityAssessmentResponseAdmin(admin.ModelAdmin):
    list_display = ('assessment', 'respondent', 'submitted_at')
    list_filter = ('assessment', 'submitted_at')
    search_fields = ('assessment__title', 'respondent__username')

# Student Support Admins
@admin.register(StudentComment)
class StudentCommentAdmin(admin.ModelAdmin):
    list_display = ('student', 'category', 'subject', 'priority', 'is_resolved', 'created_at', 'responded_by')
    list_filter = ('category', 'priority', 'is_resolved', 'created_at')
    search_fields = ('student__registration_number', 'subject', 'comment')
    date_hierarchy = 'created_at'

# Medical Records Admins
@admin.register(StudentMedicalRecord)
class StudentMedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'emergency_medical_contact', 'insurance_provider', 'last_medical_checkup')
    search_fields = ('student__registration_number', 'emergency_medical_contact', 'insurance_provider')

@admin.register(MedicalVisit)
class MedicalVisitAdmin(admin.ModelAdmin):
    list_display = ('student', 'visit_date', 'diagnosis', 'medical_officer', 'follow_up_required')
    list_filter = ('visit_date', 'follow_up_required', 'medical_officer')
    search_fields = ('student__registration_number', 'diagnosis', 'symptoms')
    date_hierarchy = 'visit_date'

# System Configuration Admins
@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'config_type', 'value', 'is_active', 'updated_at', 'updated_by')
    list_filter = ('config_type', 'is_active', 'updated_at')
    search_fields = ('key', 'value', 'description')

# Admin Site Customization
admin.site.site_header = "KMTC ERP Administration"
admin.site.site_title = "KMTC ERP Admin"
admin.site.index_title = "Welcome to KMTC ERP Administration"