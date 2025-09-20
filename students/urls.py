from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('students/', views.student_list, name='student_list'),
    path('students/<str:admission_number>/', views.student_detail, name='student_detail'),
    path('students/create/', views.StudentCreateView.as_view(), name='student_create'),
    path('students/<str:pk>/update/', views.StudentUpdateView.as_view(), name='student_update'),
    path('students/<str:admission_number>/subjects/', views.StudentSubjectEnrollmentView.as_view(), name='student_subjects'),
    path('merit-list/<int:exam_id>/', views.merit_list, name='merit_list'),
    path('performance/<str:admission_number>/', views.student_performance_graph, name='performance_graph'),
    path('report-card/<str:admission_number>/<int:exam_id>/', views.student_report_card, name='report_card'),
    path('bulk-advancement/', views.bulk_student_advancement, name='bulk_advancement'),
    
    # Student Advancement URLs
    path('advancement/', views.StudentAdvancementListView.as_view(), name='student-advancement-list'),
    path('advancement/create/', views.StudentAdvancementCreateView.as_view(), name='student-advancement-create'),
    path('advancement/upload/', views.StudentAdvancementBulkUploadView.as_view(), name='student-advancement-bulk-upload'),
    path('advancement/template/', views.DownloadAdvancementTemplateView.as_view(), name='student-advancement-template'),
]