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

    for _, row in all_patient_df.iterrows():
        StayHistoryService.save_stay_history(
            row=row,
            admission_id=row["admission_id"],
        )

    api_df = DataManipulationService.load_api_data()
    
    merged_df = DataManipulationService.create_merged_df(api_df, all_patient_df)

    print("[1] df作成完了")

    print(merged_df)

    #データフレーム対しての処理
    for _, row in merged_df.iterrows():
        PutService.execute(
            row=row,
            put_type=PutHistory.PutType.AUTO,
        )

    return None

if __name__ == "__main__":
    main()
