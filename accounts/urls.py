from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'accounts'
urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    # This line has been updated to use the new class-based view
    path('dashboard/', views.TeacherDashboardView.as_view(), name='teacher_dashboard'),
    
    path('profile/create/', views.ProfileCreateView.as_view(), name='profile_create'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile_update'),
    
    path('teacher-class/create/', views.TeacherClassCreateView.as_view(), name='teacher_class_create'),
    path('teacher-class/<int:pk>/update/', views.TeacherClassUpdateView.as_view(), name='teacher_class_update'),
    path('teacher-class/<int:pk>/delete/', views.TeacherClassDeleteView.as_view(), name='teacher_class_delete'),
]
