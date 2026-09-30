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

    #データフレームの作成
    print("[1] df作成開始")
    created_df = DataManipulationService.data_process()
    print("[1] df作成完了")
    
    print(created_df)

    return None

if __name__ == "__main__":
    main()
