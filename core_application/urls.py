from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Student authentication
    path('', views.student_login, name='student_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='student_login'), name='student_logout'),
    
    # Student dashboard and main views
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('profile/', views.student_profile, name='student_profile'),
    path('available-units/', views.available_units, name='available_units'),
    path('enroll/<int:unit_id>/', views.enroll_unit, name='enroll_unit'),
]