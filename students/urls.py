from django.urls import path
from .views import (
    StudentListView,
    StudentCreateView,
    StudentUpdateView,
    StudentDeleteView,
    StudentSubjectEnrollmentView,
    StudentAdvancementCreateView,
)

app_name = 'students'

urlpatterns = [
    # Student CRUD URLs
    path('', StudentListView.as_view(), name='student_list'),
    path('create/', StudentCreateView.as_view(), name='create_student'),
    path('<int:pk>/update/', StudentUpdateView.as_view(), name='update_student'),
    path('<int:pk>/delete/', StudentDeleteView.as_view(), name='delete_student'),

    # Student enrollment and advancement URLs
    path('<int:pk>/enroll/', StudentSubjectEnrollmentView.as_view(), name='enroll_student'),
    path('advancement/create/', StudentAdvancementCreateView.as_view(), name='create_advancement'),
]
