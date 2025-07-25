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

@login_required
def available_units(request):
    """Show units available for enrollment based on student's year and semester"""
    if request.user.user_type != 'student':
        return redirect('student_login')
    
    student = get_object_or_404(Student, user=request.user)
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get units for current year and semester
    available_programme_units = ProgrammeUnit.objects.filter(
        programme=student.programme,
        year=student.current_year,
        semester=student.current_semester,
        is_active=True
    ).select_related('unit')
    
    # Get already enrolled units
    enrolled_units = Enrollment.objects.filter(
        student=student,
        semester=current_semester,
        is_active=True
    ).values_list('unit_id', flat=True)
    
    # Filter out already enrolled units
    available_units = available_programme_units.exclude(unit_id__in=enrolled_units)
    
    context = {
        'student': student,
        'available_units': available_units,
        'current_semester': current_semester,
    }
    
    return render(request, 'students/available_units.html', context)

@login_required
def student_profile(request):
    """Show student profile information"""
    if request.user.user_type != 'student':
        return redirect('student_login')
    
    student = get_object_or_404(Student, user=request.user)
    
    # Get academic performance stats
    enrollments = Enrollment.objects.filter(student=student)
    total_units = enrollments.count()
    
    # Get grades
    grades = Grade.objects.filter(enrollment__student=student)
    passed_units = grades.filter(is_passed=True).count()
    
    # Calculate current GPA
    graded_enrollments = grades.exclude(grade_points__isnull=True)
    if graded_enrollments.exists():
        total_credit_hours = sum([g.enrollment.unit.credit_hours for g in graded_enrollments])
        weighted_points = sum([g.grade_points * g.enrollment.unit.credit_hours for g in graded_enrollments])
        current_gpa = weighted_points / total_credit_hours if total_credit_hours > 0 else 0
    else:
        current_gpa = 0
    
    context = {
        'student': student,
        'total_units': total_units,
        'passed_units': passed_units,
        'current_gpa': round(current_gpa, 2),
    }
    
    return render(request, 'students/profile.html', context)

@login_required
def enroll_unit(request, unit_id):
    """Enroll student in a specific unit"""
    if request.user.user_type != 'student':
        return redirect('student_login')
    
    student = get_object_or_404(Student, user=request.user)
    unit = get_object_or_404(Unit, id=unit_id)
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Check if unit is available for student's current year/semester
    programme_unit = ProgrammeUnit.objects.filter(
        programme=student.programme,
        unit=unit,
        year=student.current_year,
        semester=student.current_semester,
        is_active=True
    ).first()
    
    if not programme_unit:
        messages.error(request, 'This unit is not available for your current year/semester.')
        return redirect('available_units')
    
    # Check if already enrolled
    existing_enrollment = Enrollment.objects.filter(
        student=student,
        unit=unit,
        semester=current_semester
    ).first()
    
    if existing_enrollment:
        messages.warning(request, 'You are already enrolled in this unit.')
        return redirect('available_units')
    
    # Create enrollment
    enrollment = Enrollment.objects.create(
        student=student,
        unit=unit,
        semester=current_semester
    )
    
    messages.success(request, f'Successfully enrolled in {unit.name}')
    return redirect('student_dashboard')