from django.contrib import admin

from .models import (
    PutHistory,
)


@admin.register(PutHistory)
class PutHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "put_type",
        "user",
        "status_code",
        "is_success",
        "put_at",
    )

    readonly_fields = (
        "id",
        "put_type",
        "user",
        "request_data",
        "status_code",
        "response_data",
        "is_success",
        "error_message",
        "put_at",
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
