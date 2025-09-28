from django.urls import path
from . import views

app_name = 'subjects'

urlpatterns = [
    path('', views.SubjectListView.as_view(), name='subject_list'),
    path('<int:pk>/', views.SubjectDetailView.as_view(), name='subject_detail'),
    path('create/', views.SubjectCreateView.as_view(), name='subject_create'),
    path('<int:pk>/update/', views.SubjectUpdateView.as_view(), name='subject_update'),
    path('<int:pk>/delete/', views.SubjectDeleteView.as_view(), name='subject_delete'),

    path('paper/create/', views.SubjectPaperCreateView.as_view(), name='subject_paper_create'),
]
