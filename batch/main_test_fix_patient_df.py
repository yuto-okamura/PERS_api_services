import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.batch_settings",
)

import django

django.setup()

from integration.services.data_loader_service import DataManipulationService

def main():

    #データフレームの作成
    print("[1] df作成開始")
    all_patient_df = DataManipulationService.create_all_patient_df()

    print(all_patient_df)

    return None

if __name__ == "__main__":
    main()
