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
from integration.services.patient_service import PatientService
from integration.models import PutHistory

#logger = logging.getLogger("batch")

def main():

    #logger.info("バッチ開始")

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
    #logger.info("StayHistory処理開始")
    
    print(f"取得件数: {len(all_patient_df)}")

    all_patient_df.to_csv(
        "debug_all_patient.csv",
        index=False,
        encoding="utf-8-sig",
    )

    success_count = 0
    error_count = 0

    for _, row in all_patient_df.iterrows():
        try:
            PatientService.save_patient(row)
            success_count += 1
            
        except Exception as e:
            error_count += 1
            print(
                f"[ERROR] patient_id={row.get('patient_id')}, "
                f"error={e}"
            )
            
    print(f"成功件数：{success_count}")
    print(f"エラー件数：{error_count}")
    
    for _, row in all_patient_df.iterrows():       
        StayHistoryService.save_stay_history(
            row=row,
            admission_id=row["admission_id"],
        )



    api_df = DataManipulationService.load_api_data()

    api_df.to_csv(
        "debug_api_df.csv",
        index=False,
        encoding="utf-8-sig",
    )

    for _, row in api_df.iterrows():
        PatientService.save_api_patient(row)

    #logger.info("API取得開始")

    if api_df.empty:
        #logger.info("PERS API対象データなし")
        #logger.info("バッチ終了")
        return None

    #logger.info("PERS APIデータ取得")

    patient_df = PatientService.load_patient_df()

    print(f"取得件数: {len(patient_df)}")

    patient_df.to_csv(
        "debug_patient_df.csv",
        index=False,
        encoding="utf-8-sig",
    )

    merged_df = DataManipulationService.merge_api_patient_data(api_df, patient_df)

    print(f"取得件数: {len(merged_df)}")

    merged_df.to_csv(
        "debug_merged_df.csv",
        index=False,
        encoding="utf-8-sig",
    )

    #logger.info("バッチ終了")

    return None

if __name__ == "__main__":
    main()
