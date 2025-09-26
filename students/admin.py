from django.contrib import admin
from .models import Student, StudentAdvancement

# Inline to allow managing StudentAdvancement records from the Student admin page
class StudentAdvancementInline(admin.StackedInline):
    model = StudentAdvancement
    extra = 1
    fieldsets = (
        (None, {
            'fields': (('from_form_level', 'to_form_level'), 'advancement_year')
        }),
    )
    readonly_fields = ('timestamp',)

class StudentAdmin(admin.ModelAdmin):
    # Fieldsets for better organization of the form
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'admission_number', 'phone_contact', 'kcpe_marks')
        }),
        ('Academic Information', {
            'fields': ('school', 'form_level', 'stream')
        }),
    )

    list_display = ('name', 'admission_number', 'school', 'form_level', 'stream', 'phone_contact', 'kcpe_marks')
    list_filter = ('school', 'form_level', 'stream')
    search_fields = ('name', 'admission_number')
    inlines = [StudentAdvancementInline,]
    # Add a filter for schools based on the current user's school
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(school=request.user.school)

class StudentAdvancementAdmin(admin.ModelAdmin):
    # Fieldsets for better organization of the form
    fieldsets = (
        (None, {
            'fields': ('student', ('from_form_level', 'to_form_level'), 'advancement_year')
        }),
    )
    list_display = ('student', 'from_form_level', 'to_form_level', 'advancement_year', 'timestamp')
    list_filter = ('school', 'advancement_year')
    search_fields = ('student__name', 'student__admission_number')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)

    # Add a filter for schools based on the current user's school
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(school=request.user.school)

admin.site.register(Student, StudentAdmin)
admin.site.register(StudentAdvancement, StudentAdvancementAdmin)
