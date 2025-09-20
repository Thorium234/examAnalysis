from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    path('', views.exam_list, name='exam_list'),
    path('create/', views.ExamCreateView.as_view(), name='exam_create'),
    path('<int:pk>/edit/', views.ExamUpdateView.as_view(), name='exam_update'),
    path('<int:pk>/delete/', views.ExamDeleteView.as_view(), name='exam_delete'),
    path('<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('<int:exam_id>/results/', views.exam_results, name='exam_results'),
    path('<int:exam_id>/upload-results/', views.upload_results, name='upload_results'),
    path('<int:exam_id>/add-result/', views.add_result, name='add_result'),
    path('<int:exam_id>/result/<int:result_id>/edit/', views.edit_result, name='edit_result'),
    path('<int:exam_id>/download/', views.download_results, name='download_results'),
    path('<int:exam_id>/subject-analysis/', views.subject_analysis, name='subject_analysis'),

    path('exams/<int:exam_id>/enter-results/', views.enter_results, name='enter_results'),
]