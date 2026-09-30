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

    #データフレームの作成
    print("[1] df作成開始")
    created_df = DataManipulationService.data_process()
    print("[1] df作成完了")

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
            continue            
        
        admission_id = DataManipulationService.resolve_admission_id(row)

        print(f"    admission_id={admission_id}")

        #admission_idが取得、作成できない場合（未入院 or エラーデータ）
        if admission_id is None:
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
            print("過去の成功したPUT履歴が見つからないためPUT対象外")
            continue

        print(json.dumps(
            json_data,
            ensure_ascii=False,
            indent=4,
        ))

    return None

if __name__ == "__main__":
    main()
