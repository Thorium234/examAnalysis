from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static # Import the static function
from django.shortcuts import redirect

def root_redirect(request):
    """Redirect root URL based on authentication status"""
    if request.user.is_authenticated:
        # Check if user is a student
        if hasattr(request.user, 'profile') and request.user.profile.roles.filter(name='Student').exists():
            return redirect('accounts:student_dashboard')
        else:
            return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        return redirect('login_selection')

urlpatterns = [
    # Admin URL
    path('admin/', admin.site.urls),

    # Root URL redirect to login selection
    path('', root_redirect, name='root'),
    path('login-selection/', lambda request: redirect('accounts:find_account'), name='login_selection'),

    # App-specific URLs
    path('accounts/', include('accounts.urls')),
    path('students/', include('students.urls')),
    path('exams/', include('exams.urls')),
    path('subjects/', include('subjects.urls')), # New: Added subjects URL
    path('school/', include('school.urls')),     # New: Added school URL
    path('reports/', include('reports.urls')),   # New: Added reports URL
]

# Only serve media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)