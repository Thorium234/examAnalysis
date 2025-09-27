from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static # Import the static function
from django.shortcuts import redirect

def root_redirect(request):
    """Redirect root URL to find account page"""
    return redirect('accounts:find_account')

urlpatterns = [
    # Admin URL
    path('admin/', admin.site.urls),

    # Root URL redirect to find account
    path('', root_redirect, name='root'),

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