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

]