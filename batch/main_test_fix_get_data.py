import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

import django

django.setup()

from integration.services.data_loader_service import DataManipulationService
from integration.services.put_service import PutService
from integration.services.stay_history_service import StayHistoryService
from integration.services.patient_service import PatientService
from integration.models import PutHistory

def main():

    api_df = DataManipulationService.load_api_data()

    print(api_df)

    for _, row in api_df.iterrows():
        PatientService.save_api_patient(row)

    return None

if __name__ == "__main__":
    main()
