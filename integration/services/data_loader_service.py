import json
import pandas as pd
from .api_client_service import PersApiService
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("integration/input")
OUTPUT_DIR = Path("integration/output")

class DataManipulation:
    
    #APIデータ取得
    @staticmethod
    def load_api_data():
        return pd.read_csv("integration/input/test_api.csv")
    
        #return PersApiService.get_request_data()

    #最新のファイルの取得
    @staticmethod
    def get_latest_data_file():
        files = list(DATA_DIR.glob("test_input_*.csv"))
        
        if not files:
            raise FileNotFoundError(
                f"csvファイルが見つかりません： {DATA_DIR}"
            )
        
        return max(files, key=lambda file: file.stem.split("_")[-1])

    #最新のファイル読み込み
    @staticmethod
    def load_data():
        file_path = DataManipulation.get_latest_data_file()
        return pd.read_csv(file_path)

    @staticmethod
    def merge_data():
        api_df = DataManipulation.load_api_data()
        patient_df = DataManipulation.load_data()

        merged_df = api_df.merge(
            patient_df,
            on="id",
            how="left",
        )

        # unmatched_dataの取得
        missing_df = merged_df[merged_df["score"].isna()]

        print(missing_df)

        return merged_df

    @staticmethod
    def output_file(merged_df, json_data):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")        

        csv_path = OUTPUT_DIR / f"merged_data_{timestamp}.csv"
        json_path = OUTPUT_DIR / f"merged_data_{timestamp}.json"

        merged_df.fillna("").to_csv(
            csv_path,
            index=False,
            encoding="utf-8-sig",
        )

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(
                json_data,
                f,
                ensure_ascii=False,
                indent=2,
            )
        
    #JSONデータ作成
    @staticmethod
    def create_json_data(merged_df):
        return merged_df.to_dict(orient="records")

    #処理まとめ
    @staticmethod
    def data_process():
        merged_df = DataManipulation.merge_data()
        
        json_data = DataManipulation.create_json_data(merged_df)
        
        DataManipulation.output_file(
            merged_df,
            json_data,
        )

        return json_data
        