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

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import (
    Hostel, Room, Bed, HostelBooking, AcademicYear, 
    Semester, Student
)
import json


@login_required
def hostel_booking_eligibility(request):
    """Check if student is eligible for hostel booking"""
    try:
        student = request.user.student_profile
        
        # Check if student is in year 1
        if student.current_year != 1:
            messages.error(request, "Only first-year students are eligible for hostel booking.")
            return redirect('student_dashboard')
        
        # Check if student is active
        if student.status != 'active':
            messages.error(request, "Only active students can book hostels.")
            return redirect('student_dashboard')
        
        # Get current academic year
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_academic_year:
            messages.error(request, "No current academic year found.")
            return redirect('student_dashboard')
        
        # Check if student already has a booking for current academic year
        existing_booking = HostelBooking.objects.filter(
            student=student,
            academic_year=current_academic_year
        ).first()
        
        if existing_booking:
            messages.info(request, f"You already have a hostel booking for {current_academic_year.year}.")
            return redirect('hostel_booking_detail', booking_id=existing_booking.id)
        
        return redirect('hostel_list')
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')


@login_required
def hostel_list(request):
    """Display available hostels based on student's gender"""
    try:
        student = request.user.student_profile
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        
        if not current_academic_year:
            messages.error(request, "No current academic year found.")
            return redirect('dashboard')
        
        # Determine hostel type based on student's gender
        if student.user.gender == 'male':
            hostel_type = 'boys'
        elif student.user.gender == 'female':
            hostel_type = 'girls'
        else:
            messages.error(request, "Please update your gender in profile to book hostel.")
            return redirect('student_profile')
        
        # Get active hostels for the student's school and gender
        hostels = Hostel.objects.filter(
            hostel_type=hostel_type,
            #school=student.programme.school,
            is_active=True
        )
        
        # Add availability information to each hostel
        hostel_data = []
        for hostel in hostels:
            total_beds = hostel.get_total_beds_count(current_academic_year)
            occupied_beds = hostel.get_occupied_beds_count(current_academic_year)
            available_beds = total_beds - occupied_beds
            
            hostel_data.append({
                'hostel': hostel,
                'total_beds': total_beds,
                'occupied_beds': occupied_beds,
                'available_beds': available_beds,
                'occupancy_rate': (occupied_beds / total_beds * 100) if total_beds > 0 else 0
            })
        
        context = {
            'hostel_data': hostel_data,
            'student': student,
            'academic_year': current_academic_year,
        }
        
        return render(request, 'hostels/hostel_list.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')


@login_required
def room_list(request, hostel_id):
    """Display available rooms in selected hostel"""
    try:
        student = request.user.student_profile
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        hostel = get_object_or_404(Hostel, id=hostel_id, is_active=True)
        
        # Verify hostel matches student's gender and school
        hostel_type = 'boys' if student.user.gender == 'male' else 'girls'
        if hostel.hostel_type != hostel_type :
            messages.error(request, "You are not eligible for this hostel.")
            return redirect('hostel_list')
        
        # Get rooms with available beds
        rooms = Room.objects.filter(
            hostel=hostel,
            is_active=True
        ).order_by('floor', 'room_number')
        
        room_data = []
        for room in rooms:
            available_beds = room.get_available_beds_count(current_academic_year)
            occupied_beds = room.get_occupied_beds_count(current_academic_year)
            
            if available_beds > 0:  # Only show rooms with available beds
                room_data.append({
                    'room': room,
                    'available_beds': available_beds,
                    'occupied_beds': occupied_beds,
                    'total_capacity': room.capacity
                })
        
        context = {
            'hostel': hostel,
            'room_data': room_data,
            'student': student,
            'academic_year': current_academic_year,
        }
        
        return render(request, 'hostels/room_list.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')


@login_required
def bed_list(request, room_id):
    """Display available beds in selected room"""
    try:
        student = request.user.student_profile
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        room = get_object_or_404(Room, id=room_id, is_active=True)
        
        # Verify room's hostel matches student's eligibility
        hostel_type = 'boys' if student.user.gender == 'male' else 'girls'
        if (room.hostel.hostel_type != hostel_type ):
            messages.error(request, "You are not eligible for this room.")
            return redirect('hostel_list')
        
        # Get available beds
        available_beds = Bed.objects.filter(
            room=room,
            academic_year=current_academic_year,
            is_available=True,
            maintenance_status='good'
        ).order_by('bed_position')
        
        # Get occupied beds for display
        occupied_beds = Bed.objects.filter(
            room=room,
            academic_year=current_academic_year,
            is_available=False
        ).order_by('bed_position')
        
        context = {
            'room': room,
            'available_beds': available_beds,
            'occupied_beds': occupied_beds,
            'student': student,
            'academic_year': current_academic_year,
        }
        
        return render(request, 'hostels/bed_list.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')


@login_required
def book_bed(request, bed_id):
    """Book a specific bed"""
    try:
        student = request.user.student_profile
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        bed = get_object_or_404(Bed, id=bed_id)
        
        # Verify bed eligibility
        hostel_type = 'boys' if student.user.gender == 'male' else 'girls'
        if (bed.room.hostel.hostel_type != hostel_type ):
            messages.error(request, "You are not eligible for this bed.")
            return redirect('hostel_list')
        
        # Check if bed is available
        if not bed.is_available or bed.maintenance_status != 'good':
            messages.error(request, "This bed is not available for booking.")
            return redirect('bed_list', room_id=bed.room.id)
        
        # Check if student already has a booking
        existing_booking = HostelBooking.objects.filter(
            student=student,
            academic_year=current_academic_year
        ).first()
        
        if existing_booking:
            messages.error(request, "You already have a hostel booking for this academic year.")
            return redirect('hostel_booking_detail', booking_id=existing_booking.id)
        
        if request.method == 'POST':
            try:
                with transaction.atomic():
                    # Create the booking
                    booking = HostelBooking.objects.create(
                        student=student,
                        bed=bed,
                        academic_year=current_academic_year,
                        booking_fee=5000.00,  # Default booking fee - you can make this configurable
                        booking_status='pending',
                        payment_status='pending'
                    )
                    
                    messages.success(request, f"Your hostel booking has been submitted successfully! Booking reference: {booking.id}")
                    return redirect('hostel_booking_detail', booking_id=booking.id)
                    
            except ValidationError as e:
                messages.error(request, f"Booking failed: {e}")
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
        
        context = {
            'bed': bed,
            'student': student,
            'academic_year': current_academic_year,
            'booking_fee': 5000.00,  # Make this configurable
        }
        
        return render(request, 'hostels/book_bed.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('dashboard')


@login_required
def hostel_booking_detail(request, booking_id):
    """Display booking details"""
    try:
        student = request.user.student_profile
        booking = get_object_or_404(
            HostelBooking, 
            id=booking_id, 
            student=student
        )
        
        context = {
            'booking': booking,
            'student': student,
        }
        
        return render(request, 'hostels/booking_detail.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')


@login_required
def cancel_booking(request, booking_id):
    """Cancel a hostel booking"""
    try:
        student = request.user.student_profile
        booking = get_object_or_404(
            HostelBooking, 
            id=booking_id, 
            student=student
        )
        
        # Only allow cancellation if booking is pending
        if booking.booking_status not in ['pending', 'approved']:
            messages.error(request, "This booking cannot be cancelled.")
            return redirect('hostel_booking_detail', booking_id=booking_id)
        
        if request.method == 'POST':
            booking.booking_status = 'cancelled'
            booking.save()
            messages.success(request, "Your hostel booking has been cancelled.")
            return redirect('hostel_list')
        
        context = {
            'booking': booking,
        }
        
        return render(request, 'hostels/cancel_booking.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')


# AJAX Views
@login_required
def get_rooms_ajax(request):
    """AJAX endpoint to get rooms for a hostel"""
    hostel_id = request.GET.get('hostel_id')
    if not hostel_id:
        return JsonResponse({'error': 'Hostel ID required'}, status=400)
    
    try:
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        rooms = Room.objects.filter(
            hostel_id=hostel_id,
            is_active=True
        ).order_by('floor', 'room_number')
        
        room_data = []
        for room in rooms:
            available_beds = room.get_available_beds_count(current_academic_year)
            if available_beds > 0:
                room_data.append({
                    'id': room.id,
                    'room_number': room.room_number,
                    'floor': room.floor,
                    'available_beds': available_beds,
                    'capacity': room.capacity
                })
        
        return JsonResponse({'rooms': room_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_beds_ajax(request):
    """AJAX endpoint to get beds for a room"""
    room_id = request.GET.get('room_id')
    if not room_id:
        return JsonResponse({'error': 'Room ID required'}, status=400)
    
    try:
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        beds = Bed.objects.filter(
            room_id=room_id,
            academic_year=current_academic_year,
            is_available=True,
            maintenance_status='good'
        ).order_by('bed_position')
        
        bed_data = []
        for bed in beds:
            bed_data.append({
                'id': bed.id,
                'bed_number': bed.bed_number,
                'bed_position': bed.get_bed_position_display(),
                'maintenance_status': bed.get_maintenance_status_display()
            })
        
        return JsonResponse({'beds': bed_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import logging

logger = logging.getLogger(__name__)

@csrf_protect
@require_http_methods(["GET", "POST"])
def admin_login_view(request):
    """
    Admin login view with enhanced security and validation
    """
    # Redirect if already authenticated and is staff/admin
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_dashboard')  # Replace with your admin dashboard URL
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        remember_me = request.POST.get('RememberMe') == 'on'
        
        # Basic validation
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'admin/admin_login.html')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user is admin/staff
            if user.is_staff or user.is_superuser:
                if user.is_active:
                    login(request, user)
                    
                    # Handle remember me functionality
                    if remember_me:
                        request.session.set_expiry(1209600)  # 2 weeks
                    else:
                        request.session.set_expiry(0)  # Browser close
                    
                    # Log successful login
                    logger.info(f"Admin login successful for user: {username}")
                    
                    messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                    
                    # Redirect to next page or dashboard
                    next_url = request.GET.get('next', 'admin_dashboard')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Your account has been deactivated. Please contact support.')
            else:
                messages.error(request, 'Access denied. Admin privileges required.')
                logger.warning(f"Non-admin user attempted admin login: {username}")
        else:
            messages.error(request, 'Invalid username or password.')
            logger.warning(f"Failed admin login attempt for username: {username}")
    
    return render(request, 'admin/admin_login.html')

@login_required
def admin_logout_view(request):
    """
    Admin logout view
    """
    username = request.user.username
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    logger.info(f"Admin logout for user: {username}")
    return redirect('admin_login')

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models.functions import TruncMonth, TruncYear
import json
from collections import defaultdict

from .models import (
    User, Student, Instructor, Staff, School, Programme, Unit, 
    AcademicYear, Semester, Enrollment, Grade, FeePayment, 
    ClinicalPlacement, Attendance, StudentReporting, FeeStructure
)


def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.user_type == 'admin'


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    Admin dashboard with comprehensive statistics and charts
    """
    # Get current date and academic year
    current_date = timezone.now().date()
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Basic User Statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    new_users_today = User.objects.filter(created_at__date=current_date).count()
    
    # Student Statistics
    total_students = Student.objects.count()
    active_students = Student.objects.filter(status='active').count()
    new_students_today = Student.objects.filter(
        user__created_at__date=current_date
    ).count()
    
    # Faculty Statistics
    total_faculty = Instructor.objects.count()
    active_faculty = Instructor.objects.filter(is_active=True).count()
    
    # Staff Statistics
    total_staff = Staff.objects.count()
    active_staff = Staff.objects.filter(is_active=True).count()
    
    # Academic Overview
    total_schools = School.objects.filter(is_active=True).count()
    total_programmes = Programme.objects.filter(is_active=True).count()
    total_units = Unit.objects.filter(is_active=True).count()
    
    # Financial Overview
    total_fee_payments = FeePayment.objects.filter(
        payment_status='completed'
    ).count()
    today_fee_payments = FeePayment.objects.filter(
        payment_date=current_date,
        payment_status='completed'
    ).count()
    
    # Recent payments (last 10)
    recent_payments = FeePayment.objects.filter(
        payment_status='completed'
    ).select_related('student__user').order_by('-payment_date')[:10]
    
    # Gender Distribution Data for Donut Chart
    gender_data = Student.objects.filter(status='active').values(
        'user__gender'
    ).annotate(count=Count('id'))
    
    gender_chart_data = {
        'labels': [],
        'data': [],
        'colors': ['#FF6384', '#36A2EB', '#FFCE56']
    }
    
    for item in gender_data:
        gender = item['user__gender']
        if gender == 'male':
            gender_chart_data['labels'].append('Male')
            gender_chart_data['data'].append(item['count'])
        elif gender == 'female':
            gender_chart_data['labels'].append('Female')
            gender_chart_data['data'].append(item['count'])
        elif gender == 'other':
            gender_chart_data['labels'].append('Other')
            gender_chart_data['data'].append(item['count'])
    
    # Student Admission Trends (Bar Chart) - Last 5 years
    current_year = current_date.year
    admission_years = []
    admission_counts = []
    
    for year in range(current_year - 4, current_year + 1):
        year_start = datetime(year, 1, 1).date()
        year_end = datetime(year, 12, 31).date()
        count = Student.objects.filter(
            admission_date__range=[year_start, year_end]
        ).count()
        admission_years.append(str(year))
        admission_counts.append(count)
    
    admission_trend_data = {
        'labels': admission_years,
        'data': admission_counts
    }
    
    # Student Enrollment by Programme (Line Chart)
    programme_enrollment = Programme.objects.filter(
        is_active=True
    ).annotate(
        student_count=Count('students', filter=Q(students__status='active'))
    ).order_by('-student_count')[:10]
    
    programme_chart_data = {
        'labels': [p.name[:20] + '...' if len(p.name) > 20 else p.name 
                  for p in programme_enrollment],
        'data': [p.student_count for p in programme_enrollment]
    }
    
    # Student Reporting in Last 6 Semesters
    last_6_semesters = Semester.objects.order_by('-academic_year__start_date', '-semester_number')[:6]
    reporting_data = []
    
    for semester in last_6_semesters:
        total_expected = Student.objects.filter(status='active').count()
        reported = StudentReporting.objects.filter(
            semester=semester,
            status='approved'
        ).count()
        
        reporting_data.append({
            'semester': f"{semester.academic_year.year} S{semester.semester_number}",
            'reported': reported,
            'expected': total_expected,
            'percentage': round((reported/total_expected * 100) if total_expected > 0 else 0, 1)
        })
    
    reporting_chart_data = {
        'labels': [item['semester'] for item in reversed(reporting_data)],
        'reported': [item['reported'] for item in reversed(reporting_data)],
        'expected': [item['expected'] for item in reversed(reporting_data)],
        'percentages': [item['percentage'] for item in reversed(reporting_data)]
    }
    
    # Fee Collection Trends (Last 12 months)
    twelve_months_ago = current_date - timedelta(days=365)
    monthly_collections = FeePayment.objects.filter(
        payment_date__gte=twelve_months_ago,
        payment_status='completed'
    ).extra(
        select={'month': "strftime('%%Y-%%m', payment_date)"}
    ).values('month').annotate(
        total_amount=Sum('amount_paid'),
        payment_count=Count('id')
    ).order_by('month')
    
    collection_labels = []
    collection_amounts = []
    collection_counts = []
    
    for collection in monthly_collections:
        month_year = datetime.strptime(collection['month'], '%Y-%m')
        collection_labels.append(month_year.strftime('%b %Y'))
        collection_amounts.append(float(collection['total_amount'] or 0))
        collection_counts.append(collection['payment_count'])
    
    collection_chart_data = {
        'labels': collection_labels,
        'amounts': collection_amounts,
        'counts': collection_counts
    }
    
    # Attendance Summary
    if current_semester:
        attendance_summary = Attendance.objects.filter(
            date__gte=current_semester.start_date,
            date__lte=current_semester.end_date
        ).values('status').annotate(count=Count('id'))
    else:
        attendance_summary = []
    
    # Programme Performance (Average GPA by Programme) - FIXED
    programme_performance = []
    for programme in Programme.objects.filter(is_active=True)[:10]:
        avg_gpa = Grade.objects.filter(
            enrollment__student__programme=programme,
            is_passed=True
        ).aggregate(avg_gpa=Avg('grade_points'))['avg_gpa']
        
        if avg_gpa:
            programme_performance.append({
                'programme': programme.name[:20] + '...' if len(programme.name) > 20 else programme.name,
                'avg_gpa': float(avg_gpa)  # Convert Decimal to float
            })
    
    programme_performance.sort(key=lambda x: x['avg_gpa'], reverse=True)
    
    performance_chart_data = {
        'labels': [item['programme'] for item in programme_performance],
        'data': [item['avg_gpa'] for item in programme_performance]
    }
    
    # Clinical Placements Summary
    active_placements = ClinicalPlacement.objects.filter(
        start_date__lte=current_date,
        end_date__gte=current_date
    ).count()
    
    completed_placements = ClinicalPlacement.objects.filter(
        is_completed=True
    ).count()
    
    # Recent Activities (Student Registrations, Payments, etc.)
    recent_activities = []
    
    # Recent student registrations
    recent_students = Student.objects.select_related('user', 'programme').order_by('-user__created_at')[:5]
    for student in recent_students:
        recent_activities.append({
            'type': 'student_registration',
            'message': f"New student {student.user.get_full_name()} registered for {student.programme.name}",
            'date': student.user.created_at,
            'icon': 'fa-user-plus',
            'color': 'success'
        })
    
    # Recent payments
    recent_fee_payments = FeePayment.objects.select_related('student__user').order_by('-payment_date')[:5]
    for payment in recent_fee_payments:
        recent_activities.append({
            'type': 'fee_payment',
            'message': f"Fee payment of KES {payment.amount_paid} received from {payment.student.user.get_full_name()}",
            'date': payment.payment_date,
            'icon': 'fa-money-bill',
            'color': 'info'
        })
    
    # Sort activities by date
    recent_activities.sort(key=lambda x: x['date'], reverse=True)
    recent_activities = recent_activities[:10]
    
    # Top Performing Students (by GPA) - FIXED
    top_students = []
    for student in Student.objects.filter(status='active')[:20]:
        avg_gpa = Grade.objects.filter(
            enrollment__student=student,
            is_passed=True
        ).aggregate(avg_gpa=Avg('grade_points'))['avg_gpa']
        
        if avg_gpa and avg_gpa > 0:
            top_students.append({
                'student': student,
                'gpa': float(avg_gpa)  # Convert Decimal to float
            })
    
    top_students.sort(key=lambda x: x['gpa'], reverse=True)
    top_students = top_students[:10]
    
    context = {
        'current_date': current_date,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        
        # Basic Statistics
        'total_users': total_users,
        'active_users': active_users,
        'new_users_today': new_users_today,
        'total_students': total_students,
        'active_students': active_students,
        'new_students_today': new_students_today,
        'total_faculty': total_faculty,
        'active_faculty': active_faculty,
        'total_staff': total_staff,
        'active_staff': active_staff,
        
        # Academic Overview
        'total_schools': total_schools,
        'total_programmes': total_programmes,
        'total_units': total_units,
        
        # Financial Overview
        'total_fee_payments': total_fee_payments,
        'today_fee_payments': today_fee_payments,
        'recent_payments': recent_payments,
        
        # Clinical Overview
        'active_placements': active_placements,
        'completed_placements': completed_placements,
        
        # Chart Data (JSON)
        'gender_chart_data': json.dumps(gender_chart_data),
        'admission_trend_data': json.dumps(admission_trend_data),
        'programme_chart_data': json.dumps(programme_chart_data),
        'reporting_chart_data': json.dumps(reporting_chart_data),
        'collection_chart_data': json.dumps(collection_chart_data),
        'performance_chart_data': json.dumps(performance_chart_data),
        
        # Additional Data
        'attendance_summary': attendance_summary,
        'recent_activities': recent_activities,
        'top_students': top_students,
        'programme_performance': programme_performance,
        'reporting_data': reporting_data,
    }
    
    return render(request, 'admin/dashboard.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Student, Programme, School, User
from django.urls import reverse


@login_required
def student_list(request):
    """
    Display a paginated list of students with search and filter functionality
    """
    # Get all students with related data to avoid N+1 queries
    students = Student.objects.select_related(
        'user', 'programme', 'programme__school'
    ).all()
    
    # Get filter parameters from request
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    programme_filter = request.GET.get('programme', '')
    school_filter = request.GET.get('school', '')
    year_filter = request.GET.get('year', '')
    semester_filter = request.GET.get('semester', '')
    admission_type_filter = request.GET.get('admission_type', '')
    sponsor_type_filter = request.GET.get('sponsor_type', '')
    
    # Apply search filter
    if search_query:
        students = students.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(registration_number__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(programme__name__icontains=search_query) |
            Q(programme__code__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter:
        students = students.filter(status=status_filter)
    
    # Apply programme filter
    if programme_filter:
        students = students.filter(programme_id=programme_filter)
    
    # Apply school filter
    if school_filter:
        students = students.filter(programme__school_id=school_filter)
    
    # Apply year filter
    if year_filter:
        students = students.filter(current_year=year_filter)
    
    # Apply semester filter
    if semester_filter:
        students = students.filter(current_semester=semester_filter)
    
    # Apply admission type filter
    if admission_type_filter:
        students = students.filter(admission_type=admission_type_filter)
    
    # Apply sponsor type filter
    if sponsor_type_filter:
        students = students.filter(sponsor_type=sponsor_type_filter)
    
    # Order students by registration number
    students = students.order_by('-admission_date', 'registration_number')
    
    # Pagination
    paginator = Paginator(students, 20)  # Show 20 students per page
    page = request.GET.get('page', 1)
    
    try:
        students_page = paginator.page(page)
    except PageNotAnInteger:
        students_page = paginator.page(1)
    except EmptyPage:
        students_page = paginator.page(paginator.num_pages)
    
    # Get data for filter dropdowns
    status_choices = Student.STATUS_CHOICES
    programmes = Programme.objects.filter(is_active=True).order_by('name')
    schools = School.objects.filter(is_active=True).order_by('name')
    admission_type_choices = Student.ADMISSION_TYPES
    sponsor_type_choices = Student.SPONSOR_TYPES
    
    # Year and semester choices (based on your model validators)
    year_choices = [(i, f'Year {i}') for i in range(1, 5)]  # 1-4 years
    semester_choices = [(i, f'Semester {i}') for i in range(1, 4)]  # 1-3 semesters
    
    context = {
        'students': students_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'programme_filter': programme_filter,
        'school_filter': school_filter,
        'year_filter': year_filter,
        'semester_filter': semester_filter,
        'admission_type_filter': admission_type_filter,
        'sponsor_type_filter': sponsor_type_filter,
        
        # Filter options
        'status_choices': status_choices,
        'programmes': programmes,
        'schools': schools,
        'year_choices': year_choices,
        'semester_choices': semester_choices,
        'admission_type_choices': admission_type_choices,
        'sponsor_type_choices': sponsor_type_choices,
        
        # Statistics
        'total_students': students.count(),
        'active_students': Student.objects.filter(status='active').count(),
        'graduated_students': Student.objects.filter(status='graduated').count(),
    }
    
    return render(request, 'admin/students/student_list.html', context)


@login_required
def student_detail(request, registration_number):
    """
    Display detailed information for a specific student
    """
    student = get_object_or_404(
        Student.objects.select_related(
            'user', 'programme', 'programme__school'
        ),
        registration_number=registration_number
    )
    
    context = {
        'student': student,
    }
    
    return render(request, 'admin/students/student_detail.html', context)


# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password
from django.db import transaction
from .models import User, Student, Programme, School
from .forms import UserForm, StudentForm


@login_required
def student_create(request):
    """
    Create a new student record
    """
    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES)
        student_form = StudentForm(request.POST)
        
        if user_form.is_valid() and student_form.is_valid():
            try:
                with transaction.atomic():
                    # Create user
                    user = user_form.save(commit=False)
                    user.user_type = 'student'
                    
                    # Set password
                    password = user_form.cleaned_data.get('password')
                    if password:
                        user.password = make_password(password)
                    
                    user.save()
                    
                    # Create student profile
                    student = student_form.save(commit=False)
                    student.user = user
                    student.save()
                    
                    messages.success(request, f'Student {user.get_full_name()} created successfully!')
                    return redirect('student_list')
                    
            except Exception as e:
                messages.error(request, f'Error creating student: {str(e)}')
        else:
            # Add form errors to messages
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            for field, errors in student_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        user_form = UserForm()
        student_form = StudentForm()
    
    # Get data for form dropdowns
    programmes = Programme.objects.filter(is_active=True).order_by('name')
    schools = School.objects.filter(is_active=True).order_by('name')
    
    context = {
        'user_form': user_form,
        'student_form': student_form,
        'action': 'Create',
        'programmes': programmes,
        'schools': schools,
        'status_choices': Student.STATUS_CHOICES,
        'admission_type_choices': Student.ADMISSION_TYPES,
        'sponsor_type_choices': Student.SPONSOR_TYPES,
        'gender_choices': User.GENDER_CHOICES,
    }
    
    return render(request, 'admin/students/student_form.html', context)


@login_required
def student_update(request, registration_number):
    """
    Update an existing student record
    """
    student = get_object_or_404(Student, registration_number=registration_number)
    user = student.user
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES, instance=user, is_update=True)
        student_form = StudentForm(request.POST, instance=student)
        
        if user_form.is_valid() and student_form.is_valid():
            try:
                with transaction.atomic():
                    # Update user
                    user = user_form.save(commit=False)
                    
                    # Update password if provided
                    password = user_form.cleaned_data.get('password')
                    if password:
                        user.password = make_password(password)
                    
                    user.save()
                    
                    # Update student profile
                    student = student_form.save()
                    
                    messages.success(request, f'Student {user.get_full_name()} updated successfully!')
                    return redirect('student_detail', registration_number=registration_number)
                    
            except Exception as e:
                messages.error(request, f'Error updating student: {str(e)}')
        else:
            # Add form errors to messages
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            for field, errors in student_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        user_form = UserForm(instance=user, is_update=True)
        student_form = StudentForm(instance=student)
    
    # Get data for form dropdowns
    programmes = Programme.objects.filter(is_active=True).order_by('name')
    schools = School.objects.filter(is_active=True).order_by('name')
    
    context = {
        'user_form': user_form,
        'student_form': student_form,
        'student': student,
        'action': 'Update',
        'programmes': programmes,
        'schools': schools,
        'status_choices': Student.STATUS_CHOICES,
        'admission_type_choices': Student.ADMISSION_TYPES,
        'sponsor_type_choices': Student.SPONSOR_TYPES,
        'gender_choices': User.GENDER_CHOICES,
    }
    
    return render(request, 'admin/students/student_form.html', context)


@login_required
@require_http_methods(["POST"])
def student_delete(request, registration_number):
    """
    Delete a student record
    """
    student = get_object_or_404(Student, registration_number=registration_number)
    
    try:
        student_name = student.user.get_full_name()
        student_reg_number = student.registration_number
        
        # Delete the user account (this will cascade to delete student record)
        with transaction.atomic():
            student.user.delete()
        
        messages.success(request, f'Student {student_name} ({student_reg_number}) has been deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting student: {str(e)}')
    
    return redirect('student_list')


@login_required
def student_performance(request, registration_number):
    """View specific student performance with all academic records"""
    
    # Get the student
    student = get_object_or_404(Student, registration_number=registration_number)
    
    # Get all enrollments for this student
    enrollments = Enrollment.objects.filter(
        student=student
    ).select_related(
        'unit', 'semester', 'semester__academic_year'
    ).prefetch_related('grade').order_by(
        'semester__academic_year__start_date', 'semester__semester_number'
    )
    
    # Organize data by academic year and semester
    academic_data = []
    
    current_year = None
    current_semester = None
    year_data = None
    semester_data = None
    
    overall_stats = {
        'total_subjects': 0,
        'passed_subjects': 0,
        'failed_subjects': 0,
        'total_credits': 0,
        'earned_credits': 0,
        'overall_gpa': 0,
        'total_grade_points': 0
    }
    
    for enrollment in enrollments:
        academic_year = enrollment.semester.academic_year
        semester = enrollment.semester
        
        # Create new year data if needed
        if current_year != academic_year:
            if year_data:
                academic_data.append(year_data)
            year_data = {
                'academic_year': academic_year,
                'semesters': []
            }
            current_year = academic_year
            current_semester = None
        
        # Create new semester data if needed
        if current_semester != semester:
            if semester_data:
                # Calculate semester statistics
                total_subjects = len(semester_data['subjects'])
                passed_subjects = sum(1 for s in semester_data['subjects'] if s['is_passed'])
                failed_subjects = total_subjects - passed_subjects
                
                total_credits = sum(s['subject'].credit_hours for s in semester_data['subjects'])
                earned_credits = sum(s['subject'].credit_hours for s in semester_data['subjects'] if s['is_passed'])
                
                # Calculate GPA for semester
                total_grade_points = sum(
                    (s['grade_points'] or 0) * s['subject'].credit_hours 
                    for s in semester_data['subjects'] if s['grade_points'] is not None
                )
                semester_gpa = total_grade_points / total_credits if total_credits > 0 else 0
                
                semester_data['stats'] = {
                    'total_subjects': total_subjects,
                    'passed_subjects': passed_subjects,
                    'failed_subjects': failed_subjects,
                    'total_credits': total_credits,
                    'earned_credits': earned_credits,
                    'semester_gpa': round(semester_gpa, 2),
                    'total_grade_points': total_grade_points
                }
                
                year_data['semesters'].append(semester_data)
            
            semester_data = {
                'semester': semester,
                'subjects': [],
                'stats': {}
            }
            current_semester = semester
        
        # Get grade information
        grade_info = {
            'enrollment': enrollment,
            'subject': enrollment.unit,
            'theory_marks': None,
            'practical_marks': None,
            'clinical_marks': None,
            'continuous_assessment': None,
            'final_exam_marks': None,
            'total_marks': None,
            'grade': None,
            'grade_points': None,
            'is_passed': False,
            'exam_date': None,
            'remarks': None
        }
        
        # Check if grade exists
        if hasattr(enrollment, 'grade'):
            grade = enrollment.grade
            grade_info.update({
                'theory_marks': grade.theory_marks,
                'practical_marks': grade.practical_marks,
                'clinical_marks': grade.clinical_marks,
                'continuous_assessment': grade.continuous_assessment,
                'final_exam_marks': grade.final_exam_marks,
                'total_marks': grade.total_marks,
                'grade': grade.grade,
                'grade_points': grade.grade_points,
                'is_passed': grade.is_passed,
                'exam_date': grade.exam_date,
                'remarks': grade.remarks
            })
        
        semester_data['subjects'].append(grade_info)
        
        # Add to overall statistics
        overall_stats['total_subjects'] += 1
        if grade_info['is_passed']:
            overall_stats['passed_subjects'] += 1
        else:
            overall_stats['failed_subjects'] += 1
        
        overall_stats['total_credits'] += enrollment.unit.credit_hours
        if grade_info['is_passed']:
            overall_stats['earned_credits'] += enrollment.unit.credit_hours
        
        if grade_info['grade_points'] is not None:
            overall_stats['total_grade_points'] += grade_info['grade_points'] * enrollment.unit.credit_hours
    
    # Don't forget the last semester and year
    if semester_data:
        # Calculate final semester statistics
        total_subjects = len(semester_data['subjects'])
        passed_subjects = sum(1 for s in semester_data['subjects'] if s['is_passed'])
        failed_subjects = total_subjects - passed_subjects
        
        total_credits = sum(s['subject'].credit_hours for s in semester_data['subjects'])
        earned_credits = sum(s['subject'].credit_hours for s in semester_data['subjects'] if s['is_passed'])
        
        total_grade_points = sum(
            (s['grade_points'] or 0) * s['subject'].credit_hours 
            for s in semester_data['subjects'] if s['grade_points'] is not None
        )
        semester_gpa = total_grade_points / total_credits if total_credits > 0 else 0
        
        semester_data['stats'] = {
            'total_subjects': total_subjects,
            'passed_subjects': passed_subjects,
            'failed_subjects': failed_subjects,
            'total_credits': total_credits,
            'earned_credits': earned_credits,
            'semester_gpa': round(semester_gpa, 2),
            'total_grade_points': total_grade_points
        }
        
        year_data['semesters'].append(semester_data)
    
    if year_data:
        academic_data.append(year_data)
    
    # Calculate overall GPA
    if overall_stats['total_credits'] > 0:
        overall_stats['overall_gpa'] = round(
            overall_stats['total_grade_points'] / overall_stats['total_credits'], 2
        )
    
    # Calculate completion percentage
    overall_stats['completion_percentage'] = round(
        (overall_stats['earned_credits'] / overall_stats['total_credits']) * 100, 2
    ) if overall_stats['total_credits'] > 0 else 0
    
    context = {
        'student': student,
        'academic_data': academic_data,
        'overall_stats': overall_stats,
        'programme': student.programme,
        'school': student.programme.school,
    }
    
    return render(request, 'admin/students/student_performance.html', context)


# AJAX view for dynamic filtering (optional)
@login_required
def get_programmes_by_school(request):
    """
    AJAX view to get programmes filtered by school
    """
    school_id = request.GET.get('school_id')
    programmes = Programme.objects.filter(
        school_id=school_id, is_active=True
    ).values('id', 'name', 'code').order_by('name')
    
    return JsonResponse(list(programmes), safe=False)

#marks entry 
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction
from django.forms import modelformset_factory
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect  # Added redirect import
from django.contrib.auth.decorators import login_required
from .models import Student, Unit, Enrollment, Grade, Semester, AcademicYear
from datetime import datetime
import json

def calculate_grade_and_points(total_marks):
    """
    Calculate grade, grade points, and pass status based on total marks
    """
    if total_marks is None or total_marks == 0:
        return '', 0.0, False
    
    if total_marks >= 90:
        return 'A+', 4.0, True
    elif total_marks >= 80:
        return 'A', 4.0, True
    elif total_marks >= 70:
        return 'B+', 3.5, True
    elif total_marks >= 60:
        return 'B', 3.0, True
    elif total_marks >= 50:
        return 'C+', 2.5, True
    elif total_marks >= 40:
        return 'C', 2.0, True
    elif total_marks >= 30:
        return 'D', 1.0, False
    else:
        return 'F', 0.0, False

def calculate_total_marks(theory_marks, practical_marks, clinical_marks, continuous_assessment, final_exam_marks):
    """
    Calculate total marks based on the same logic as JavaScript
    """
    # Collect component marks (theory, practical, clinical)
    component_marks = []
    
    if theory_marks is not None:
        component_marks.append(theory_marks)
    if practical_marks is not None:
        component_marks.append(practical_marks)
    if clinical_marks is not None:
        component_marks.append(clinical_marks)
    
    ca = continuous_assessment if continuous_assessment is not None else 0
    final_exam = final_exam_marks if final_exam_marks is not None else 0
    
    # Calculate total
    total = 0
    
    # If we have component marks, calculate their average and add CA
    if component_marks:
        component_average = sum(component_marks) / len(component_marks)
        total = component_average + ca
    else:
        # If no component marks, just use CA
        total = ca
    
    # Final exam mark is the same as total (not added to it)
    if final_exam > 0:
        total = final_exam
    
    return round(total, 2) if total > 0 else 0

@login_required
def admin_marks_entry(request, registration_number=None):
    # Check if user is admin
    if request.user.user_type != 'admin':
        return HttpResponseForbidden("Access denied. Admins only.")
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    if not current_academic_year or not current_semester:
        messages.error(request, "Please set current academic year and semester first.")
        return render(request, 'admin/admin_marks_entry.html', {'error': 'No current academic year/semester set'})
    
    student = None
    enrollments = []
    grades_data = {}
    
    # Handle student search - check both GET parameter and URL parameter
    search_registration_number = registration_number or request.GET.get('registration_number')
    
    if search_registration_number:
        try:
            student = Student.objects.get(registration_number=search_registration_number, status='active')
            
            # Get enrollments for current semester
            enrollments = Enrollment.objects.filter(
                student=student,
                semester=current_semester,
                is_active=True
            ).select_related('unit').order_by('unit__code')
            
            # Get existing grades
            for enrollment in enrollments:
                try:
                    grade = Grade.objects.get(enrollment=enrollment)
                    grades_data[enrollment.id] = {
                        'theory_marks': float(grade.theory_marks) if grade.theory_marks else None,
                        'practical_marks': float(grade.practical_marks) if grade.practical_marks else None,
                        'clinical_marks': float(grade.clinical_marks) if grade.clinical_marks else None,
                        'continuous_assessment': float(grade.continuous_assessment) if grade.continuous_assessment else None,
                        'final_exam_marks': float(grade.final_exam_marks) if grade.final_exam_marks else None,
                        'total_marks': float(grade.total_marks) if grade.total_marks else None,
                        'grade': grade.grade,
                        'grade_points': float(grade.grade_points) if grade.grade_points else None,
                        'is_passed': grade.is_passed,
                        'exam_date': grade.exam_date.strftime('%Y-%m-%d') if grade.exam_date else '',
                        'remarks': grade.remarks or ''
                    }
                except Grade.DoesNotExist:
                    grades_data[enrollment.id] = {
                        'theory_marks': None,
                        'practical_marks': None,
                        'clinical_marks': None,
                        'continuous_assessment': None,
                        'final_exam_marks': None,
                        'total_marks': None,
                        'grade': '',
                        'grade_points': None,
                        'is_passed': False,
                        'exam_date': '',
                        'remarks': ''
                    }
            
        except Student.DoesNotExist:
            messages.error(request, f"Student with registration number '{search_registration_number}' not found or not active.")
    
    # Handle marks submission
    if request.method == 'POST' and 'save_marks' in request.POST:
        registration_number = request.POST.get('registration_number')
        if not registration_number:
            messages.error(request, "Student registration number is required.")
            return render(request, 'admin/admin_marks_entry.html', {})
        
        try:
            student = Student.objects.get(registration_number=registration_number, status='active')
            enrollments = Enrollment.objects.filter(
                student=student,
                semester=current_semester,
                is_active=True
            ).select_related('unit')
            
            saved_count = 0
            
            with transaction.atomic():
                for enrollment in enrollments:
                    enrollment_id = str(enrollment.id)
                    
                    # Get form data
                    theory_marks = request.POST.get(f'theory_marks_{enrollment_id}')
                    practical_marks = request.POST.get(f'practical_marks_{enrollment_id}')
                    clinical_marks = request.POST.get(f'clinical_marks_{enrollment_id}')
                    continuous_assessment = request.POST.get(f'continuous_assessment_{enrollment_id}')
                    final_exam_marks = request.POST.get(f'final_exam_marks_{enrollment_id}')
                    exam_date = request.POST.get(f'exam_date_{enrollment_id}')
                    remarks = request.POST.get(f'remarks_{enrollment_id}')
                    
                    # Convert to appropriate types with proper validation
                    def safe_float(value):
                        if value and value.strip():
                            try:
                                return float(value)
                            except ValueError:
                                return None
                        return None
                    
                    theory_marks = safe_float(theory_marks)
                    practical_marks = safe_float(practical_marks)
                    clinical_marks = safe_float(clinical_marks)
                    continuous_assessment = safe_float(continuous_assessment)
                    final_exam_marks = safe_float(final_exam_marks)
                    
                    # Validate mark ranges
                    def validate_mark_range(mark, max_value, field_name):
                        if mark is not None and (mark < 0 or mark > max_value):
                            raise ValidationError(f"{field_name} must be between 0 and {max_value}")
                    
                    try:
                        validate_mark_range(theory_marks, 100, "Theory marks")
                        validate_mark_range(practical_marks, 100, "Practical marks")
                        validate_mark_range(clinical_marks, 100, "Clinical marks")
                        validate_mark_range(continuous_assessment, 30, "Continuous Assessment")
                        validate_mark_range(final_exam_marks, 100, "Final exam marks")
                    except ValidationError as e:
                        messages.error(request, f"Validation error for unit {enrollment.unit.code}: {str(e)}")
                        continue
                    
                    # Handle exam date
                    exam_date_obj = None
                    if exam_date and exam_date.strip():
                        try:
                            exam_date_obj = datetime.strptime(exam_date, '%Y-%m-%d').date()
                        except ValueError:
                            pass  # Invalid date format, keep as None
                    
                    remarks = remarks.strip() if remarks else ''
                    
                    # Check if at least one mark is provided
                    has_marks = any([
                        theory_marks is not None,
                        practical_marks is not None,
                        clinical_marks is not None,
                        continuous_assessment is not None,
                        final_exam_marks is not None
                    ])
                    
                    if has_marks:
                        # Calculate total marks
                        total_marks = calculate_total_marks(
                            theory_marks, practical_marks, clinical_marks, 
                            continuous_assessment, final_exam_marks
                        )
                        
                        # Calculate grade, grade points, and pass status
                        grade, grade_points, is_passed = calculate_grade_and_points(total_marks)
                        
                        # Create or update grade
                        grade_obj, created = Grade.objects.get_or_create(
                            enrollment=enrollment,
                            defaults={
                                'theory_marks': theory_marks,
                                'practical_marks': practical_marks,
                                'clinical_marks': clinical_marks,
                                'continuous_assessment': continuous_assessment,
                                'final_exam_marks': final_exam_marks,
                                'total_marks': total_marks,
                                'grade': grade,
                                'grade_points': grade_points,
                                'is_passed': is_passed,
                                'exam_date': exam_date_obj,
                                'remarks': remarks
                            }
                        )
                        
                        if not created:
                            # Update existing grade
                            grade_obj.theory_marks = theory_marks
                            grade_obj.practical_marks = practical_marks
                            grade_obj.clinical_marks = clinical_marks
                            grade_obj.continuous_assessment = continuous_assessment
                            grade_obj.final_exam_marks = final_exam_marks
                            grade_obj.total_marks = total_marks
                            grade_obj.grade = grade
                            grade_obj.grade_points = grade_points
                            grade_obj.is_passed = is_passed
                            grade_obj.exam_date = exam_date_obj
                            grade_obj.remarks = remarks
                            grade_obj.save()
                        
                        saved_count += 1
                
                if saved_count > 0:
                    messages.success(request, f"Marks saved successfully for {saved_count} units for student {student.registration_number}")
                    # Redirect to student performance page after successful save
                    return redirect('student_performance', registration_number=registration_number)
                else:
                    messages.warning(request, "No marks were provided to save.")
                
        except Student.DoesNotExist:
            messages.error(request, f"Student with registration number '{registration_number}' not found.")
        except Exception as e:
            messages.error(request, f"Error saving marks: {str(e)}")
            # For debugging - remove in production
            import traceback
            print(traceback.format_exc())
    
    # Get all active students for dropdown
    all_students = Student.objects.filter(status='active').select_related('user', 'programme').order_by('registration_number')
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'grades_data': grades_data,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'all_students': all_students,
    }
    
    return render(request, 'admin/admin_marks_entry.html', context)

@login_required
def get_student_info(request):
    """AJAX endpoint to get student information"""
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    registration_number = request.GET.get('registration_number')
    if not registration_number:
        return JsonResponse({'error': 'Student registration number required'}, status=400)
    
    try:
        student = Student.objects.get(registration_number=registration_number, status='active')
        current_semester = Semester.objects.filter(is_current=True).first()
        
        enrollments = Enrollment.objects.filter(
            student=student,
            semester=current_semester,
            is_active=True
        ).select_related('unit')
        
        data = {
            'student': {
                'registration_number': student.registration_number,
                'name': student.user.get_full_name(),
                'programme': student.programme.name,
                'programme_code': student.programme.code,
                'current_year': student.current_year,
                'current_semester': student.current_semester,
                'school': student.programme.school.name,
            },
            'enrollments': [
                {
                    'id': enrollment.id,
                    'unit_code': enrollment.unit.code,
                    'unit_name': enrollment.unit.name,
                    'credit_hours': enrollment.unit.credit_hours,
                    'theory_hours': enrollment.unit.theory_hours,
                    'practical_hours': enrollment.unit.practical_hours,
                    'clinical_hours': enrollment.unit.clinical_hours,
                    'unit_type': enrollment.unit.get_unit_type_display(),
                }
                for enrollment in enrollments
            ]
        }
        
        return JsonResponse(data)
        
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)
    
#instructure management

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from .models import Instructor, School, User
from .forms import InstructorForm, UserForm  # You'll need to create these forms

User = get_user_model()

@login_required
def instructor_list(request):
    """Display list of all instructors with search and filtering"""
    instructors = Instructor.objects.select_related('user', 'school').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        instructors = instructors.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(employee_number__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(designation__icontains=search_query) |
            Q(school__name__icontains=search_query)
        )
    
    # Filter by school
    school_filter = request.GET.get('school', '')
    if school_filter:
        instructors = instructors.filter(school_id=school_filter)
    
    # Filter by designation
    designation_filter = request.GET.get('designation', '')
    if designation_filter:
        instructors = instructors.filter(designation=designation_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        instructors = instructors.filter(is_active=True)
    elif status_filter == 'inactive':
        instructors = instructors.filter(is_active=False)
    
    # Ordering
    order_by = request.GET.get('order_by', 'user__first_name')
    if order_by in ['user__first_name', 'user__last_name', 'employee_number', 'designation', 'joining_date', 'school__name']:
        instructors = instructors.order_by(order_by)
    
    # Pagination
    paginator = Paginator(instructors, 20)  # Show 20 instructors per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all schools for filter dropdown
    schools = School.objects.filter(is_active=True).order_by('name')
    
    # Get designation choices for filter
    designation_choices = Instructor.DESIGNATION_CHOICES
    
    context = {
        'page_obj': page_obj,
        'instructors': page_obj,
        'search_query': search_query,
        'schools': schools,
        'designation_choices': designation_choices,
        'school_filter': school_filter,
        'designation_filter': designation_filter,
        'status_filter': status_filter,
        'order_by': order_by,
        'total_instructors': instructors.count(),
    }
    
    return render(request, 'instructors/instructor_list.html', context)


@login_required
def instructor_detail(request, employee_number):
    """Display detailed view of a specific instructor"""
    instructor = get_object_or_404(
        Instructor.objects.select_related('user', 'school'),
        employee_number=employee_number
    )
    
    # You can add additional context here like:
    # - Current teaching assignments
    # - Student evaluations
    # - Performance metrics
    # - etc.
    
    context = {
        'faculty': instructor,  # Using 'faculty' to match your template
        'instructor': instructor,
        # Add other context as needed
    }
    
    return render(request, 'instructors/instructor_detail.html', context)


@login_required
def instructor_create(request):
    """Create a new instructor"""
    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES)
        instructor_form = InstructorForm(request.POST)
        
        if user_form.is_valid() and instructor_form.is_valid():
            # Create user first
            user = user_form.save(commit=False)
            user.user_type = 'instructor'  # Set user type
            user.save()
            
            # Create instructor profile
            instructor = instructor_form.save(commit=False)
            instructor.user = user
            instructor.save()
            
            messages.success(request, f'Instructor {user.get_full_name()} created successfully!')
            return redirect('instructor_detail', employee_number=instructor.employee_number)
    else:
        user_form = UserForm()
        instructor_form = InstructorForm()
    
    context = {
        'user_form': user_form,
        'instructor_form': instructor_form,
        'is_create': True,
    }
    
    return render(request, 'instructors/instructor_form.html', context)


@login_required
def instructor_update(request, employee_number):
    """Update an existing instructor"""
    instructor = get_object_or_404(Instructor, employee_number=employee_number)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES, instance=instructor.user)
        instructor_form = InstructorForm(request.POST, instance=instructor)
        
        if user_form.is_valid() and instructor_form.is_valid():
            user_form.save()
            instructor_form.save()
            
            messages.success(request, f'Instructor {instructor.user.get_full_name()} updated successfully!')
            return redirect('instructor_detail', employee_number=instructor.employee_number)
    else:
        user_form = UserForm(instance=instructor.user)
        instructor_form = InstructorForm(instance=instructor)
    
    context = {
        'user_form': user_form,
        'instructor_form': instructor_form,
        'instructor': instructor,
        'is_create': False,
    }
    
    return render(request, 'instructors/instructor_form.html', context)


@login_required
def instructor_delete(request, employee_number):
    """Delete an instructor"""
    instructor = get_object_or_404(Instructor, employee_number=employee_number)
    
    if request.method == 'POST':
        instructor_name = instructor.user.get_full_name()
        
        # Delete the user (this will cascade delete the instructor due to OneToOneField)
        instructor.user.delete()
        
        messages.success(request, f'Instructor {instructor_name} deleted successfully!')
        return redirect('instructor_list')
    
    # If it's a GET request, show confirmation page
    context = {
        'instructor': instructor,
        'faculty': instructor,  # For template compatibility
    }
    
    return render(request, 'instructors/instructor_confirm_delete.html', context)


@login_required
def instructor_toggle_status(request, employee_number):
    """Toggle instructor active/inactive status via AJAX"""
    if request.method == 'POST':
        instructor = get_object_or_404(Instructor, employee_number=employee_number)
        instructor.is_active = not instructor.is_active
        instructor.save()
        
        # Also update user status
        instructor.user.is_active = instructor.is_active
        instructor.user.save()
        
        return JsonResponse({
            'status': 'success',
            'is_active': instructor.is_active,
            'message': f'Instructor status updated to {"Active" if instructor.is_active else "Inactive"}'
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
def instructor_search_api(request):
    """API endpoint for instructor search (for AJAX autocomplete)"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    instructors = Instructor.objects.filter(
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(employee_number__icontains=query)
    ).select_related('user', 'school')[:10]
    
    results = []
    for instructor in instructors:
        results.append({
            'id': instructor.employee_number,
            'text': f"{instructor.user.get_full_name()} ({instructor.employee_number})",
            'designation': instructor.get_designation_display(),
            'school': instructor.school.name,
        })
    
    return JsonResponse({'results': results})


# Additional utility views

@login_required
def instructor_export(request):
    """Export instructors data to CSV/Excel"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="instructors.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Employee Number', 'Full Name', 'Email', 'Phone', 'School', 
        'Designation', 'Employment Type', 'Joining Date', 'Status'
    ])
    
    instructors = Instructor.objects.select_related('user', 'school').all()
    
    for instructor in instructors:
        writer.writerow([
            instructor.employee_number,
            instructor.user.get_full_name(),
            instructor.user.email or '',
            instructor.user.phone or '',
            instructor.school.name,
            instructor.get_designation_display(),
            instructor.get_employment_type_display(),
            instructor.joining_date.strftime('%Y-%m-%d'),
            'Active' if instructor.is_active else 'Inactive'
        ])
    
    return response


@login_required
def instructor_bulk_action(request):
    """Handle bulk actions on multiple instructors"""
    if request.method == 'POST':
        action = request.POST.get('action')
        instructor_ids = request.POST.getlist('instructor_ids')
        
        if not instructor_ids:
            messages.error(request, 'No instructors selected.')
            return redirect('instructor_list')
        
        instructors = Instructor.objects.filter(employee_number__in=instructor_ids)
        
        if action == 'activate':
            instructors.update(is_active=True)
            User.objects.filter(instructor_profile__in=instructors).update(is_active=True)
            messages.success(request, f'{instructors.count()} instructors activated.')
            
        elif action == 'deactivate':
            instructors.update(is_active=False)
            User.objects.filter(instructor_profile__in=instructors).update(is_active=False)
            messages.success(request, f'{instructors.count()} instructors deactivated.')
            
        elif action == 'delete':
            count = instructors.count()
            # Delete users (this will cascade delete instructors)
            User.objects.filter(instructor_profile__in=instructors).delete()
            messages.success(request, f'{count} instructors deleted.')
    
    return redirect('instructor_list')

#departments
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import School, User
from .forms import SchoolForm

def school_list(request):
    schools = School.objects.all().order_by('name')
    context = {
        'schools': schools,
        'is_create': False
    }
    return render(request, 'school/school_list.html', context)

def school_create(request):
    if request.method == 'POST':
        form = SchoolForm(request.POST)
        if form.is_valid():
            school = form.save()
            messages.success(request, f'School "{school.name}" created successfully!')
            return redirect('school_detail', pk=school.pk)
    else:
        form = SchoolForm()
    
    context = {
        'form': form,
        'is_create': True
    }
    return render(request, 'school/school_form.html', context)

def school_detail(request, pk):
    school = get_object_or_404(School, pk=pk)
    context = {
        'school': school
    }
    return render(request, 'school/school_detail.html', context)

def school_edit(request, pk):
    school = get_object_or_404(School, pk=pk)
    if request.method == 'POST':
        form = SchoolForm(request.POST, instance=school)
        if form.is_valid():
            updated_school = form.save()
            messages.success(request, f'School "{updated_school.name}" updated successfully!')
            return redirect('school_detail', pk=school.pk)
    else:
        form = SchoolForm(instance=school)
    
    context = {
        'form': form,
        'school': school,
        'is_create': False
    }
    return render(request, 'school/school_form.html', context)