import os
import logging
import time
from datetime import datetime

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
from integration.services.error_notification_service import (
    BatchError,
    ErrorNotificationService,
)
from integration.services.api_patient_snapshot_service import ApiDataService
from integration.services.api_client_service import PersApiService
from integration.models import PutHistory

logger = logging.getLogger("batch")

def main():

    logger.info("バッチ開始")

    errors = []

    #データフレームの作成

    try:
        patient_file_path = DataManipulationService.get_latest_data_file(
            "current_patient"
        )

        file_timestamp = datetime.strptime(
            patient_file_path.stem.split("_")[-1],
            "%Y%m%d%H%M%S",
        )
        if file_timestamp.date() != timezone.localdate():
            raise ValueError(
                f"本日の患者データではありません: {patient_file_path.name}"
            )

    except Exception:
        logger.exception("本日の患者データ確認に失敗しました")
        errors.append(
            BatchError(
                key_value="current_patient",
                message="当日データの取得エラー。管理端末を確認してください",
                category="データ取得",
                importance="A",
            )
        )
        ErrorNotificationService.send_error_alert(errors)
        logger.info("患者データ確認エラーのためバッチ終了")
        return None

    emr_patient_df, discharge_df = (
        DataManipulationService.load_emr_dataset(
            patient_file_path=patient_file_path,
        )
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

    saved_count = ApiDataService.save_api_snapshot(json_data)

    logger.info(
        "APIリクエスト数：%s件",
        saved_count,
    )

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

    for _, row in merged_df.iterrows():
        try:
            result = PutService.put_execute(
                row=row,
                put_type=PutHistory.PutType.AUTO,
            )

        except Exception:
            logger.exception("PUT処理中に予期しないエラー発生")
            errors.append(
                BatchError(
                    key_value=str(row.get("orderCode", "")),
                    message="予期しない例外",
                    category="PUT処理",
                    importance="C",
                )
            )
        
        else:
            if result.status == "error":
                errors.append(
                    BatchError(
                        key_value=result.order_code,
                        message=result.error_message or "PUT処理エラー",
                        category="PUT処理",
                        importance="C",
                    )
                )

        time.sleep(1)

    if errors:
        sent = ErrorNotificationService.send_error_alert(errors)
        if sent:
            logger.info(
                "%d件のエラーあり。エラー通知をSESへ依頼",
                len(errors),
            )
        
    logger.info("バッチ終了")

    return None

if __name__ == "__main__":
    main()
