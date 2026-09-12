from django.contrib import admin

from .models import (
    PostHistory,
)


@admin.register(PostHistory)
class PostHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "post_type",
        "user",
        "status_code",
        "is_success",
        "posted_at",
    )

    readonly_fields = (
        "id",
        "post_type",
        "user",
        "request_data"
        "status_code",
        "response_data",
        "is_success",
        "error_message",
        "posted_at",
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
