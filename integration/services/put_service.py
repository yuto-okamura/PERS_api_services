import requests
import pandas as pd

from integration.models import PutHistory
from integration.services.data_loader_service import DataManipulationService
from integration.services.put_history_service import PutHistoryService
from integration.services.stay_history_service import StayHistoryService
from integration.services.api_client_service import PersApiService


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
        
        print(
            f"    PUT処理開始："
            f"patient_id={patient_id}, "
            f"order_code={order_code}"
        )

        status = DataManipulationService.conf_status(row)
        
        if status is None:
            PutHistoryService.save_put_excluded(
                row=row,
                error_message="PUT対象となるステータスを判定できないためPUT対象外",
                put_type=put_type,
                user=user,
            )
            return None

        print(f"    status={status}")

        admission_id = row["admission_id"]

        if pd.isna(admission_id):
            PutHistoryService.save_put_excluded(
                row=row,
                error_message="admission_idが取得・作成できないためPUT対象外",
                put_type=put_type,
                user=user,
            )
            return None

        print(f"    admission_id={admission_id}")

        json_data = DataManipulationService.create_json(
            row=row,
            admission_id=admission_id,
            status=status,
        )

        if json_data is None:
            PutHistoryService.save_put_excluded(
                row=row,
                error_message="PUT用データを作成できないためPUT対象外",
                put_type=put_type,
                user=user,
            )
            return None

        print("    json作成完了")
        
        print("    PERS PUT開始")

        try:
            response = PersApiService.put_request_data(
                json_data=json_data,
                order_code=order_code,
            )
            
            print(
                f"    PERS PUTレスポンス："
                f"status_code={response.status_code}"
            )

            PutHistoryService.save(
                row=row,
                admission_id=admission_id,
                request_data=json_data,
                response=response,
                put_type=put_type,
                user=user,
            )

            print("    PutHistory保存完了")

            return response
        
        except requests.exceptions.RequestException as e:
            print(f"    PERS PUT通信エラー：{e}")
            
            PutHistoryService.save_communication_error(
                row=row,
                admission_id=admission_id,
                request_data=json_data,
                error_message=str(e),
                put_type=put_type,
                user=user,
            )
            
            print("    通信エラー PutHistory保存完了")
            
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
