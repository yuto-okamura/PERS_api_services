import os
import json
import requests

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

import django

django.setup()

from integration.services.data_loader_service import DataManipulationService
from integration.services.api_client_service import PersApiService
from integration.services.put_history_service import PutHistoryService
from integration.services import StayHistoryService
from integration.models import PutHistory

def main():
    print("PERS API service batch started")

    json_data = PersApiService.get_request_data()
    
    print(json.dumps(
        json_data,
        ensure_ascii=False,
        indent=4,
    ))

    return None

if __name__ == "__main__":
    main()
