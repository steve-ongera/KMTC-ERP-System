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