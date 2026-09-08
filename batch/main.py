from integration.services.data_loader_service import DataManipulation


def main():
    print("PERS API service batch started")
    
    json_data = DataManipulation.data_process()

    # 実行処理 uv run python -m batch.main タスクスケジューラ用

if __name__ == "__main__":
    main()
