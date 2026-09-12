from django.contrib.auth.forms import UserCreationForm,UserChangeForm
from django import forms
from accounts.models import CustomUsers


class CustomUserCreationAdminForm(UserCreationForm):
    
    class Meta:
        model = CustomUsers
        fields = (
            'employee_no',
            'first_name',
            'last_name',
        )

class CustomUserChangeAdminForm(UserChangeForm):
    
    class Meta:
        model = CustomUsers
        fields = (
            'employee_no',
            'first_name',
            'last_name',
            'first_name_kana',
            'last_name_kana',
            'is_active',
        )
