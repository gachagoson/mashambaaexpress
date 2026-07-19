from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AuditLog


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('GizmoBay', {'fields': ('role', 'phone')}),
    )
    list_display = ['username', 'get_full_name', 'role', 'email', 'is_active']
    list_filter  = ['role', 'is_active']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ['timestamp', 'user', 'action', 'model_name', 'detail']
    list_filter   = ['action', 'user']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'detail', 'timestamp', 'ip_address']
    search_fields = ['user__username', 'detail']
