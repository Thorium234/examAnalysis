# reports/admin.py
from django.contrib import admin
from .models import ReportSettings

class ReportSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'school',
        'show_report_cover',
        'show_subject_grades',
        'show_overall_rank',
        'show_school_fees_layout',
    )
    list_filter = ('school',)
    search_fields = ('school__name',)
    
admin.site.register(ReportSettings, ReportSettingsAdmin)
