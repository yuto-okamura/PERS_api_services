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

    try:

        json_data = PersApiService.get_request_data()
        
        print(json.dumps(
            json_data,
            ensure_ascii=False,
            indent=4,
        ))
    
    except requests.exceptions.RequestException as e:
        print(f"PERS API通信エラー: {e}")

    except ValueError as e:
        print(f"レスポンスJSON解析エラー: {e}")

    """
    
    #データフレームの作成
    created_df = DataManipulationService.data_process()

    print(created_df.to_string())

    #StayHistoryに滞在情報を保存
    for _, row in created_df.iterrows():
        
        status = DataManipulationService.conf_status(row)

        #入院状況が判定できない場合（未入院？）
        if status is None:
            PutHistoryService.save_put_excluded(
                row=row,
                error_message="PUT対象となるステータスを判定できないためPUT対象外"
            )
            continue            
        
        admission_id = DataManipulationService.resolve_admission_id(row)

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

            StayHistoryService.save_stay_history(
                row=row,
                admission_id=admission_id,
            )

            json_data = DataManipulationService.create_json(
                row=row,
                admission_id=admission_id,
                status=status,
            )

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
    """
    return None
    


    # 実行処理 uv run python -m batch.main タスクスケジューラ用
"""
    try:
        response = PersApiService.post_request_data(json_data)

        PostHistoryService.save(
            post_type=PostHistory.PostType.AUTO,
            user=None,
            request_data=json_data,
            status_code=response.status_code,
            response_data=response.json(),
            is_success=True,
        )

    except Exception as e:
        PostHistoryService.save(
            post_type=PostHistory.PostType.AUTO,
            user=None,
            request_data=json_data,
            is_success=False,
            error_message=str(e),
        )
"""

if __name__ == "__main__":
    main()
