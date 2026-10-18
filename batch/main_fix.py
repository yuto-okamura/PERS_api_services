import os
import logging

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.batch_settings",
)

import django
from django.conf import settings
from django.utils import timezone

django.setup()

from integration.services.data_loader_service import DataManipulationService
from integration.services.put_service import PutService
from integration.services.stay_history_service import StayHistoryService
from integration.services.patient_service import PatientService
from integration.models import PutHistory

logger = logging.getLogger("batch")

def main():

    logger.info("バッチ開始")

    #データフレームの作成

    emr_patient_df, discharge_df = (
        DataManipulationService.load_emr_dataset()
    )

    print(f"emrPatient-取得件数: {len(emr_patient_df)}")
    print(f"discharge-取得件数: {len(discharge_df)}")

    emr_patient_df.to_csv(
        "debug_emr_patient.csv",
        index=False,
        encoding="utf-8-sig",
    )

    discharge_df.to_csv(
        "debug_discharge.csv",
        index=False,
        encoding="utf-8-sig",
    )

    success_count = 0
    error_count = 0

    for _, row in emr_patient_df.iterrows():
        try:
            PatientService.save_patient(row)
            success_count += 1
            
        except Exception as e:
            error_count += 1
            print(
                f"[ERROR] patient_id={row.get('patient_id')}, "
                f"error={e}"
            )

    print(f"成功件数-patient：{success_count}")
    print(f"エラー件数-patient：{error_count}")

    success_count = 0
    error_count = 0

    for _, row in emr_patient_df.iterrows():
        try:
            StayHistoryService.save_stay_history(
                row=row,
                admission_id=row["admission_id"],
            )
            success_count += 1
            
        except Exception as e:
            error_count += 1
            print(
                f"[ERROR] patient_id={row.get('patient_id')}, "
                f"error={e}"
            )            

    print(f"成功件数-stay：{success_count}")
    print(f"エラー件数-stay：{error_count}")

    success_count = 0
    error_count = 0

    for _, row in discharge_df.iterrows():
        try:
            PatientService.save_discharge(row)
            success_count += 1
            
        except Exception as e:
            error_count += 1
            print(
                f"[ERROR] patient_id={row.get('patient_id')}, "
                f"error={e}"
            )

    print(f"成功件数-discharge：{success_count}")
    print(f"エラー件数-discharge：{error_count}")

    logger.info("StayHistory処理開始")

    api_df = DataManipulationService.load_api_data()

    api_df.to_csv(
        "debug_api_df.csv",
        index=False,
        encoding="utf-8-sig",
    )

    for _, row in api_df.iterrows():
        PatientService.save_api_patient(row)

    logger.info("API取得開始")

    if api_df.empty:
        #logger.info("PERS API対象データなし")
        #logger.info("バッチ終了")
        return None

    logger.info("PERS APIデータ取得")

    patient_df = PatientService.load_patient_df()

    print(f"取得件数-patient: {len(patient_df)}")

    patient_df.to_csv(
        "debug_patient_df.csv",
        index=False,
        encoding="utf-8-sig",
    )

    merged_df = DataManipulationService.merge_api_patient_data(api_df, patient_df)

    print(f"取得件数-merged: {len(merged_df)}")
    print(merged_df["_merge"].value_counts(dropna=False))

    merged_df.to_csv(
        "debug_merged_df.csv",
        index=False,
        encoding="utf-8-sig",
    )

    for _, row in merged_df.iterrows():
        PutService.put_execute(
            row=row,
            put_type=PutHistory.PutType.AUTO,
        )
        
    logger.info("バッチ終了")

    return None

if __name__ == "__main__":
    main()
