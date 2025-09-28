# school/admin.py
from django.contrib import admin
from .models import School, Resource

class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'phone_number', 'email')
    search_fields = ('name', 'location')
    
admin.site.register(School, SchoolAdmin)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'school', 'resource_type', 'uploaded_by', 'uploaded_at')
    list_filter = ('school', 'resource_type', 'subject', 'form_level')
    search_fields = ('title', 'description')

admin.site.register(Resource, ResourceAdmin)
