import logging
import pandas as pd
from django.utils import timezone
from integration.models import ApiPatientSnapshot


class ApiDataService:
    
    @staticmethod
    def save_api_snapshot(response_data):
        items = response_data.get("data",[])
        
        snapshots = [
            ApiPatientSnapshot(
                order_code=item["orderCode"],
                patient_id=item["patient"]["id"],
                birth_date=item["patient"]["birthDate"],
                api_data=item,
            )
            for item in items
        ]

        ApiPatientSnapshot.objects.bulk_create(snapshots)
        
        return len(snapshots)


