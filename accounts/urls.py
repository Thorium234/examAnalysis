from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'accounts'
urlpatterns = [
    # Multi-step Authentication Flow
    path('find-account/', views.FindAccountView.as_view(), name='find_account'),
    path('account-found/', views.AccountFoundView.as_view(), name='account_found'),
    path('goodbye/', views.GoodbyeView.as_view(), name='goodbye'),

    # Legacy login (for backward compatibility)
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),

    # Profile Management
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),

    # Password Reset
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # Teacher Dashboard and Management
    path('dashboard/', views.TeacherDashboardView.as_view(), name='teacher_dashboard'),

    path('profile/create/', views.ProfileCreateView.as_view(), name='profile_create'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile_update'),

    path('teacher-class/create/', views.TeacherClassCreateView.as_view(), name='teacher_class_create'),
    path('teacher-class/<int:pk>/update/', views.TeacherClassUpdateView.as_view(), name='teacher_class_update'),
    path('teacher-class/<int:pk>/delete/', views.TeacherClassDeleteView.as_view(), name='teacher_class_delete'),

    # Student Authentication and Dashboard
    path('student-login/', views.StudentLoginView.as_view(), name='student_login'),
    path('student-dashboard/', views.StudentDashboardView.as_view(), name='student_dashboard'),
]