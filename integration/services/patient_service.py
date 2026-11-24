import logging
import pandas as pd
from dataclasses import dataclass
from django.utils import timezone
from integration.models import Patient

logger = logging.getLogger("batch")


@dataclass
class ApiPatientSaveResult:
    patient: Patient | None
    mismatch_reason: str | None = None


class PatientService:

    @staticmethod
    def strip_name(value):
        if pd.isna(value):
            return value
        return str(value).strip(" \u3000")

    @staticmethod
    def save_patient(row):

        hospitalized_at = row["hospitalizedAt"]
        
        if pd.notna(hospitalized_at):
            hospitalized_at = pd.Timestamp(hospitalized_at).to_pydatetime()

            if timezone.is_naive(hospitalized_at):
                hospitalized_at = timezone.make_aware(
                    hospitalized_at,
                    timezone.get_current_timezone(),
                )

        patient, created = Patient.objects.update_or_create(
            admission_id=row["admission_id"],
            defaults={
                "patient_id": row["patient_id"],
                "patient_name": PatientService.strip_name(row["fullName"]),
                "patient_name_kana": PatientService.strip_name(row["fullNameKana"]),
                "birth_date": row["birthDate"],
                "hospitalized_at": hospitalized_at,
            },
        )

        return created

    @staticmethod
    def save_discharge(row):
        
        patient_id = row["patient_id"]
        discharge_date = row["dischargedAt"]
        discharge_time = row["dischargedTime"]
        
        if pd.isna(patient_id) or pd.isna(discharge_date):
            return None
        
        discharged_at = None
        
        if pd.notna(discharge_time):
            time_str = str(int(discharge_time)).zfill(6)
            
            discharged_at = pd.to_datetime(
                f"{pd.Timestamp(discharge_date).strftime('%Y%m%d')}{time_str}",
                format="%Y%m%d%H%M%S",
                errors="coerce",
            )
            
            if pd.isna(discharged_at):
                return None
            
        else:
            discharged_at = pd.Timestamp(
                discharge_date
            ).replace(
                hour=12,
                minute=0,
                second=0,
            )

        if timezone.is_naive(discharged_at):
            discharged_at = timezone.make_aware(
                discharged_at,
                timezone.get_current_timezone(),
            )

        queryset = Patient.objects.filter(
            patient_id=patient_id,
            discharged_at__isnull=True,
        ).order_by("-hospitalized_at")
        
        count = queryset.count()
        
        if count == 0:
            return None
        
        if count > 1:
            logger.info(
                "退院日登録をスキップ：未退院レコードが複数存在します "
                "patient_id=%s, 対象件数=%s",
                patient_id,
                count,
            )

            return None

        patient = queryset.first()

        if patient is None:
            return None

        patient.discharged_at = discharged_at
        patient.save(
            update_fields=["discharged_at", "updated_at"]
        )

        return patient

    @staticmethod
    def save_api_patient(row):
        
        patient_id = row.get("patient_id")
        admission_id = row.get("pers_admission_id")
        birth_date = row.get("birthDate")

        patient = None
        if pd.notna(admission_id) and admission_id:
            patient = Patient.objects.filter(
                admission_id=admission_id,
            ).first()

        if patient is None and pd.notna(patient_id) and patient_id:
            patient = Patient.objects.filter(
                patient_id=patient_id,
                birth_date=birth_date,
            ).order_by("-hospitalized_at").first()

        if patient is None:
            if Patient.objects.filter(patient_id=patient_id).exists():
                mismatch_reason = "birth_date_mismatch"
            else:
                mismatch_reason = "patient_id_mismatch"
            return ApiPatientSaveResult(
                patient=None,
                mismatch_reason=mismatch_reason,
            )

        mismatch_reason = None
        incoming_order_code = row.get("orderCode")
        if (
            pd.notna(patient.order_code)
            and str(patient.order_code).strip()
            and pd.notna(incoming_order_code)
            and str(incoming_order_code).strip()
            and str(patient.order_code).strip()
            != str(incoming_order_code).strip()
        ):
            mismatch_reason = "order_code_mismatch"
    
        update_fields = []
        
        order_code = row["orderCode"]
        
        if (
            not patient.order_code
            and pd.notna(order_code)
            and str(order_code).strip() != ""
        ):
            patient.order_code = str(order_code).strip()
            update_fields.append("order_code")
        
        service_start_date = row.get("startDate")
        
        if (
            patient.service_start_date is None
            and service_start_date is not None
            and pd.notna(service_start_date)
            and str(service_start_date).strip() != ""
        ):
            patient.service_start_date = pd.to_datetime(
                service_start_date
            ).date()

            update_fields.append("service_start_date")

        if update_fields:
            patient.save()

        return ApiPatientSaveResult(
            patient=patient,
            mismatch_reason=mismatch_reason,
        )

    @staticmethod
    def load_patient_df():
        
        queryset = Patient.objects.filter(
            order_code__isnull=False,
        ).exclude(
            order_code="",
        ).values(
            "patient_id",
            "patient_name",
            "patient_name_kana",
            "birth_date",
            "admission_id",
            "hospitalized_at",
            "discharged_at",
            "order_code",
            "service_start_date",
        )

        return pd.DataFrame.from_records(queryset)

    @staticmethod
    def load_all_patient_df():
        
        queryset = Patient.objects.all().values(
            "patient_id",
            "patient_name",
            "patient_name_kana",
            "birth_date",
            "admission_id",
            "hospitalized_at",
            "discharged_at",
            "order_code",
            "service_start_date",
        )

        return pd.DataFrame.from_records(queryset)
