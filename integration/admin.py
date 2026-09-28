from django.contrib import admin

from .models import (
    PutHistory,
    StayHistory,
)


@admin.register(PutHistory)
class PutHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "put_type",
        "user",
        "status_code",
        "is_communication_success",
        "is_integration_success",
        "put_at",
    )

    readonly_fields = (
        "id",
        "put_type",
        "user",
        "request_data",
        "status_code",
        "response_data",
        "is_communication_success",
        "is_integration_success",
        "error_message",
        "put_at",
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(StayHistory)
class StayHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "admission_id",
        "stayed_at",
        "ward",
        "room",
        "bed",
        "created_at",
    )
    
    list_filter = (
        "ward",
        "room",
        "stayed_at",
    )
    
    ordering = (
        "-stayed_at",
    )
    
    