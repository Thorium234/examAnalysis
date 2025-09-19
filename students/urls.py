from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('students/', views.student_list, name='student_list'),
    path('students/<str:admission_number>/', views.student_detail, name='student_detail'),
    path('merit-list/<int:exam_id>/', views.merit_list, name='merit_list'),
]