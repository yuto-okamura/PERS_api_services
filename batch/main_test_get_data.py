import os
import traceback

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.batch_settings",
)

import django

django.setup()

from integration.services.api_client_service import PersApiService
from integration.services.api_patient_snapshot_service import ApiDataService


def main():
    print("PERS API service test batch started", flush=True)

    try:

        json_data = PersApiService.get_request_data()

        saved_count = ApiDataService.save_api_snapshot(json_data)
        print(f"保存件数：{saved_count}", flush=True)

    except Exception:

        traceback.print_exc()

    print("PERS API test finished", flush=True)

if __name__ == "__main__":
    main()
