from typing import Any

from django.contrib import admin
from django.http import HttpRequest

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
        "pers_response",
        "is_communication_success",
        "is_integration_success",
        "put_at",
    )

    fields = (
        "id",
        "put_type",
        "user",
        "patient_id",
        "patient_name",
        "patient_name_kana",
        "admission_id",
        "request_data",
        "status_code",
        "response_data",
        "pers_response",
        "pers_response_description",
        "pers_response_action",
        "is_communication_success",
        "is_integration_success",
        "is_put_target",
        "error_message",
        "put_at",
    )

    readonly_fields = (
        "id",
        "put_type",
        "user",
        "patient_id",
        "patient_name",
        "patient_name_kana",
        "admission_id",
        "request_data",
        "status_code",
        "response_data",
        "pers_response",
        "pers_response_description",
        "pers_response_action",
        "is_communication_success",
        "is_integration_success",
        "is_put_target",
        "error_message",
        "put_at",
    )

    actions = ["manual_put"]
    
    @admin.action(description="選択した患者を手動PUT")
    def manual_put(self, request, queryset):
        for put_history in queryset:
            print(
                f"手動PUT対象："
                f"patient_id={put_history.patient_id}, "
                f"admission_id={put_history.admission_id}"
            )

    @admin.display(description="PERSレスポンス状況")
    def pers_response_description(self, obj):
        if obj.pers_response is None:
            return "-"
        return obj.pers_response.description

    @admin.display(description="PERSレスポンス状況")
    def pers_response_action(self, obj):
        if obj.pers_response is None:
            return "-"
        return obj.pers_response.action

    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True


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
    
    