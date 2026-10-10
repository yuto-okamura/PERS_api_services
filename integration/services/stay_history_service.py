from django.db import transaction
from integration.models import StayHistory
from integration.services import DataManipulationService
from masters.models import (
    Ward,
    Room,
    Bed,
)

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
    def supplement_admission_history(row, admission_id):
        hospitalized_at = row["hospitalizedAt"]
        
        if pd.isna(hospitalized_at):
            return None
        
        admission_date = hospitalized_at.date()
        
        exists = StayHistory.objects.filter(
            admission_id=admission_id,
            stayed_at__date=admission_date,
        ).exists()

        if exists:
            return None
        
        if (
            pd.isna(row["ward_id"])
            or pd.isna(row["room_id"])
            or pd.isna(row["bed_id"])
        ):
            return None

        stayed_at = hospitalized_at.replace(
            hour=12,
            minute=0,
            second=0,
            microsecond=0,
        )

        StayHistory.objects.update_or_create(
            admission_id=admission_id,
            stayed_at=stayed_at,
            defaults={
                "ward_id": row["ward_id"],
                "room_id": row["room_id"],
                "bed_id": row["bed_id"],
            },            
        )

        return None

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

