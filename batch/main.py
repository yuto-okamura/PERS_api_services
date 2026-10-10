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

logger = logging.getLogger("batch")

def main():

    logger.info("バッチ開始")

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
    for _, row in all_patient_df.iterrows():
        StayHistoryService.save_stay_history(
            row=row,
            admission_id=row["admission_id"],
        )

    api_df = DataManipulationService.load_api_data()

    if api_df.empty:
        logger.info("PERS API対象データなし")
        logger.info("バッチ終了")
        return None

    logger.info("PERS APIデータ取得")
   
    merged_df = DataManipulationService.create_merged_df(api_df, all_patient_df)

    #データフレーム対しての処理
    for _, row in merged_df.iterrows():
        PutService.execute(
            row=row,
            put_type=PutHistory.PutType.AUTO,
        )

    logger.info("バッチ終了")

    return None

if __name__ == "__main__":
    main()
