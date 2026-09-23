import json
import pandas as pd
from .api_client_service import PersApiService
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("integration/input")
OUTPUT_DIR = Path("integration/output")

class DataManipulationService:
    
    #APIデータ取得
    @staticmethod
    def load_api_data():
        with open("integration/input/test.json", "r", encoding="utf-8") as f:
            json_data = json.load(f)
            
        api_df = pd.json_normalize(json_data["data"])

        api_df = api_df.rename(columns={
            "patient.id": "patient_id",
            "patient.fullName": "patient_fullName",
            "patient.fullNameKana": "patient_fullNameKana",
            "patient.birthDate": "patient_birthDate",
            "admission.id": "admission_id",
            "admission.hospitalizedAt": "admission_hospitalizedAt",
            "admission.dischargedAt": "admission_dischargedAt",
        })

        return api_df


    """
        json_data = PersApiService.get_request_data()
        
        api_df = pd.json_normalize(json_data["data"])

        api_df = api_df.rename(columns={
            "patient.id": "patient_id",
            "patient.fullName": "patient_fullName",
            "patient.fullNameKana": "patient_fullNameKana",
            "patient.birthDate": "patient_birthDate",
            "admission.id": "admission_id",
            "admission.hospitalizedAt": "admission_hospitalizedAt",
            "admission.dischargedAt": "admission_dischargedAt",
        })
    
        return api_df
    """

    #最新のファイルの取得
    @staticmethod
    def get_latest_data_file():
        # files = list(DATA_DIR.glob("test_input_*.csv"))
        
        patient_df = pd.read_csv("integration/input/test_input_patients.csv")
        
        discharge_df = pd.read_csv("integration/input/test_discharge_patients.csv")
        
        emr_df = patient_df.merge(
            discharge_df,
            on="patient_id",
            how="left",
        )
        
        return emr_df

    """
        if not files:
            raise FileNotFoundError(
                f"csvファイルが見つかりません： {DATA_DIR}"
            )
        
        return max(files, key=lambda file: file.stem.split("_")[-1])
    """


    """
    #最新のファイル読み込み
    @staticmethod
    def load_data():
        file_path = DataManipulationService.get_latest_data_file()
        return pd.read_csv(file_path)
    """


    @staticmethod
    def merge_data():
        api_df = DataManipulationService.load_api_data()
        emr_df = DataManipulationService.get_latest_data_file()

        merged_df = api_df.merge(
            emr_df,
            on="id",
            how="left",
            suffixes=("_api","_emr"),
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

    #JSONデータ作成
    @staticmethod
    def create_json(row, events):
        
        event_data = []

        i = 1

        for event in events:
            event_data.append({
                "id": f"{row['admission_id']}-{i:03d}",
                "admission_id": row["admission_id"],
                "type": "move",
                "ward": {
                    "id": event["ward_id"],
                    "name": event["ward_name"],
                },
                "room": {
                    "id": event["room_id"],
                    "name": event["room_name"],
                },
                "bed": {
                    "id": event["bed_id"],
                    "name": event["bed_no"],
                },
                "executedAt": event["executed_at"].strftime("%Y-%m-%d %H:%M:%S"),
                "isPriceDifference": {
                    event["executed_at"].strftime("%Y-%m-%d"): event["is_price_difference"],
                },
            })
            
            i = i + 1
        
        return {
            "id": row["admission_id"],
            "status": "move",
            "hospitalizedAt": row["admission_hospitalizedAt"],
            "dischargedAt": row["dischargedAt"],
            "ward": {
                "id": row["ward_id"],
                "name": row["ward_name"],
            },
            "room": {
                "id": row["room_id"],
                "name" : row["room_name"],
            },
            "bed":{
                "id": row["bed_id"],
                "name": row["bed_no"],
            },
            "patient": {
                "id": row["patient_id"],
                "fullNameKana": row["patient_fullNameKana"],
                "birthDate": row["patient_birthDate"],
            },
            "events": event_data,
        }

    #処理まとめ
    @staticmethod
    def data_process():
        merged_df = DataManipulationService.merge_data()
        
        json_data = DataManipulationService.create_json_data(merged_df)
        
        DataManipulationService.output_file(
            merged_df,
            json_data,
        )

        return json_data
        