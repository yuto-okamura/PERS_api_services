import os
import logging
import shutil
import pandas as pd

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.batch_settings",
)

import django
from pathlib import Path

django.setup()

from integration.services.data_loader_service import DataManipulationService
from integration.services.stay_history_service import StayHistoryService
from integration.services.patient_service import PatientService

logger = logging.getLogger("batch")

NIGHT_DATA_DIR = Path("integration/night_input")
NIGHT_PROCESSED_DIR = Path("integration/night_processed")

def main():

    logger.info("夜間csv取り込み開始")

    #データフレームの作成

    night_folder = NIGHT_DATA_DIR

    patient_path = (
        DataManipulationService.get_latest_data_file(
            "current_patient",
            data_dir=night_folder,
        )
    )

    emr_patient_df = (
        DataManipulationService.load_emr_patient_data(
            patient_file_path=patient_path,
        )
    )

    discharge_path = None

    try:
        discharge_path = (
            DataManipulationService.get_latest_data_file(
                "discharge",
                data_dir=night_folder,
            )
        )

        discharge_df = (
            DataManipulationService.load_emr_discharge_data(
                discharge_file_path=discharge_path,
            )
        )
    
    except FileNotFoundError:
        discharge_df = pd.DataFrame(
            columns=["patient_id", "dischargedAt"]
        )

        logger.warning(
            "退院csvデータが見つからないため処理をスキップ"
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

    create_count = 0
    existing_count = 0
    success_count = 0
    error_count = 0
    total_error_count = 0

    for _, row in emr_patient_df.iterrows():
        try:
            created = PatientService.save_patient(row)

            success_count += 1

            if created:
                create_count += 1
            else:
                existing_count += 1
            
        except Exception as e:
            error_count += 1
            print(
                f"[ERROR] patient_id={row.get('patient_id')}, "
                f"error={e}"
            )

    logger.info(
        "Patient取込結果：新規=%s件、既存=%s件、エラー=%s件",
        create_count,
        existing_count,
        error_count,
    )

    total_error_count += error_count

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

    total_error_count += error_count

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

    total_error_count += error_count

    logger.info("夜間データ取り込み終了")

    if total_error_count == 0:
        try:
            NIGHT_PROCESSED_DIR.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.move(
                str(patient_path),
                str(NIGHT_PROCESSED_DIR / patient_path.name),
            )

            shutil.move(
                str(discharge_path),
                str(NIGHT_PROCESSED_DIR / discharge_path.name),
            )

            logger.info("夜間csv処理済みフォルダへ移動")
        
        except Exception:
            logger.exception("csvファイル移動失敗")

    else:
        logger.error(
            "エラーデータが確認されました"
        )

    return None

if __name__ == "__main__":
    main()
