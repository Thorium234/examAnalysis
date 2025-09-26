from django.urls import path
from . import views

app_name = 'exams'
urlpatterns = [
    # Exam-related URLs
    path('create/', views.ExamCreateView.as_view(), name='exam_create'),
    path('', views.ExamListView.as_view(), name='exam_list'),
    path('<int:pk>/edit/', views.ExamUpdateView.as_view(), name='exam_edit'),
    path('<int:pk>/delete/', views.ExamDeleteView.as_view(), name='exam_delete'),
    
    # Result-related URLs
    path('<int:pk>/results/entry/', views.exam_results_entry, name='exam_results_entry'),
    path('<int:pk>/results/upload/', views.upload_results, name='upload_results'),
    path('<int:pk>/results/template/', views.download_exam_results_template, name='download_exam_results_template'),
    path('<int:pk>/results/summary/', views.ExamResultsSummaryView.as_view(), name='exam_results_summary'),
    path('<int:pk>/results/summary/data/', views.get_exam_summary_data, name='get_exam_summary_data'),
    path('<int:exam_pk>/report/<int:student_pk>/', views.StudentReportCardView.as_view(), name='student_report_card'),
    
    # Grading-related URLs
    path('grading_systems/', views.GradingSystemListView.as_view(), name='grading_system_list'),
    path('grading_systems/create/', views.GradingSystemCreateView.as_view(), name='grading_system_create'),
    path('grading_systems/<int:pk>/', views.GradingSystemDetailView.as_view(), name='grading_system_detail'),
    path('grading_systems/<int:pk>/edit/', views.GradingSystemUpdateView.as_view(), name='grading_system_edit'),
    path('grading_systems/<int:pk>/delete/', views.GradingSystemDeleteView.as_view(), name='grading_system_delete'),
    
    path('grading_ranges/create/', views.GradingRangeCreateView.as_view(), name='grading_range_create'),
    path('grading_ranges/<int:pk>/edit/', views.GradingRangeUpdateView.as_view(), name='grading_range_edit'),
    path('grading_ranges/<int:pk>/delete/', views.GradingRangeDeleteView.as_view(), name='grading_range_delete'),
]
