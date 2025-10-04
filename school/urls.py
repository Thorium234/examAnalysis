# Location: exam_system/school/urls.py

from django.urls import path
from . import views
from exams.views import GradingSystemListView

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

    # New Dashboard URLs
    path('class/<int:form_level>/', views.class_dashboard, name='class_dashboard'),
    path('class/<int:form_level>/<str:stream>/students/', views.stream_students, name='stream_students'),
    path('stream/<int:form_level>/<str:stream>/', views.stream_dashboard, name='stream_dashboard'),
    path('subject/<int:subject_id>/', views.subject_dashboard, name='subject_dashboard'),
    path('subject/<int:form_level>/<int:subject_id>/', views.subject_dashboard, name='subject_dashboard_form'),
    path('subject/<int:form_level>/<str:stream>/<int:subject_id>/', views.subject_dashboard, name='subject_dashboard_stream'),
    path('subject/<int:form_level>/<str:stream>/<int:subject_id>/entry/', views.subject_entry, name='subject_entry'),
    path('school-wide/', views.school_wide_dashboard, name='school_wide_dashboard'),
    path('departments/', views.departments_dashboard, name='departments_dashboard'),
    path('department/<int:category_id>/subjects/', views.category_subjects, name='category_subjects'),
    path('subject/<int:subject_id>/teachers/', views.subject_teachers, name='subject_teachers'),
    path('subject/<int:subject_id>/teachers/add/', views.add_teacher_to_subject, name='add_teacher_to_subject'),
    path('subject/<int:subject_id>/teachers/<int:teacher_id>/remove/', views.remove_teacher_from_subject, name='remove_teacher_from_subject'),
    # Exam Analysis URLs
    path('exam-analysis/<int:form_level>/<int:exam_id>/', views.exam_merit_list, name='exam_merit_list'),
    path('upload-exam/<int:form_level>/<int:exam_id>/<str:stream>/', views.exam_upload_subjects, name='exam_upload_subjects'),
    path('upload-exam/<int:form_level>/<int:exam_id>/<str:stream>/<int:category_id>/', views.exam_upload_individual, name='exam_upload_individual'),
    path('upload-exam/<int:form_level>/<int:exam_id>/', views.exam_upload_streams, name='exam_upload_streams'),
    path('student-report-card/<int:form_level>/', views.form_report_card, name='form_report_card'),
    path('student-report-card/<int:form_level>/', views.form_report_card, name='form_report_card'),
    path('student-report-card/<int:form_level>/pdf/', views.generate_form_report_pdf, name='generate_form_report_pdf'),
    path('student-report-card/<int:form_level>/<str:stream>/pdf/', views.generate_stream_report_pdf, name='generate_stream_report_pdf'),

    # Upload Exam URLs
    path('upload-exam/<int:form_level>/', views.form_upload_exam, name='form_upload_exam'),
    # Student Report Card URLs
    path('student-report-card/', views.student_report_card, name='student_report_card'),

    # Upload Exam URLs
    path('upload-exam/', views.upload_exam, name='upload_exam'),
    path('exam-analysis/<int:form_level>/', views.exam_form_analysis, name='exam_form_analysis'),
    path('grading-systems/', GradingSystemListView.as_view(), name='gradingsystem_list'),
    path('teacher/<int:teacher_id>/', views.teacher_detail, name='teacher_detail'),
]