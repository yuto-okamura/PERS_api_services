from pathlib import Path
from tempfile import TemporaryDirectory

from typing import Any
from django import forms
from django.contrib import admin, messages
from django.http import HttpRequest, HttpResponseRedirect
from django.http.response import HttpResponse
from django.template.response import TemplateResponse
from django.urls.resolvers import URLPattern
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import path, reverse


import json
import logging

from .models import (
    PutHistory,
    StayHistory,
    ImportHistory,
)

from integration.services.put_service import PutService
from integration.services.data_loader_service import DataManipulationService
from integration.services.stay_history_service import StayHistoryService

logger = logging.getLogger("manual_put")
csv_import_logger = logging.getLogger("csv_import")

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
    
class CsvImportForm(forms.Form):
    #Csv取込専用フォーム
    
    patient_file = forms.FileField(
        label="対象患者Csv",
        help_text="対象のcurrent_patient_*.csvファイルを選択してください",
    )

    discharge_file = forms.FileField(
        label="対象退院データCsv",
        help_text="対象のdischarge_*.csvファイルを選択してください",
    )

    def clean_patient_file(self):
        file = self.cleaned_data["patient_file"]
        
        if not file.name.lower().endswith(".csv"):
            raise forms.ValidationError(
                "対象患者CsvはCsvファイルを指定してください"
            )
            
        return file
    
    def clean_discharge_file(self):
        file = self.cleaned_data["discharge_file"]
        
        if not file.name.lower().endswith(".csv"):
            raise forms.ValidationError(
                "対象退院データCsvはCsvファイルを指定してください"
            )
            
        return file

@admin.register(ImportHistory)
class ImportHistoryAdmin(admin.ModelAdmin):
    #Csv取込専用画面

    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_urls(self):
        urls = super().get_urls()
        
        custom_urls = [
            path(
                "csv-import/",
                self.admin_site.admin_view(self.csv_import_view),
                name="integration_importhistory_csv_import",
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        return HttpResponseRedirect(
            reverse("admin:integration_importhistory_csv_import")
        )

    def csv_import_view(self, request):
        
        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)

            if form.is_valid():
                try:
                    patient_file = form.cleaned_data["patient_file"]
                    discharge_file = form.cleaned_data["discharge_file"]
                    
                    with TemporaryDirectory() as temp_dir:
                        temp_dir = Path(temp_dir)
                        
                        patient_path = temp_dir / patient_file.name
                        discharge_path = temp_dir / discharge_file.name
                        
                        with patient_path.open("wb") as f:
                            for chunk in patient_file.chunks():
                                f.write(chunk)
                                
                        with discharge_path.open("wb") as f:
                            for chunk in discharge_file.chunks():
                                f.write(chunk)
                        
                        all_patient_df = (
                            DataManipulationService.create_all_patient_df(
                                patient_file_path=patient_path,
                                discharge_file_path=discharge_path,
                            )
                        )

                        for _, row in all_patient_df.iterrows():
                            StayHistoryService.save_stay_history(
                                row,
                                row["admission_id"],
                            )

                    self.message_user(
                        request,
                        (
                            "Csv取込処理が完了しました。"
                            f"対象件数：{len(all_patient_df)}件"
                        ),
                    )

                    return HttpResponseRedirect(
                        reverse(
                            "admin:integration_importhistory_csv_import"
                        )
                    )
                except Exception:
                    csv_import_logger.exception("Csv取込処理に失敗しました")
                    
                    self.message_user(
                        request,
                        "Csv取込処理に失敗しました。ログを確認してください",
                        level=messages.ERROR,
                    )

        else:
            form = CsvImportForm()
            
        context = {
            **self.admin_site.each_context(request),
            "title": "Csv取込",
            "form": form,
            "opts": self.model._meta,
        }

        return TemplateResponse(
            request,
            "admin/integration/importhistory/csv_import.html",
            context,
        )
