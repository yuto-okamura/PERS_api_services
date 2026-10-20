from django.db import transaction
from django.db.models import Exists, OuterRef
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

import logging

from integration.models import (
    StayHistory,
    Patient,
)
from integration.services import DataManipulationService
from masters.models import (
    Ward,
    Room,
    Bed,
)

logger = logging.getLogger("csv_import")

import pandas as pd

class StayHistoryService:
    
    @staticmethod
    def save_stay_history(row, admission_id):

        StayHistory.objects.update_or_create(
            admission_id=admission_id,
            stayed_at=row["stayed_at"],
            defaults={
                "ward_id": row["ward_id"],
                "room_id": row["room_id"],
                "bed_id": row["bed_id"],
            }
        )
        
        return None

    @staticmethod
    def supplement_admission_history(row):
        admission_id = row["admission_id"]
        hospitalized_at = row["hospitalized_at"]
        
        if pd.isna(hospitalized_at) or pd.isna(admission_id):
            return None

        hospitalized_at = pd.Timestamp(hospitalized_at)
        service_start_date = pd.Timestamp("2026-10-01")
        admission_date = hospitalized_at.date()

        if admission_date < service_start_date.date():
            return None

        exists = StayHistory.objects.filter(
            admission_id=admission_id,
            stayed_at__date=admission_date,
        ).exists()

        if exists:
            return None

        next_day = admission_date + timedelta(days=1)

        next_day_stay = (
            StayHistory.objects.filter(
                admission_id=admission_id,
                stayed_at__date=next_day,
            )
            .order_by("stayed_at")
            .first()
        )

        if next_day_stay is None:
            return None

        if (
            next_day_stay.ward_id is None
            or next_day_stay.room_id is None
            or next_day_stay.bed_id is None
        ):
            return None

        stayed_at = hospitalized_at.replace(
            hour=23,
            minute=0,
            second=0,
            microsecond=0,
        )

        obj, created = StayHistory.objects.update_or_create(
            admission_id=admission_id,
            stayed_at=stayed_at,
            defaults={
                "ward_id": next_day_stay.ward_id,
                "room_id": next_day_stay.room_id,
                "bed_id": next_day_stay.bed_id,
            },            
        )

        return created

    @staticmethod
    def get_current_stay(admission_id, discharged_at):

        if pd.notna(discharged_at):
            return None

        stay = (
            StayHistory.objects
            .filter(admission_id=admission_id)
            .select_related("ward", "room", "bed")
            .order_by("-stayed_at")
            .first()
        )
        
        return stay

    @staticmethod
    def create_events(admission_id):
        
        stays = (
            StayHistory.objects
            .filter(admission_id=admission_id)
            .select_related("ward", "room", "bed")
            .order_by("stayed_at")
        )

        events = []
        previous_bed_id = None
        event = None
        event_no = 0

        for stay in stays:
            if stay.bed_id != previous_bed_id:
                event_no += 1
                
                event = {
                    "id": f"{admission_id}-{event_no:03d}",
                    "admissionId": admission_id,
                    "type": (
                        "hospitalize" if previous_bed_id is None else "move"
                    ),
                    "ward": {
                        "id": stay.ward.id,
                        "name": stay.ward.name,
                    },
                    "room": {
                        "id": stay.room.id,
                        "name": stay.room.name,
                    },
                    "bed": {
                        "id": stay.bed.id,
                        "name": stay.bed.bed_no,
                    },
                    "executedAt": stay.stayed_at.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "isPriceDifference":{},
                }

                events.append(event)
                previous_bed_id = stay.bed_id

            if event is not None:                
                event["isPriceDifference"][
                    stay.stayed_at.strftime("%Y-%m-%d")
                ] = False

        return events

    @staticmethod
    def find_missing_admission_stay_history():
        missing_patients = []
        
        patients = Patient.objects.all().only(
            "patient_id",
            "patient_name",
            "admission_id",
            "hospitalized_at",
            "discharged_at",
        )

        for patient in patients:
            hospitalized_date = timezone.localtime(
                patient.hospitalized_at
            ).date()
            
            has_stay_history = StayHistory.objects.filter(
                admission_id=patient.admission_id,
                stayed_at__date=hospitalized_date,
            ).exists()
            
            if not has_stay_history:
                missing_patients.append({
                    "patient_id": patient.patient_id,
                    "patient_name": patient.patient_name,
                    "admission_id": patient.admission_id,
                    "hospitalized_at": patient.hospitalized_at,
                    "discharged_at": patient.discharged_at,
                })
        
        return missing_patients

    @staticmethod
    def find_missing_discharge_candidates(days=3):
        threshold = timezone.now() - timedelta(days=days)
        
        patients = (
            Patient.objects
            .filter(
                discharged_at__isnull=True,
            )
            .values(
                "patient_id",
                "patient_name",
                "admission_id",
                "hospitalized_at",
                "discharged_at",
            )
        )
        
        missing_patients = []
        
        for patient in patients:
            latest_stay = (
                StayHistory.objects
                .filter(admission_id=patient["admission_id"])
                .order_by("-stayed_at")
                .values_list("stayed_at", flat=True)
                .first()
            )

            if latest_stay is None:
                missing_patients.append({
                    **patient,
                    "latest_stayed_at": None,
                    "reason": "StayHistoryなし",
                })

            elif latest_stay < threshold:
                missing_patients.append({
                    **patient,
                    "latest_stayed_at": latest_stay,
                    "reason": f"最終StayHistoryから{days}日以上経過",                    
                })

        return missing_patients

class ManualStayHistoryImportService:
    
    @staticmethod
    def execute(patient_file_path, discharge_file_path):
        all_patient_df = DataManipulationService.create_all_patient_df(
            patient_file_path=patient_file_path,
            discharge_file_path=discharge_file_path,
        )

        with transaction.atomic():
            for _, row in all_patient_df.iterrows():
                StayHistoryService.save_stay_history(
                    row,
                    row["admission_id"],
                )
                
        return len(all_patient_df)

