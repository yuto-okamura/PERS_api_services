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
from integration.models import PutHistory

def main():

    api_df = DataManipulationService.load_api_data()

    print(api_df)

    return None

if __name__ == "__main__":
    main()
