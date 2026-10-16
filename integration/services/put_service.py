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

    @staticmethod
    def execute(
        *,
        put_type=PutHistory.PutType.AUTO,
        user=None,
        json_data,
        order_code,
        patient_name,
    ):

        patient_id = json_data["patient"]["id"]

        try:
            response = PersApiService.put_request_data(
                json_data=json_data,
                order_code=order_code,
            )
            
            PutHistoryService.save(
                order_code=order_code,
                request_data=json_data,
                response=response,
                put_type=put_type,
                user=user,
                patient_name=patient_name,
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
                order_code=order_code,
                request_data=json_data,
                error_message=str(e),
                put_type=put_type,
                user=user,
                patient_name=patient_name,
            )
            
            return None

    @staticmethod
    def execute_process(
        *,
        row,
        put_type=PutHistory.PutType.AUTO,
        user=None,
    ):
        patient_id = row["patient_id"]
        patient_name = row["patient_fullName"]
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
                order_code=order_code,
                error_message="PUT対象となるステータスを判定できないためPUT対象外",
                put_type=put_type,
                user=user,
            )
            return None

        if row["_merge"] == "left_only":

            #初回PUT前 or 入院IDなし
            if pd.isna(row["pers_admission_id"]):
                
                logger.warning(
                    f"PUT対象外：admission_idが取得・作成できない"
                    f"patient_id={patient_id}, "
                    f"order_code={order_code}"
                )
                
                PutHistoryService.save_put_excluded(
                    row=row,
                    order_code=order_code,
                    error_message="admission_idが取得・作成できないためPUT対象外",
                    put_type=put_type,
                    user=user,
                )
                return None  

            #退院後
            admission_id = row["pers_admission_id"]

            json_data = DataManipulationService.create_discharged_json(
                row=row,
                admission_id=admission_id,
            )

        else:

            admission_id = row["admission_id"]

            events = StayHistoryService.create_events(admission_id)

            json_data = DataManipulationService.create_json(
                row=row,
                admission_id=admission_id,
                status=status,
                events=events,
            )

        if json_data is None:
            logger.error(
                f"json_data作成対象データなし"
                f"patient_id={patient_id}, "
                f"order_code={order_code}"
            )
            PutHistoryService.save_put_excluded(
                row=row,
                order_code=order_code,
                error_message="PUT用データを作成できないためPUT対象外",
                put_type=put_type,
                user=user,
            )
            return None        

        response = PutService.execute(
            put_type=put_type,
            user=user,
            json_data=json_data,
            order_code=order_code,
            patient_name=patient_name,
        )

        return response
