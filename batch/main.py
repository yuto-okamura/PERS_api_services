import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

import django

django.setup()

from integration.services.data_loader_service import DataManipulationService
from integration.services.api_client_service import PersApiService
from integration.services.post_history_service import PostHistoryService
from integration.models import PostHistory

def main():
    print("PERS API service batch started")
    
    json_data = DataManipulationService.data_process()

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
