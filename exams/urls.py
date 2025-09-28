from django.urls import path
from . import views

app_name = 'exams'
urlpatterns = [
    # New hierarchical result entry URLs
    path('results/form-levels/', views.exam_form_levels, name='exam_form_levels'),
    path('results/form/<int:form_level>/subjects/', views.exam_form_subjects, name='exam_form_subjects'),
    path('results/form/<int:form_level>/subject/<int:subject_id>/entry/', views.exam_subject_results_entry, name='exam_subject_results_entry'),
    # Exam-related URLs
    path('create/', views.ExamCreateView.as_view(), name='exam_create'),
    path('', views.ExamListView.as_view(), name='exam_list'),
    path('<int:pk>/edit/', views.ExamUpdateView.as_view(), name='exam_edit'),
    path('<int:pk>/delete/', views.ExamDeleteView.as_view(), name='exam_delete'),

    # Result-related URLs
    path('<int:pk>/results/', views.exam_results_upload_choice, name='exam_results_upload_choice'),
    path('<int:pk>/results/download-template/', views.download_exam_results_template, name='download_exam_results_template'),
    path('<int:pk>/results/upload/', views.upload_results, name='upload_results'),
    path('<int:pk>/results/summary/', views.exam_results_summary, name='exam_results_summary'),
    path('<int:exam_pk>/subject/<int:subject_pk>/results/', views.subject_results, name='subject_results'),
    path('<int:exam_pk>/stream/<int:form_level>/<str:stream>/results/', views.stream_results, name='stream_results'),
    path('<int:pk>/results/entry/', views.exam_results_entry, name='exam_results_entry'),
    # Grading System URLs
    path('grading-systems/create/', views.GradingSystemCreateView.as_view(), name='grading_system_create'),
    path('grading-systems/', views.GradingSystemListView.as_view(), name='gradingsystem_list'),
    path('grading-systems/<int:pk>/', views.GradingSystemDetailView.as_view(), name='grading_system_detail'),
    path('grading-systems/<int:pk>/edit/', views.GradingSystemUpdateView.as_view(), name='grading_system_edit'),
    path('grading-systems/<int:pk>/delete/', views.GradingSystemDeleteView.as_view(), name='grading_system_delete'),

    # Grading Range URLs
    path('grading-systems/<int:grading_system_pk>/ranges/create/', views.GradingRangeCreateView.as_view(), name='gradingrange_create'),
    path('grading-ranges/<int:pk>/edit/', views.GradingRangeUpdateView.as_view(), name='gradingrange_update'),
    path('grading-ranges/<int:pk>/delete/', views.GradingRangeDeleteView.as_view(), name='gradingrange_delete'),
]