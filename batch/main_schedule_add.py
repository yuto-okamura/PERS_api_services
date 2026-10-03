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

    #データフレームの作成
    print("[1] df作成開始")
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
    for _, row in all_patient_df.iterrows():
        StayHistoryService.save_stay_history(
            row=row,
            admission_id=row["admission_id"],
        )

    return None

if __name__ == "__main__":
    main()
