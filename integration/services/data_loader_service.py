import json
import pandas as pd
from .api_client_service import PersApiService
from pathlib import Path
from datetime import datetime
from django.utils import timezone
from integration.models import (
    Ward,
    Room,
    Bed,
)
from .stay_history_service import StayHistoryService
from .put_history_service import PutHistoryService

DATA_DIR = Path("integration/input")
OUTPUT_DIR = Path("integration/output")

class DataManipulationService:
    
    #APIデータ取得
    @staticmethod
    def load_api_data():

        json_data = PersApiService.get_request_data()
        
        api_df = pd.json_normalize(json_data["data"])

        api_df = api_df.rename(columns={
            "patient.id": "patient_id",
            "patient.fullName": "patient_fullName",
            "patient.fullNameKana": "patient_fullNameKana",
            "patient.birthDate": "birthDate",
            "admission.id": "pers_admission_id",
            "admission.hospitalizedAt": "admission_hospitalizedAt",
            "admission.dischargedAt": "admission_dischargedAt",
        })
    
        return api_df

    #最新のファイルの取得
    @staticmethod
    def get_latest_data_file(file_name):
        files = list(DATA_DIR.glob(f"{file_name}_*.csv"))

        if not files:
            raise FileNotFoundError(
                f"csvファイルが見つかりません： {DATA_DIR}"
            )
        
        return max(files, key=lambda file: file.stem.split("_")[-1])
    
    @staticmethod
    def load_emr_data():

        file_path = DataManipulationService.get_latest_data_file(
            "current_patient"
        )

        stayed_at = timezone.make_aware(
            datetime.strptime(
            file_path.stem.split("_")[-1],
            "%Y%m%d%H%M%S"
            )
        ).replace(
            minute=0,
            second=0,
            microsecond=0,            
        )

        patient_df = pd.read_csv(
            file_path,
            dtype={
                "patient_id": str,
                "birthDate": str,
                "bed_no": str,
            },
        )
        
        discharge_file_path = DataManipulationService.get_latest_data_file(
            "discharge"
        )
        
        try:
            discharge_df = pd.read_csv(discharge_file_path)

        except pd.errors.EmptyDataError:
            discharge_df = pd.DataFrame(
                columns=["patient_id", "dischargedAt"]
            )

        patient_df["patient_id"] = (
            patient_df["patient_id"]
            .str.zfill(10)
        )

        patient_df["birthDate"] = pd.to_datetime(
            patient_df["birthDate"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
        
        patient_df["hospitalizedAt"] = pd.to_datetime(
            patient_df["hospitalizedAt"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d %H:%M:%S")

        patient_df["stayed_at"] = stayed_at

        discharge_df["patient_id"] = (
            discharge_df["patient_id"]
            .astype(str)
            .str.zfill(10)
        )
        
        discharge_df["dischargedAt"] = pd.to_datetime(
            discharge_df["dischargedAt"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d %H:%M:%S")

        emr_df = patient_df.merge(
            discharge_df,
            on="patient_id",
            how="left",
        )
        
        return emr_df

    @staticmethod
    def merge_data():
        api_df = DataManipulationService.load_api_data()
        emr_df = DataManipulationService.load_emr_data()

        merged_df = api_df.merge(
            emr_df,
            on=["patient_id", "birthDate"],
            how="left",
            suffixes=("_api","_emr"),
            indicator=True,
        )

        return merged_df

    @staticmethod
    def create_master_df():
        ward_df = pd.DataFrame(
            Ward.objects.values("id","emr_id", "name")
        ).rename(columns={
            "id": "ward_id",
            "emr_id": "emr_id_ward",
            "name": "ward_name",
        })

        room_df = pd.DataFrame(
            Room.objects.values(
                "id", 
                "emr_id", 
                "ward_id",
                "name",
                "is_private_room",
            )
        ).rename(columns={
            "id": "room_id",
            "emr_id": "emr_id_room",
            "name": "room_name",
        })

        bed_df = pd.DataFrame(
            Bed.objects.values(
                "id",
                "emr_id",
                "room_id",
                "bed_no",
            )
        ).rename(columns={
            "id": "bed_id",
            "emr_id": "emr_id_bed",
            "bed_no": "bed_no_master",
        })

        master_df = ward_df.merge(
            room_df,
            on="ward_id",
        ).merge(
            bed_df,
            on="room_id",
        )

        return master_df

    @staticmethod
    def create_all_patient_df():
        emr_df = DataManipulationService.load_emr_data()
        print(emr_df)
        print(emr_df["bed_no"])
        
        master_df = DataManipulationService.create_master_df()
        print(master_df)
        
        all_patient_df = emr_df.merge(
            master_df,
            left_on=["ward_code", "room_code", "bed_no"],
            right_on=["emr_id_ward", "emr_id_room", "emr_id_bed"],
            how="left",
        )

        all_patient_df["admission_id"] = all_patient_df.apply(
            DataManipulationService.set_admission_id,
            axis=1,
        )

        return all_patient_df

    @staticmethod
    def merge_master_data(merged_df, master_df):
        merged_df = merged_df.merge(
            master_df,
            left_on=["ward_code", "room_code", "bed_no"],
            right_on=["emr_id_ward", "emr_id_room", "emr_id_bed"],
            how="left",
        )

        return merged_df

    @staticmethod
    def create_merged_df(api_df, all_patient_df):
        merged_df = api_df.merge(
            all_patient_df,
            on=["patient_id", "birthDate"],
            how="left",
            suffixes=("_api","_emr"),
            indicator=True,
        )

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
    def resolve_admission_id(row):
        merge_status = row["_merge"]
        
        if pd.notna(row["admission_id"]):
            admission_id = str(row["admission_id"])
            parts = admission_id.split("-")
            
            #PERS_APIのadmission_idの書式が正しい場合は採用
            if (
                len(parts) == 2
                and len(parts[0]) == 10
                and len(parts[1]) == 8
                and parts[0].isdigit()
                and parts[1].isdigit()
            ):
                return admission_id

        
        if merge_status == "both":
            if pd.notna(row["hospitalizedAt"]):
                hospitalized_at = pd.to_datetime(row["hospitalizedAt"])
                return f"{row['patient_id']}-{hospitalized_at:%Y%m%d}"

        return None

    @staticmethod
    def set_admission_id(row):
        hospitalized_at = pd.to_datetime(row["hospitalizedAt"])
        admission_id = f"{row['patient_id']}-{hospitalized_at:%Y%m%d}"

        return admission_id


    @staticmethod
    def conf_status(row):
        order_status = row["orderStatus"]
        merge_status = row["_merge"]
        discharged_at = row["dischargedAt"]

        status = None

        if order_status == "reserved" and merge_status == "both":
            status = "hospitalized"

        elif order_status == "executing":
            if pd.isna(discharged_at):
                status = "hospitalized"
            else:
                discharged_date = pd.to_datetime(discharged_at).date()
                
                if discharged_date < timezone.localdate():
                    status = "discharged"
                else:
                    status = "hospitalized"
        return status

    @staticmethod
    def create_discharged_json(row, admission_id):
        
        request_data = PutHistoryService.get_latest_successful_request(admission_id)

        if request_data is None:
            return None
        
        data = request_data.copy()
        
        data["status"] = "discharged"
        data["dischargedAt"] = row["dischargedAt"]

        return data

    @staticmethod
    def create_json(row, admission_id, status):

        events = StayHistoryService.create_events(admission_id)

        data = {
            "id": admission_id,
            "status": status,
            "hospitalizedAt": row["hospitalizedAt"],
            "dischargedAt": (
                row["dischargedAt"] if pd.notna(row["dischargedAt"]) else None
            ),
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
                "name": row["bed_no_master"],
            },
            "patient": {
                "id": row["patient_id"],
                "fullNameKana": row["patient_fullNameKana"],
                "birthDate": row["birthDate"],
            },
            "events": events,            
        }

        return data

    #処理まとめ
    @staticmethod
    def data_process():
        merged_df = DataManipulationService.merge_data()
        
        master_df = DataManipulationService.create_master_df()
        
        completed_df = DataManipulationService.merge_master_data(merged_df,master_df)
        
        #events = ""
        #json_data = DataManipulationService.create_json(merged_df,events)
        
        """
        DataManipulationService.output_file(
            merged_df,
            json_data,
        )
        """
        return completed_df
        