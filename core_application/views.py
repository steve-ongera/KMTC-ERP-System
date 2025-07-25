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
    View for student unit enrollment, history, and curriculum display
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
    
    # Get available units for current year and semester
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
        
        # Check prerequisites for each unit
        for programme_unit in available_programme_units:
            unit = programme_unit.unit
            can_enroll = True
            
            # Check if student has completed prerequisites
            if unit.prerequisites.exists():
                prerequisite_ids = unit.prerequisites.values_list('id', flat=True)
                completed_prerequisites = Enrollment.objects.filter(
                    student=student,
                    unit_id__in=prerequisite_ids,
                    is_active=True
                ).values_list('unit_id', flat=True)
                
                if set(prerequisite_ids) != set(completed_prerequisites):
                    can_enroll = False
            
            if can_enroll:
                available_units.append(unit)
    
    # Get enrollment history grouped by year and semester
    enrollment_groups = defaultdict(lambda: defaultdict(list))
    enrollments = Enrollment.objects.select_related(
        'unit', 'semester', 'semester__academic_year'
    ).filter(
        student=student,
        is_active=True
    ).order_by('-semester__academic_year__year', '-semester__semester_number')
    
    for enrollment in enrollments:
        # Determine year and semester from programme structure
        programme_unit = ProgrammeUnit.objects.filter(
            programme=student.programme,
            unit=enrollment.unit
        ).first()
        
        if programme_unit:
            year = programme_unit.year
            semester = programme_unit.semester
            enrollment_groups[year][semester].append(enrollment)
    
    # Get full curriculum for the programme
    curriculum = defaultdict(lambda: defaultdict(list))
    programme_units = ProgrammeUnit.objects.select_related('unit').filter(
        programme=student.programme,
        is_active=True,
        unit__is_active=True
    ).order_by('year', 'semester', 'unit__name')
    
    for programme_unit in programme_units:
        curriculum[programme_unit.year][programme_unit.semester].append(programme_unit.unit)
    
    # Handle POST request for unit enrollment
    if request.method == 'POST':
        return handle_unit_enrollment(request, student, current_semester, available_units)
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'show_registration': show_registration,
        'available_subjects': available_units,  # Using 'subjects' to match template
        'enrollment_groups': dict(enrollment_groups),
        'curriculum': dict(curriculum),
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
    
    
    selected_unit_ids = request.POST.getlist('subjects')  # Using 'subjects' to match template
    
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
            
            # Double-check prerequisites
            if unit.prerequisites.exists():
                prerequisite_ids = unit.prerequisites.values_list('id', flat=True)
                completed_prerequisites = Enrollment.objects.filter(
                    student=student,
                    unit_id__in=prerequisite_ids,
                    is_active=True
                ).count()
                
                if completed_prerequisites != len(prerequisite_ids):
                    errors.append(f"Prerequisites not met for {unit.name}")
                    continue
            
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

@login_required
def get_available_units_ajax(request):
    """
    AJAX endpoint to get available units for a specific year and semester
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student profile not found'}, status=404)
    
    year = request.GET.get('year')
    semester = request.GET.get('semester')
    
    if not year or not semester:
        return JsonResponse({'error': 'Year and semester are required'}, status=400)
    
    try:
        year = int(year)
        semester = int(semester)
    except ValueError:
        return JsonResponse({'error': 'Invalid year or semester format'}, status=400)
    
    # Get programme units for specified year and semester
    programme_units = ProgrammeUnit.objects.select_related('unit').filter(
        programme=student.programme,
        year=year,
        semester=semester,
        is_active=True,
        unit__is_active=True
    )
    
    # Get current semester for enrollment check
    current_semester = Semester.objects.filter(is_current=True).first()
    enrolled_unit_ids = []
    
    if current_semester:
        enrolled_unit_ids = Enrollment.objects.filter(
            student=student,
            semester=current_semester,
            is_active=True
        ).values_list('unit_id', flat=True)
    
    units_data = []
    for programme_unit in programme_units:
        unit = programme_unit.unit
        
        # Check prerequisites
        prerequisites = []
        if unit.prerequisites.exists():
            prerequisites = [
                {'code': prereq.code, 'name': prereq.name}
                for prereq in unit.prerequisites.all()
            ]
        
        units_data.append({
            'id': unit.id,
            'code': unit.code,
            'name': unit.name,
            'unit_type': unit.get_unit_type_display(),
            'credit_hours': unit.credit_hours,
            'is_enrolled': unit.id in enrolled_unit_ids,
            'prerequisites': prerequisites,
        })
    
    return JsonResponse({
        'units': units_data,
        'year': year,
        'semester': semester
    })

