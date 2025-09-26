from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Role, Profile, TeacherClass

# This is the correct way to define a custom admin class for your CustomUser model.
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'school', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('school',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('school',)}),
    )

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'display_roles')
    search_fields = ('user__username', 'phone_number')

    def display_roles(self, obj):
        return ", ".join([role.name for role in obj.roles.all()])
    display_roles.short_description = 'Roles'

class TeacherClassAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'school', 'form_level', 'stream', 'is_class_teacher')
    list_filter = ('school', 'form_level', 'stream', 'is_class_teacher')
    search_fields = ('teacher__username', 'school__name')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Role)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(TeacherClass, TeacherClassAdmin)
