from typing import Any
from django.contrib import admin, messages
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.safestring import mark_safe

import json
import logging

from .models import (
    PutHistory,
    StayHistory,
)

from integration.services.put_service import PutService

logger = logging.getLogger("batch")

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

    fieldsets = (
        (
            "基本情報",
            {
                "fields": (
                    "id",
                    "put_type",
                    "user",
                    "put_at",
                ),
            },
        ),
        (
            "患者情報",
            {
                "fields": (
                    "patient_id",
                    "patient_name",
                    "patient_name_kana",
                    "admission_id",                    
                ),
            },
        ),
        (
            "PUT・通信情報",
            {
                "fields": (
                    "request_data_display",
                    "status_code",
                    "response_data_display", 
                    "is_communication_success",
                    "is_integration_success",
                    "is_put_target",                   
                ),
            },
        ),
        (
            "PERSレスポンス",
            {
                "classes": ("collapse",),
                "fields": (
                    "pers_response",
                    "pers_response_description",
                    "pers_response_action",
                ),
            },
        ),
        (
            "エラー情報",
            {
                "classes": ("collapse",),
                "fields": (
                    "error_message",                    
                ),
            },
        ),
    )

    readonly_fields = (
        "id",
        "put_type",
        "user",
        "patient_id",
        "patient_name",
        "patient_name_kana",
        "admission_id",
        "request_data_display",
        "status_code",
        "response_data_display",
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
            patient_id = put_history.patient_id
            
            logger.info(
                f"手動PUT対象："
                f"patient_id={put_history.patient_id}, "
                f"admission_id={put_history.admission_id}"
            )

            put_result =PutService.execute_manual(
                patient_id=patient_id,
                user=request.user,
            )

            if put_result == PutService.ManualPutResult.SUCCESS:
                logger.info(
                    f"手動PUT成功："
                    f"patient_id={patient_id}"
                )
                
                messages.success(
                    request,
                    f"患者ID {patient_id} のPUT処理完了"
                )
                
            elif put_result == PutService.ManualPutResult.NOT_FOUND:
                logger.warning(
                    f"手動PUT対象なし："
                    f"patient_id={patient_id}"
                )
                
                messages.warning(
                    request,
                    f"患者ID {patient_id} はPERS側に存在しないため、PUT処理未実行"
                )
                
            else:
                logger.warning(
                    f"手動PUTエラー："
                    f"patient_id={patient_id}"
                )
                
                messages.warning(
                    request,
                    f"患者ID {patient_id} のPUT処理中にエラーが発生しました"
                )

    @admin.display(description="リクエストJSON")
    def request_data_display(self, obj):
        if obj.request_data is None:
            return "-"
        
        json_text = json.dumps(
            obj.request_data,
            ensure_ascii=False,
            indent=2,
        )

        return format_html(
            '<pre style="'
            'max-height: 400px; '
            'overflow: auto; '
            'white-space: pre-wrap; '
            'word-break: break-word; '
            'margin: 0;'
            '">{}</pre>',
            json_text,
        )

    @admin.display(description="レスポンスJSON")
    def response_data_display(self, obj):
        if obj.response_data is None:
            return "-"
        
        json_text = json.dumps(
            obj.response_data,
            ensure_ascii=False,
            indent=2,
        )

        return format_html(
            '<pre style="'
            'max-height: 400px; '
            'overflow: auto; '
            'white-space: pre-wrap; '
            'word-break: break-word; '
            'margin: 0;'
            '">{}</pre>',
            json_text,
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
    
    