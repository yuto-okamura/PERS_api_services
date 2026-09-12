from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.forms.models import ModelForm as ModelForm
from .models import (
    CustomUsers,
)
from .forms import (
    CustomUserCreationAdminForm,
    CustomUserChangeAdminForm,
)

class AuditAdminMixin:
    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, "created_by"):
            obj.created_by = request.user
        if hasattr(obj, "updated_by"):
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        if hasattr(obj, "is_active"):
            obj.is_active = False
            obj.updated_by = request.user
            obj.save(update_fields=["is_active", "updated_by"])
        else:
            super().delete_model(request, obj)
            
@admin.register(CustomUsers)
class CustomUserAdmin(AuditAdminMixin, UserAdmin):
    
    add_form = CustomUserCreationAdminForm
    form = CustomUserChangeAdminForm
    
    list_display = (
        'employee_no',
        'last_name',
        'first_name',
        'is_staff',
        'is_superuser',
    )
    list_filter = (
        'is_staff',
        'is_superuser',
    )
    search_fields = (
        'employee_no',
        'last_name',
        'first_name',
    )
    ordering = ('employee_no',)

    #追加のフィールド
    add_fieldsets = (
        ('基本情報', {
            'classes': ('wide',),
            'fields': (
                'employee_no',
                'password1',
                'password2',
                'last_name',
                'first_name',
            )
        }),
    )

    #変更のフィールド
    fieldsets = (
        ('基本情報', {
            'fields':(
                'employee_no',
                'password',
                'last_name',
                'first_name',
                'last_name_kana',
                'first_name_kana',
            )
        }),
    )