
from django.urls import path
from .views import (
    StudentListView,
    FormLevelDashboardView,
    StreamStudentListView,
    StudentCreateView,
    StudentDetailView,
    StudentUpdateView,
    StudentDeleteView,
    StudentSubjectEnrollmentView,
    StudentAdvancementCreateView,
    SubjectSelectionDashboardView,
    FormSubjectSelectionView,
    StreamSubjectSelectionView,
)

app_name = 'students'

urlpatterns = [
    # Student management hierarchy URLs
    path('', StudentListView.as_view(), name='student_list'),
    path('form/<int:form_level>/', FormLevelDashboardView.as_view(), name='form_dashboard'),
    path('form/<int:form_level>/stream/<str:stream>/', StreamStudentListView.as_view(), name='stream_students'),

    # Student CRUD URLs
    path('create/', StudentCreateView.as_view(), name='student_create'),
    path('<int:pk>/', StudentDetailView.as_view(), name='student_detail'),
    path('<int:pk>/update/', StudentUpdateView.as_view(), name='update_student'),
    path('<int:pk>/delete/', StudentDeleteView.as_view(), name='delete_student'),

    # Student enrollment and advancement URLs
    path('<int:pk>/enroll/', StudentSubjectEnrollmentView.as_view(), name='enroll_student'),
    path('advancement/create/', StudentAdvancementCreateView.as_view(), name='create_advancement'),

    # Subject selection dashboard
    path('subject-selection/', SubjectSelectionDashboardView.as_view(), name='subject_selection_dashboard'),
    path('subject-selection/<int:form_level>/', FormSubjectSelectionView.as_view(), name='form_subject_selection'),
    path('subject-selection/<int:form_level>/<str:stream>/', StreamSubjectSelectionView.as_view(), name='stream_subject_selection'),
]