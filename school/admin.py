# school/admin.py
from django.contrib import admin
from .models import School

class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'phone_number', 'email')
    search_fields = ('name', 'location')
    
admin.site.register(School, SchoolAdmin)
