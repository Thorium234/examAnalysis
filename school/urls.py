# Location: exam_system/school/urls.py

from django.urls import path
from . import views

app_name = 'school'
 
urlpatterns = [
    # Main dashboard view. This will be the landing page for authenticated users.
    # It is a function-based view, separate from the SchoolDashboardView class.
    path('', views.school_dashboard, name='school_dashboard'),

    # Principal's Control Panel
    # This path is restricted to the superuser (COE) and will be the hub for user management.
    path('principal-control/', views.principal_control, name='principal_control'),

    # Teachers' List/Dashboard
    path('teachers/', views.teacher_list, name='teacher_list'),

    # Students' List/Dashboard
    path('students/', views.student_list, name='student_list'),

    # Forms & Classes Dashboard
    path('forms/', views.forms_dashboard, name='forms_dashboard'),

    # Exam Management Dashboard
    path('exams/', views.exam_management, name='exam_management'),

    # Reports and Analysis Dashboard
    path('reports/', views.reports_and_analysis, name='reports_and_analysis'),

    # Form Level Management
    path('form-levels/', views.FormLevelListView.as_view(), name='form_level_list'),
    path('form-levels/create/', views.FormLevelCreateView.as_view(), name='form_level_create'),

    # URLs for managing the School object itself using Class-Based Views
    # We keep these for the superuser to manage the school's details (name, logo, etc.).
    path('create/', views.SchoolCreateView.as_view(), name='school_create'),
    path('<int:pk>/update/', views.SchoolUpdateView.as_view(), name='school_update'),
    path('<int:pk>/delete/', views.SchoolDeleteView.as_view(), name='school_delete'),
]
