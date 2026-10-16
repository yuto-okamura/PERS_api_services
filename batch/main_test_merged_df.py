import os
import logging

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.batch_settings",
)

import django

django.setup()

from integration.services.data_loader_service import DataManipulationService
from integration.services.put_service import PutService
from integration.services.stay_history_service import StayHistoryService
from integration.models import PutHistory

def main():

    #データフレームの作成
    all_patient_df = DataManipulationService.create_all_patient_df()

    """

    print(
        all_patient_df[
            all_patient_df["bed_id"].isna()
        ][
            [
                "patient_id",
                "ward_code",
                "room_code",
                "bed_no",
                "ward_id",
                "room_id",
                "bed_id",
            ]
        ]
    )

    """
    api_df = DataManipulationService.load_api_data()

    api_df.to_csv(
        "api_df.csv",
        index=False,
        encoding="utf-8-sig",
    )
  
    merged_df = DataManipulationService.create_merged_df(api_df, all_patient_df)

    merged_df.to_csv(
        "debug_merged.csv",
        index=False,
        encoding="utf-8-sig",
    )

    return None

if __name__ == "__main__":
    main()
