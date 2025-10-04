from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('settings/create/', views.ReportSettingsCreateView.as_view(), name='report_settings_create'),
    path('settings/update/', views.ReportSettingsUpdateView.as_view(), name='report_settings_update'),
]
