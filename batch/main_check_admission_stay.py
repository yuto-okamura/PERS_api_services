import os
import json

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.batch_settings",
)

import django

django.setup()

from integration.services.stay_history_service import StayHistoryService


def main():
    print("PERS Check AdmissionStay", flush=True)

    missing = StayHistoryService.find_missing_admission_stay_history()

    print(f"欠損候補：{len(missing)}件",flush=True)
    
    for row in missing:
        print(row, flush=True)

    print("PERS Check finished", flush=True)

if __name__ == "__main__":
    main()
