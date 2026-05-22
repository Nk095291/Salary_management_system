from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Employee, HRUser


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'employee_id',
        'first_name',
        'last_name',
        'department',
        'job_title',
        'country',
        'status',
    ]
    list_filter = ['status', 'department', 'country', 'seniority_level']
    search_fields = ['employee_id', 'first_name', 'last_name', 'company_email']
    readonly_fields = ['employee_id', 'created_at', 'updated_at']


@admin.register(HRUser)
class HRUserAdmin(UserAdmin):
    model = HRUser
    list_display = ['email', 'first_name', 'last_name', 'employee', 'is_active', 'is_staff']
    list_filter = ['is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'employee')}),
        (
            'Permissions',
            {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')},
        ),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'password1', 'password2', 'employee'),
            },
        ),
    )
