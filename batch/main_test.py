import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

import django

django.setup()

from integration.services.data_loader_service import DataManipulationService
from integration.services.put_service import PutService
from integration.models import PutHistory

def main():

    #データフレームの作成
    print("[1] df作成開始")
    created_df = DataManipulationService.data_process()
    print("[1] df作成完了")
    
    print(created_df)

    #データフレーム対しての処理
    for _, row in created_df.iterrows():
        PutService.execute(
            row=row,
            put_type=PutHistory.PutType.AUTO,
        )

    return None

if __name__ == "__main__":
    main()
