from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    path('', views.exam_list, name='exam_list'),
    path('<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('<int:exam_id>/results/', views.exam_results, name='exam_results'),
    path('<int:exam_id>/enter-results/', views.enter_results, name='enter_results'),
]