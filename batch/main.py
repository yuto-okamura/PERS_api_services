import os
import json
import requests

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

import django

django.setup()

from integration.services.data_loader_service import DataManipulationService
from integration.services.api_client_service import PersApiService
from integration.services.put_history_service import PutHistoryService
from integration.services import StayHistoryService
from integration.models import PutHistory

def main():
    print("PERS API service batch started")

    json_data = PersApiService.get_request_data()
    
    print(json.dumps(
        json_data,
        ensure_ascii=False,
        indent=4,
    ))

    #データフレームの作成
    print("[1] df作成開始")
    created_df = DataManipulationService.data_process()
    print("[1] df作成完了")
    
    print(created_df)

    #データフレーム対しての処理
    for _, row in created_df.iterrows():
    
        print(
            "[2] 患者処理開始"
            f"patient_id={row['patient_id']}, "
            f"order_code={row['orderCode']}"
        )
    
        status = DataManipulationService.conf_status(row)

        print(f"    status={status}")

        #入院状況が判定できない場合（未入院？）
        if status is None:
            PutHistoryService.save_put_excluded(
                row=row,
                error_message="PUT対象となるステータスを判定できないためPUT対象外"
            )
            continue            
        
        admission_id = DataManipulationService.resolve_admission_id(row)

        print(f"    admission_id={admission_id}")

        #admission_idが取得、作成できない場合（未入院 or エラーデータ）
        if admission_id is None:
            PutHistoryService.save_put_excluded(
                row=row,
                error_message="admission_idが取得・作成できないためPUT対象外"
            )
            continue

        #退院者のjson作成
        if status == "discharged" and row["_merge"] == "left_only":
            json_data = DataManipulationService.create_discharged_json(row, admission_id)

        #通常の入院患者のjson作成（初回と継続入院中）
        else:

            print("    json作成開始")

            StayHistoryService.save_stay_history(
                row=row,
                admission_id=admission_id,
            )

            print("    StayHistory保存完了")

            json_data = DataManipulationService.create_json(
                row=row,
                admission_id=admission_id,
                status=status,
            )

            print("    json作成完了")

        #jsonを作成できなかった場合
        if json_data is None:
            PutHistoryService.save_put_excluded(
                row=row,
                error_message="過去の成功したPUT履歴が見つからないためPUT対象外"
            )
            continue

        print(json.dumps(
            json_data,
            ensure_ascii=False,
            indent=4,
        ))
        
        try:
        
            response = PersApiService.put_request_data(
                json_data=json_data,
                order_code=row["orderCode"],
            )

            print(
                "    PERS PUTレスポンス："
                f"status_code={response.status_code}"
            )

            PutHistoryService.save(
                row=row,
                admission_id=admission_id,
                request_data=json_data,
                response=response,
            )

            print("    puthistory保存完了")

        except requests.exceptions.RequestException as e:
            
            PutHistoryService.save_communication_error(
                row=row,
                admission_id=admission_id,
                request_data=json_data,
                error_message=str(e),
            )

    return None

if __name__ == "__main__":
    main()
