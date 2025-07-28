from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Student authentication
    path('', views.student_login, name='student_login'),
    path('logout/', views.student_logout, name='student_logout'),
    
    # Student dashboard and main views
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('units/', views.student_units_view, name='student_units'),
    path('profile/', views.student_profile, name='student_profile'),
    path('reporting/', views.student_reporting, name='student_reporting'),

    # Main hostel booking flow
    path('hostel/check-eligibility/', views.hostel_booking_eligibility, name='hostel_booking_eligibility'),
    path('hostel/list/', views.hostel_list, name='hostel_list'),
    path('hostel/<int:hostel_id>/rooms/', views.room_list, name='room_list'),
    path('room/<int:room_id>/beds/', views.bed_list, name='bed_list'),
    path('bed/<int:bed_id>/book/', views.book_bed, name='book_bed'),
    
    # Booking management
    path('booking/<int:booking_id>/', views.hostel_booking_detail, name='hostel_booking_detail'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    
    # AJAX endpoints
    path('ajax/rooms/', views.get_rooms_ajax, name='get_rooms_ajax'),
    path('ajax/beds/', views.get_beds_ajax, name='get_beds_ajax'),

    # Admin authentication URLs
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('students/', views.student_list, name='student_list'),
    path('students/create/', views.student_create, name='student_create'),
    path('students/<str:registration_number>/', views.student_detail, name='student_detail'),
    path('students/<str:registration_number>/update/', views.student_update, name='student_update'),
    path('students/<str:registration_number>/delete/', views.student_delete, name='student_delete'),
    path('students/<str:registration_number>/performance/', views.student_performance, name='student_performance'),
    path('api/programmes-by-school/', views.get_programmes_by_school, name='get_programmes_by_school'),

    path('admin-marks-entry/', views.admin_marks_entry, name='admin_marks_entry'),
    path('admin-student-info/', views.get_student_info, name='get_student_info'),

    # Main instructor views
    path('instructors/', views.instructor_list, name='instructor_list'),
    path('instructors/create/', views.instructor_create, name='instructor_create'),
    path('instructors/<str:employee_number>/', views.instructor_detail, name='instructor_detail'),
    path('instructors/<str:employee_number>/edit/', views.instructor_update, name='instructor_update'),
    path('instructors/<str:employee_number>/delete/', views.instructor_delete, name='instructor_delete'),

    # AJAX and API endpoints
    path('api/instructors/toggle-status/<str:employee_number>/', views.instructor_toggle_status, name='instructor_toggle_status'),
    path('api/instructors/search/', views.instructor_search_api, name='instructor_search_api'),
    path('instructors/bulk/action/', views.instructor_bulk_action, name='instructor_bulk_action'),
    path('instructors/export/csv/', views.instructor_export, name='instructor_export'),

    path('schools/', views.school_list, name='school_list'),
    path('schools/add/', views.school_create, name='school_create'),
    path('schools/<int:pk>/', views.school_detail, name='school_detail'),
    path('schools/<int:pk>/edit/', views.school_edit, name='school_edit'),

    #students transcript
    path('student/transcript/', views.student_transcript, name='student_transcript'),
    path('student-download-transcript', views.student_transcript_pdf , name='student_transcript_pdf'),
    
]
