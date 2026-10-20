import os
import json
import pandas as pd

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.batch_settings",
)

import django

django.setup()

from integration.services.stay_history_service import StayHistoryService
from integration.services.data_loader_service import DataManipulationService
from integration.services.patient_service import PatientService

def main():

    patient_df = PatientService.load_patient_df()

    target_admission_id = "0000103275-20261019"
    
    patient_df = patient_df[
        patient_df["admission_id"] == target_admission_id
    ]

    print(patient_df[["patient_id", "admission_id", "hospitalized_at"]])

    supplement_count = 0

    for _, row in patient_df.iterrows():
        created = StayHistoryService.supplement_admission_history(row)

        if created:
            supplement_count += 1
            
    print(f"補完件数：{supplement_count}件")

if __name__ == "__main__":
    main()
