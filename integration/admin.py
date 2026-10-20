from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime

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
from django.shortcuts import redirect

import re
import json
import logging

from .models import (
    PutHistory,
    StayHistory,
    ImportHistory,
    Patient,
)

from integration.services.put_service import PutService
from integration.services.data_loader_service import DataManipulationService
from integration.services.stay_history_service import StayHistoryService
from integration.services.put_history_service import PutHistoryService
from integration.services.patient_service import PatientService

logger = logging.getLogger("manual_put")
csv_import_logger = logging.getLogger("csv_import")

@admin.register(PutHistory)
class PutHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient_id",
        "put_type",
        "order_code",
        "user",
        "status_code",
        "pers_response",
        "is_communication_success",
        "is_integration_success",
        "put_at",
        "manual_put_link",
    )

    search_fields = (
        "order_code",
        "patient_id",
        "admission_id",
    )

    fieldsets = (
        (
            "基本情報",
            {
                "fields": (
                    "id",
                    "put_type",
                    "order_code",
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
        "order_code",
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
    
    @admin.display(description="手動PUT")
    def manual_put_link(self, obj):
        url = reverse(
            "admin:integration_puthistory_manual_put",
            args=[obj.pk],
        )

        return format_html(
            '<a class="button" href="{}">手動PUT</a>',
            url,
        )

    def get_urls(self):
        urls = super().get_urls()
        
        custom_urls = [
            path(
                "<int:object_id>/manual-put/",
                self.admin_site.admin_view(self.manual_put_view),
                name="integration_puthistory_manual_put",
            ),
        ]

        return custom_urls + urls

    def create_manual_put_json(self, put_history):
        
        patient = (
            Patient.objects
            .filter(order_code=put_history.order_code)
            .first()
        )

        if patient is None:
            raise ValueError(
                "Patientテーブルに対象患者が存在しません"
            )

        admission_id = patient.admission_id
        discharged_at = patient.discharged_at

        current_stay = StayHistoryService.get_current_stay(
            admission_id=admission_id,
            discharged_at=discharged_at,
        )

        events = StayHistoryService.create_events(admission_id)
        
        status = (
            "discharged"
            if patient.discharged_at is not None
            else "hospitalized"
        )

        patient_id = patient.patient_id
        hospitalized_at = patient.hospitalized_at
        patient_name_kana = patient.patient_name_kana
        birth_date = patient.birth_date

        json_data = DataManipulationService.create_json_request(
            patient_id=patient_id,
            admission_id=admission_id,
            status=status,
            hospitalized_at=hospitalized_at,
            discharged_at=discharged_at,
            current_stay=current_stay,
            patient_name_kana=patient_name_kana,
            birth_date=birth_date,
            events=events,
        )

        return json_data

    def manual_put_view(self, request, object_id):
        
        put_history = self.get_object(request, object_id)
        
        if put_history is None:
            messages.error(request, "対象のPUT履歴が見つかりません")
            return redirect("admin:integration_puthistory_changelist")

        patient = (
            Patient.objects
            .filter(order_code=put_history.order_code)
            .first()
        )

        if patient is None:
            messages.error(
                request,
                "Patientテーブルに該当患者なし"
            )
            return redirect(
                "admin:integration_puthistory_change",
                object_id,
            )

        admission_id = patient.admission_id

        try:
            request_data = self.create_manual_put_json(put_history)
            
        except ValueError as e:
            messages.error(request, str(e))
            return redirect(
                "admin:integration_puthistory_change",
                object_id,
            )
        
        except Exception:
            logger.exception(
                "手動PUT用JSON作成失敗："
                "patient_id=%s, admission_id=%s",
                patient.patient_id,
                admission_id
            )

            messages.error(
                request,
                "JSON作成に失敗しました。"
            )
            
            return redirect(
                "admin:integration_puthistory_change",
                object_id,
            )            
            
        json_text = json.dumps(
            request_data,
            ensure_ascii=False,
            indent=2,
        )

        if request.method == "POST":
            
            json_text = request.POST.get("request_data", "")
            
            try:
                json_data = json.loads(json_text)
                
            except json.JSONDecodeError as e:
                messages.error(
                    request,
                    f"JSONの形式が正しくありません。位置：{e.pos}",
                )

            else:
                
                if not isinstance(json_data, dict):
                    messages.error(
                        request,
                        "リクエストJSONはオブジェクト形式で入力してください",
                    )

                else:
                    required_keys = [
                        "id",
                        "status",
                        "hospitalizedAt",
                        "dischargedAt",
                        "ward",
                        "room",
                        "bed",
                        "patient",
                        "events",
                    ]

                    missing_keys = [
                        key for key in required_keys
                        if key not in json_data
                    ]

                    if missing_keys:
                        messages.error(
                            request,
                            "必須項目が不足しています："
                            + ", ".join(missing_keys),
                        )

                    elif not isinstance(json_data["patient"], dict):
                        messages.error(
                            request,
                            "patientはオブジェクト形式で入力してください",
                        )

                    elif not isinstance(json_data["events"], list):
                        messages.error(
                            request,
                            "eventsは配列形式で入力してください"
                        )

                    elif json_data["id"] != admission_id:
                        messages.error(
                            request,
                            "入院IDは対象レコードの入院IDから変更できません",
                        )

                    else:
                        
                        try:
                            responce = PutService.execute(
                                put_type=PutHistory.PutType.MANUAL,
                                user=request.user,
                                json_data=json_data,
                                order_code=put_history.order_code,
                                patient_name=put_history.patient_name,
                            )
                            
                        except Exception:
                            logger.exception(
                                "手動PUT実行中に予期しないエラーが発生："
                                f"patient_id={put_history.patient_id}, "
                                f"admission_id={put_history.admission_id}"
                            )
                            
                            messages.error(
                                request,
                                "手動PUTエラー"
                            )

                        else:
                            if responce is not None:
                                messages.success(
                                    request,
                                    "PUTリクエストを実行しました",
                                )

                            else:
                                messages.warning(
                                    request,
                                    "PUT処理が完了しませんでした。"
                                )

                            return redirect(
                                "admin:integration_puthistory_changelist"
                            )

        context = {
            **self.admin_site.each_context(request),
            "title": "手動PUT",
            "put_history": put_history,
            "patient": patient,
            "json_text": json_text,
            "opts": self.model._meta,
        }

        return TemplateResponse(
            request,
            "admin/integration/puthistory/manual_put.html",
            context,
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

    search_fields = (
        "admission_id",
    )

class PatientCsvImportForm(forms.Form):
    #Csv取込専用フォーム
    
    patient_file = forms.FileField(
        label="対象患者Csv",
        help_text=(
            "末尾「_YYYYmmddHHMMSS.csv」のcsvファイルを選択してください<br>"
            "例：current_patient_20261001120000.csv<br>"
            "【必須カラム】 patient_id, fullName, fullNameKana, birthDate, hospitalizedAt, ward_code, room_code, bed_no"
        ),
        widget=forms.ClearableFileInput(attrs={"accept": ".csv"})
    )

    def clean_patient_file(self):
        file = self.cleaned_data["patient_file"]

        filename = file.name
        
        pattern = r".*_(\d{14})\.csv"
        
        match = re.fullmatch(pattern, filename, re.IGNORECASE)
        
        if not match:
            raise forms.ValidationError(
                "ファイル名の末尾を「_YYYYmmddHHMMSS.csv」の形式にしてください"
            )
            
        timestamp = match.group(1)
        
        try:
            datetime.strptime(timestamp, "%Y%m%d%H%M%S")
        except ValueError:
            raise forms.ValidationError(
                "ファイル名の日時が正しくありません"
            )

        return file

class DischargeCsvImportForm(forms.Form):
    #Csv取込専用フォーム
    
    discharge_file = forms.FileField(
        label="対象退院データCsv",
        help_text=(
            "対象のcsvファイルを選択してください<br>"
            "【必須カラム】patient_id, dischargedAt, dischargedTime<br>"
            "【書式】<br>"
            " ・dischargedAt：退院日（YYYYmmdd または日付形式）<br>"
            " ・dischargedTime：退院時刻（HHMMSS、例093000）<br>"
            " ※ dischagedTimeがない場合、退院時刻は12:00:00として登録されます"
        ),
        widget=forms.ClearableFileInput(attrs={"accept": ".csv"})
    )
   
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

        patient_form = PatientCsvImportForm()
        discharge_form = DischargeCsvImportForm()

        if request.method == "POST":
            
            import_type = request.POST.get("import_type")
            
            if import_type == "patient":
                patient_form = PatientCsvImportForm(request.POST, request.FILES)
                
                if patient_form.is_valid():

                    try:
                        patient_file = patient_form.cleaned_data["patient_file"]
                        
                        with TemporaryDirectory() as temp_dir:
                            temp_dir = Path(temp_dir)
                            
                            patient_path = temp_dir / patient_file.name
                            
                            with patient_path.open("wb") as f:
                                for chunk in patient_file.chunks():
                                    f.write(chunk)
                            
                            patient_df = (
                                DataManipulationService.load_emr_patient_data(
                                    patient_file_path=patient_path,
                                )
                            )

                            for _, row in patient_df.iterrows():
                                PatientService.save_patient(
                                    row,
                                )

                            for _, row in patient_df.iterrows():
                                StayHistoryService.save_stay_history(
                                    row,
                                    row["admission_id"],
                                )

                        self.message_user(
                            request,
                            (
                                "Csv取込処理が完了しました。"
                                f"対象件数：{len(patient_df)}件"
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

            elif import_type == "discharge":
                discharge_form = DischargeCsvImportForm(request.POST, request.FILES)

                if discharge_form.is_valid():

                    try:
                        discharge_file = discharge_form.cleaned_data["discharge_file"]
                        
                        with TemporaryDirectory() as temp_dir:
                            temp_dir = Path(temp_dir)
                            
                            discharge_path = temp_dir / discharge_file.name
                                                               
                            with discharge_path.open("wb") as f:
                                for chunk in discharge_file.chunks():
                                    f.write(chunk)
                            
                            discharge_df = (
                                DataManipulationService.load_emr_discharge_data(
                                    discharge_file_path=discharge_path,
                                )
                            )

                            for _, row in discharge_df.iterrows():
                                PatientService.save_discharge(
                                    row,
                                )

                        self.message_user(
                            request,
                            (
                                "Csv取込処理が完了しました。"
                                f"対象件数：{len(discharge_df)}件"
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
            
        context = {
            **self.admin_site.each_context(request),
            "title": "Csv取込",
            "patient_form": patient_form,
            "discharge_form": discharge_form,
            "opts": self.model._meta,
        }

        return TemplateResponse(
            request,
            "admin/integration/importhistory/csv_import.html",
            context,
        )

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "patient_id",
        "patient_name",
        "patient_name_kana",
        "admission_id",
        "hospitalized_at",
        "discharged_at",
        "order_code",
        "service_start_date",
    )

    search_fields = (
        "patient_id",
        "patient_name",
        "patient_name_kana",
        "admission_id",
        "order_code",
    )

    list_filter = (
        "hospitalized_at",
        "discharged_at",
        "service_start_date",
    )

    ordering = ("-hospitalized_at",)
