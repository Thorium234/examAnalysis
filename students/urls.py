from django.urls import path
from . import views

urlpatterns = [
    path('', views.StudentListView.as_view(), name='student_list'),
    path('create/', views.StudentCreateView.as_view(), name='student_create'),
    path('<str:admission_number>/update/', views.StudentUpdateView.as_view(), name='student_update'),
    path('<str:admission_number>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),
    path('<str:admission_number>/subjects/', views.StudentSubjectEnrollmentView.as_view(), name='student_subjects'),
    
    # Student Advancement URLs
    path('advancement/create/', views.StudentAdvancementCreateView.as_view(), name='student_advancement_create'),
]
