import os
import logging
import time

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.batch_settings",
)

import django
from django.conf import settings
from django.utils import timezone

django.setup()

from integration.services.data_loader_service import DataManipulationService
from integration.services.put_service import PutService, PutResult
from integration.services.stay_history_service import StayHistoryService
from integration.services.patient_service import PatientService
from integration.services.api_client_service import PersApiService
from integration.models import PutHistory

logger = logging.getLogger("batch")

def main():

    logger.info("バッチ開始")

    #データフレームの作成

    emr_patient_df, discharge_df = (
        DataManipulationService.load_emr_dataset()
    )

    logger.info("Patient処理開始")

    create_count = 0
    existing_count = 0
    success_count = 0
    error_count = 0

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
            logger.info(
                f"[ERROR] patient_id={row.get('patient_id')}, "
                f"error={e}"
            )

    logger.info(
        "Patient取込結果：新規=%s件、既存=%s件、エラー=%s件、",
        create_count,
        existing_count,
        error_count,
    )

    logger.info("StayHistory処理開始")

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
            logger.exception(
                "StayHistory取り込みエラー：patient_id=%s",
                row.get("patient_id"),
            )

    logger.info(
        "StayHistory取込結果：成功=%s件、エラー：%s",
        success_count,
        error_count,
    )

    logger.info("退院情報取得処理開始")

    success_count = 0
    error_count = 0

    for _, row in discharge_df.iterrows():
        try:
            PatientService.save_discharge(row)
            success_count += 1
            
        except Exception as e:
            error_count += 1
            logger.exception(
                "退院情報取り込みエラー：patient_id=%s",
                row.get("patient_id"),
            )

    logger.info(
        "退院情報取込結果：成功%s件、エラー%s件",
        success_count,
        error_count,
    )

    logger.info("API取得開始")

    json_data = PersApiService.get_request_data()

    api_df = DataManipulationService.load_api_data(json_data)

    api_df["mismatch_reason"] = None
    for index, row in api_df.iterrows():
        save_result = PatientService.save_api_patient(row)
        api_df.at[index, "mismatch_reason"] = save_result.mismatch_reason

    if api_df.empty:
        logger.info("PERS API対象データなし")
        logger.info("バッチ終了")
        return None

    patient_df = PatientService.load_patient_df()

    merged_df = DataManipulationService.merge_api_patient_data(api_df, patient_df)

    logger.info(
        "マージ結果：%s",
        merged_df['_merge'].value_counts(dropna=False).to_dict(),
    )

    errors = []

    for _, row in merged_df.iterrows():
        try:
            result = PutService.put_execute(
                row=row,
                put_type=PutHistory.PutType.AUTO,
            )

        except Exception:
            logger.exception("PUT処理中に予期しないエラー発生")
            errors.append(
                PutResult(
                    status="error",
                    order_code=str(row.get("orderCode","")),
                    error_message="予期しない例外",
                )
            )
        
        else:
            if result.status == "error":
                errors.append(result)

        time.sleep(1)
       
    logger.info("バッチ終了")

    return None

if __name__ == "__main__":
    main()
