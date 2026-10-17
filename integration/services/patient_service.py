import logging
import pandas as pd
from django.utils import timezone
from integration.models import Patient

logger = logging.getLogger("batch")


class PatientService:
    
    @staticmethod
    def save_patient(row):

        discharged_at = None

        discharged_date = row["dischargedAt"]
        discharged_time = row["dischargedTime"]

        if pd.notna(discharged_date):
            if pd.notna(discharged_time):
                time_str = str(int(discharged_time)).zfill(6)
                
                discharged_at = pd.to_datetime(
                    f"{pd.Timestamp(discharged_date).strftime('%Y%m%d')}{time_str}",
                    format="%Y%m%d%H%M%S",
                    errors="coerce",
                )
                
                if pd.isna(discharged_at):
                    discharged_at = None
                
            else:
                discharged_at = discharged_date.replace(
                    hour=12,
                    minute=0,
                    second=0,
                )

            if pd.notna(discharged_at):
                discharged_at = discharged_at.to_pydatetime()
                
                if timezone.is_naive(discharged_at):
                    discharged_at = timezone.make_aware(
                        discharged_at,
                        timezone.get_current_timezone(),
                    )

            else:
                discharged_at = None

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
                "patient_name": row["fullName"],
                "patient_name_kana": row["fullNameKana"],
                "birth_date": row["birthDate"],
                "hospitalized_at": hospitalized_at,
            },
        )

        if discharged_at is not None and pd.notna(discharged_at):
            patient.discharged_at = discharged_at
            patient.save(update_fields=["discharged_at", "updated_at"])

            print(
                f"患者ID={patient.patient_id}, "
                f"退院日={discharged_date!r}, "
                f"退院時刻={discharged_time!r}, "
                f"退院日時={patient.discharged_at!r}, "
                f"退院時刻型={type(patient.discharged_at).__name__}"
            )

        return patient

    @staticmethod
    def save_api_patient(row):
        
        patient_id = row.get("patient_id")
        admission_id = row.get("pers_admission_id")

        if pd.notna(admission_id) and admission_id:
            patient = Patient.objects.filter(
                admission_id=admission_id,
            ).first()
        
        elif pd.notna(patient_id) and patient_id:
            patient = Patient.objects.filter(
                patient_id=patient_id,
            ).order_by("-hospitalized_at").first()
        
        else:
            return None

        if patient is None:
            return None
        
        order_code = row["orderCode"]
        patient.order_code = order_code

        service_start_date = row.get("startDate")
        
        if (
            service_start_date is not None
            and pd.notna(service_start_date)
            and service_start_date != ""
        ):
            patient.service_start_date = pd.to_datetime(
                service_start_date
            ).date()

        patient.save()

    @staticmethod
    def load_patient_df():
        
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
    