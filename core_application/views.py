from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Count, Avg
from .models import Student, Enrollment, Unit, ProgrammeUnit, Semester, Grade
from decimal import Decimal

def student_login(request):
    """Custom login view for students"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None and user.user_type == 'student':
            login(request, user)
            return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not a student account')
    
    return render(request, 'student/auth/login.html')

from django.contrib.auth import logout
from django.shortcuts import redirect

def student_logout(request):
    logout(request)
    return redirect('student_login')  # This should match your login URL name


@login_required
def student_dashboard(request):
    """Main dashboard for logged-in students"""
    if request.user.user_type != 'student':
        return redirect('student_login')
    
    student = get_object_or_404(Student, user=request.user)
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get current semester enrollments
    current_enrollments = Enrollment.objects.filter(
        student=student,
        semester=current_semester,
        is_active=True
    ).select_related('unit')
    
    # Calculate semester progress
    total_semesters = student.programme.total_semesters
    completed_semesters = (student.current_year - 1) * student.programme.semesters_per_year + (student.current_semester - 1)
    progress_percentage = (completed_semesters / total_semesters) * 100 if total_semesters > 0 else 0
    
    # Calculate GPA (mock fee balance for now)
    fee_balance = Decimal('45000.00')  # This should come from a Fee model
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'current_enrollments': current_enrollments,
        'progress_percentage': round(progress_percentage, 1),
        'completed_semesters': completed_semesters,
        'total_semesters': total_semesters,
        'fee_balance': fee_balance,
    }
    
    return render(request, 'student/dashboard.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from collections import defaultdict
from .models import (
    Student, Unit, ProgrammeUnit, Enrollment, 
    Semester, AcademicYear, Programme
)

@login_required
def student_units_view(request):
    """
    Simplified view for student unit enrollment, history, and curriculum display
    """
    # Get student profile
    try:
        student = Student.objects.select_related(
            'user', 'programme', 'programme__school'
        ).get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('dashboard')
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Check if registration is open
    show_registration = False
    if current_semester:
        today = timezone.now().date()
        show_registration = (
            current_semester.registration_start_date <= today <= current_semester.registration_end_date
        )
    
    # Get available units for registration
    available_units = []
    if show_registration and current_semester:
        # Get programme units for student's current year and semester
        programme_units = ProgrammeUnit.objects.select_related('unit').filter(
            programme=student.programme,
            year=student.current_year,
            semester=student.current_semester,
            is_active=True,
            unit__is_active=True
        )
        
        # Get already enrolled units for current semester
        enrolled_unit_ids = Enrollment.objects.filter(
            student=student,
            semester=current_semester,
            is_active=True
        ).values_list('unit_id', flat=True)
        
        # Filter out already enrolled units
        available_programme_units = programme_units.exclude(
            unit_id__in=enrolled_unit_ids
        )
        
        for programme_unit in available_programme_units:
            available_units.append(programme_unit.unit)
    
    # Get enrollment history
    enrollments = Enrollment.objects.select_related(
        'unit', 'semester', 'semester__academic_year'
    ).filter(
        student=student,
        is_active=True
    ).order_by('-semester__academic_year__year', '-semester__semester_number')
    
    # Group enrollments by academic year and semester
    enrollment_history = {}
    for enrollment in enrollments:
        year_key = f"Year {enrollment.semester.academic_year.year}"
        sem_key = f"Semester {enrollment.semester.semester_number}"
        
        if year_key not in enrollment_history:
            enrollment_history[year_key] = {}
        if sem_key not in enrollment_history[year_key]:
            enrollment_history[year_key][sem_key] = []
            
        enrollment_history[year_key][sem_key].append(enrollment)
    
    # Get complete curriculum
    curriculum_data = {}
    programme_units = ProgrammeUnit.objects.select_related('unit').filter(
        programme=student.programme,
        is_active=True,
        unit__is_active=True
    ).order_by('year', 'semester', 'unit__name')
    
    for programme_unit in programme_units:
        year_key = f"Year {programme_unit.year}"
        sem_key = f"Semester {programme_unit.semester}"
        
        if year_key not in curriculum_data:
            curriculum_data[year_key] = {}
        if sem_key not in curriculum_data[year_key]:
            curriculum_data[year_key][sem_key] = []
            
        curriculum_data[year_key][sem_key].append(programme_unit.unit)
    
    # Handle POST request for unit enrollment
    if request.method == 'POST':
        return handle_unit_enrollment(request, student, current_semester, available_units)
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'show_registration': show_registration,
        'available_units': available_units,
        'enrollment_history': enrollment_history,
        'curriculum_data': curriculum_data,
    }
    
    return render(request, 'student/units.html', context)

@login_required
@require_POST
@transaction.atomic
def handle_unit_enrollment(request, student, current_semester, available_units):
    """
    Handle unit enrollment form submission
    """
    if not current_semester:
        messages.error(request, "No active semester found.")
        return redirect('student_units')
    
    # Check if registration is still open
    today = timezone.now().date()
    if not (current_semester.registration_start_date <= today <= current_semester.registration_end_date):
        messages.error(request, "Unit registration is closed.")
        return redirect('student_units')
    
    selected_unit_ids = request.POST.getlist('units')
    
    if not selected_unit_ids:
        messages.error(request, "Please select at least one unit to register.")
        return redirect('student_units')
    
    # Validate selected units
    available_unit_ids = [str(unit.id) for unit in available_units]
    invalid_units = [uid for uid in selected_unit_ids if uid not in available_unit_ids]
    
    if invalid_units:
        messages.error(request, "Some selected units are not available for enrollment.")
        return redirect('student_units')
    
    # Create enrollments
    enrolled_count = 0
    errors = []
    
    for unit_id in selected_unit_ids:
        try:
            unit = Unit.objects.get(id=unit_id, is_active=True)
            
            # Check if already enrolled
            existing_enrollment = Enrollment.objects.filter(
                student=student,
                unit=unit,
                semester=current_semester
            ).first()
            
            if existing_enrollment:
                if existing_enrollment.is_active:
                    errors.append(f"Already enrolled in {unit.name}")
                else:
                    # Reactivate existing enrollment
                    existing_enrollment.is_active = True
                    existing_enrollment.save()
                    enrolled_count += 1
            else:
                # Create new enrollment
                Enrollment.objects.create(
                    student=student,
                    unit=unit,
                    semester=current_semester,
                    is_active=True
                )
                enrolled_count += 1
                
        except Unit.DoesNotExist:
            errors.append(f"Unit with ID {unit_id} not found")
        except Exception as e:
            errors.append(f"Error enrolling in unit: {str(e)}")
    
    # Provide feedback
    if enrolled_count > 0:
        messages.success(
            request, 
            f"Successfully enrolled in {enrolled_count} unit{'s' if enrolled_count != 1 else ''}."
        )
    
    if errors:
        for error in errors:
            messages.error(request, error)
    
    return redirect('student_units')

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .models import User, Student

@login_required
def student_profile(request):
    student = request.user.student_profile
    
    if request.method == 'POST':
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            request.user.profile_picture = request.FILES['profile_picture']
            request.user.save()
            messages.success(request, 'Profile picture updated successfully!')
            return redirect('student_profile')
        
        # Handle password change
        if 'current_password' in request.POST:
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('student_profile')
            else:
                for error in form.errors.values():
                    messages.error(request, error)
                return redirect('student_profile#Password')
        
        # Handle profile updates
        try:
            # Update User model fields
            user_fields = ['first_name', 'last_name', 'email', 'phone', 'address']
            for field in user_fields:
                if field in request.POST:
                    setattr(request.user, field, request.POST[field])
            
            # Update Student model fields
            student_fields = ['guardian_name', 'guardian_phone', 'guardian_relationship', 
                            'guardian_address', 'emergency_contact', 'blood_group', 
                            'medical_conditions']
            for field in student_fields:
                if field in request.POST:
                    setattr(student, field, request.POST[field])
            
            request.user.save()
            student.save()
            messages.success(request, 'Profile updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
        
        return redirect('student_profile')
    
    context = {
        'student': student,
    }
    return render(request, 'student/student_profile.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Student, Semester, StudentReporting

@login_required
def student_reporting(request):
    student = get_object_or_404(Student, user=request.user)
    current_semester = Semester.objects.filter(is_current=True).first()
    reports = StudentReporting.objects.filter(student=student).order_by('-reporting_date')
    
    # Check if student has already reported for current semester
    has_reported = False
    if current_semester:
        has_reported = StudentReporting.objects.filter(
            student=student,
            semester=current_semester
        ).exists()
    
    if request.method == 'POST':
        if not current_semester:
            messages.error(request, "No active semester found for reporting.")
            return redirect('student_dashboard')
        
        if has_reported:
            messages.error(request, f"You have already reported for {current_semester}.")
            return redirect('student_reporting')
        
        remarks = request.POST.get('remarks', '')
        
        try:
            # Create new reporting record
            StudentReporting.objects.create(
                student=student,
                semester=current_semester,
                reporting_type='online',
                remarks=remarks,
                status='approved'  # Auto-approve online reporting
            )
            
            messages.success(request, f"Successfully reported for {current_semester}!")
            return redirect('student_reporting')
            
        except Exception as e:
            messages.error(request, f"Error submitting report: {str(e)}")
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'reports': reports,
        'has_reported': has_reported,
    }
    return render(request, 'student/student_reporting.html', context)