import requests
import pandas as pd
import logging

from integration.models import PutHistory
from integration.services.data_loader_service import DataManipulationService
from integration.services.put_history_service import PutHistoryService
from integration.services.stay_history_service import StayHistoryService
from integration.services.api_client_service import PersApiService

logger = logging.getLogger("batch")

class PutService:

    class ManualPutResult:
        SUCCESS = "success"
        NOT_FOUND = "not_found"
        EXCLUDED = "excluded"
        ERROR = "error"

    @staticmethod
    def execute(
        *,
        row,
        put_type=PutHistory.PutType.AUTO,
        user=None,
    ):
        patient_id = row["patient_id"]
        order_code = row["orderCode"]
        
        status = DataManipulationService.conf_status(row)
        
        if status is None:
            logger.warning(
                f"PUT対象外："
                f"statusを判定できない "
                f"patient_id={patient_id},"
                f"order_code={order_code}"
            )
            
            PutHistoryService.save_put_excluded(
                row=row,
                error_message="PUT対象となるステータスを判定できないためPUT対象外",
                put_type=put_type,
                user=user,
            )
            return None

        admission_id = row["admission_id"]

        if pd.isna(admission_id):
            logger.warning(
                f"PUT対象外：admission_idが取得・作成できない"
                f"patient_id={patient_id}, "
                f"order_code={order_code}"
            )
            
            PutHistoryService.save_put_excluded(
                row=row,
                error_message="admission_idが取得・作成できないためPUT対象外",
                put_type=put_type,
                user=user,
            )
            return None

        json_data = DataManipulationService.create_json(
            row=row,
            admission_id=admission_id,
            status=status,
        )

        if json_data is None:
            logger.error(
                f"json_data作成対象データなし"
                f"patient_id={patient_id}, "
                f"order_code={order_code}"
            )
            PutHistoryService.save_put_excluded(
                row=row,
                error_message="PUT用データを作成できないためPUT対象外",
                put_type=put_type,
                user=user,
            )
            return None

        try:
            response = PersApiService.put_request_data(
                json_data=json_data,
                order_code=order_code,
            )
            
            PutHistoryService.save(
                row=row,
                admission_id=admission_id,
                request_data=json_data,
                response=response,
                put_type=put_type,
                user=user,
            )

            return response
        
        except requests.exceptions.RequestException as e:
            logger.error(
                f"PERS PUT通信エラー："
                f"patient_id={patient_id}, "
                f"order_code={order_code}, "
                f"error={e}"
            )
            
            PutHistoryService.save_communication_error(
                row=row,
                admission_id=admission_id,
                request_data=json_data,
                error_message=str(e),
                put_type=put_type,
                user=user,
            )
            
            return None
        
    @staticmethod
    def execute_manual(*, patient_id, user):
        row = DataManipulationService.get_manual_put_row(patient_id=patient_id)
        
        if row is None:
            return PutService.ManualPutResult.NOT_FOUND

        response = PutService.execute(
            row=row,
            put_type=PutHistory.PutType.MANUAL,
            user=user,
        )

        if response is None:
            return PutService.ManualPutResult.ERROR

        return PutService.ManualPutResult.SUCCESS
