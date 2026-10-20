import json
import pandas as pd
from .api_client_service import PersApiService
from pathlib import Path
from datetime import datetime, date
from django.utils import timezone
from integration.models import (
    Ward,
    Room,
    Bed,
)
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

        api_df["patient_id"] = (
            api_df["patient_id"]
            .astype("string")
            .str.zfill(10)
        )

        api_df["birthDate"] = pd.to_datetime(
            api_df["birthDate"],
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

        return api_df

    @staticmethod
    def get_manual_put_row(patient_id):
        api_df = DataManipulationService.load_api_data()
        
        if api_df[api_df["patient_id"] == patient_id].empty:
            return None

        all_patient_df = DataManipulationService.create_all_patient_df()

        merged_df = DataManipulationService.create_merged_df(
            api_df=api_df,
            all_patient_df=all_patient_df,
        )

        target_df = merged_df[merged_df["patient_id"] == patient_id]

        if target_df.empty:
            return None

        return target_df.iloc[0]

    #最新のファイルの取得
    @staticmethod
    def get_latest_data_file(file_name, data_dir=None):
        if data_dir is None:
            data_dir = DATA_DIR
        
        files = list(DATA_DIR.glob(f"{file_name}_*.csv"))

        if not files:
            raise FileNotFoundError(
                f"csvファイルが見つかりません： {DATA_DIR}"
            )
        
        return max(files, key=lambda file: file.stem.split("_")[-1])
    
    @staticmethod
    def load_emr_data(
        patient_file_path=None,
        discharge_file_path=None,
    ):

        if patient_file_path is None:
            patient_file_path = DataManipulationService.get_latest_data_file(
                "current_patient"
            )

        stayed_at = timezone.make_aware(
            datetime.strptime(
            patient_file_path.stem.split("_")[-1],
            "%Y%m%d%H%M%S"
            )
        ).replace(
            minute=0,
            second=0,
            microsecond=0,            
        )

        patient_df = pd.read_csv(
            patient_file_path,
            dtype={
                "patient_id": str,
                "birthDate": str,
                "bed_no": str,
            },
        )

        if discharge_file_path is None:
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
            .astype("string")
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
        )

        patient_df["stayed_at"] = stayed_at

        discharge_df["patient_id"] = (
            discharge_df["patient_id"]
            .astype("string")
            .str.zfill(10)
        )
        
        discharge_df["dischargedAt"] = pd.to_datetime(
            discharge_df["dischargedAt"],
            errors="coerce",
        )

        emr_df = patient_df.merge(
            discharge_df,
            on="patient_id",
            how="left",
        )
        
        return emr_df

    @staticmethod
    def load_emr_patient_data(patient_file_path=None):

        if patient_file_path is None:
            patient_file_path = DataManipulationService.get_latest_data_file(
                "current_patient"
            )

        stayed_at = timezone.make_aware(
            datetime.strptime(
            patient_file_path.stem.split("_")[-1],
            "%Y%m%d%H%M%S"
            )
        ).replace(
            minute=0,
            second=0,
            microsecond=0,            
        )        

        patient_df = pd.read_csv(
            patient_file_path,
            dtype={
                "patient_id": str,
                "birthDate": str,
                "bed_no": str,
            },
        )
        
        master_df = DataManipulationService.create_master_df()

        patient_df = patient_df.merge(
            master_df,
            left_on=["ward_code", "room_code", "bed_no"],
            right_on=["emr_id_ward", "emr_id_room", "emr_id_bed"],
            how="left",
        )

        patient_df["patient_id"] = (
            patient_df["patient_id"]
            .astype("string")
            .str.zfill(10)
        )

        patient_df["hospitalizedAt"] = pd.to_datetime(
            patient_df["hospitalizedAt"],
            format="%Y%m%d",
            errors="coerce",
        )

        patient_df["admission_id"] = patient_df.apply(
            DataManipulationService.set_admission_id,
            axis=1,
        )

        patient_df["birthDate"] = pd.to_datetime(
            patient_df["birthDate"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.date

        patient_df["stayed_at"] = stayed_at
        
        return patient_df

    @staticmethod
    def load_emr_discharge_data(discharge_file_path=None):

        if discharge_file_path is None:
            discharge_file_path = DataManipulationService.get_latest_data_file(
                "discharge"
            )

        try:
            discharge_df = pd.read_csv(discharge_file_path)

        except pd.errors.EmptyDataError:
            discharge_df = pd.DataFrame(
                columns=["patient_id", "dischargedAt"]
            )

        discharge_df["patient_id"] = (
            discharge_df["patient_id"]
            .astype(str)
            .str.zfill(10)
        )
        
        discharge_df["dischargedAt"] = pd.to_datetime(
            discharge_df["dischargedAt"],
            errors="coerce",
        )
        
        return discharge_df

    @staticmethod
    def load_emr_dataset(
        patient_file_path=None,
        discharge_file_path=None,
    ):

        patient_df = DataManipulationService.load_emr_patient_data(
            patient_file_path=patient_file_path,
        )

        discharge_df = DataManipulationService.load_emr_discharge_data(
            discharge_file_path=discharge_file_path,
        )
        
        return patient_df, discharge_df    

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
    def create_all_patient_df(
        patient_file_path=None,
        discharge_file_path=None,
    ):
        emr_df = DataManipulationService.load_emr_data(
            patient_file_path=patient_file_path,
            discharge_file_path=discharge_file_path,
        )
        
        master_df = DataManipulationService.create_master_df()
        
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

    @staticmethod
    def merge_api_patient_data(api_df, patient_df):
        merged_df = api_df.merge(
            patient_df,
            left_on="orderCode",
            right_on="order_code",
            how="left",
            suffixes=("_api", "_db"),
            validate="one_to_one",
            indicator=True,
        )
        
        return merged_df

    @staticmethod
    def create_json_request(
        *,
        patient_id, 
        admission_id, 
        status, 
        hospitalized_at, 
        discharged_at, 
        current_stay,
        patient_name_kana,
        birth_date, 
        events,
    ):
        
        data = {
            "id": admission_id,
            "status": status,
            "hospitalizedAt": DataManipulationService.to_json_value(
                hospitalized_at
            ),
            "dischargedAt": DataManipulationService.to_json_value(
                discharged_at,
            ),
            "ward": {
                "id": current_stay.ward_id,
                "name": current_stay.ward.name,
            } if current_stay is not None else None,
            "room": {
                "id": current_stay.room_id,
                "name": current_stay.room.name,                
            } if current_stay is not None else None,
            "bed": {
                "id": current_stay.bed_id,
                "name": current_stay.bed.bed_no,                
            } if current_stay is not None else None,
            "patient": {
                "id": patient_id,
                "fullNameKana": patient_name_kana,
                "birthDate": DataManipulationService.to_json_value(
                    birth_date,
                ),
            },
            "events": events,
        }

        return data

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
    def set_status(row):
        if pd.notna(row["discharged_at"]):
            return "discharged"
        
        return "hospitalized"

    @staticmethod
    def conf_status(row):
        order_status = row["orderStatus"]
        merge_status = row["_merge"]
        discharged_at = row["dischargedAt"]

        if order_status == "reserved" and merge_status == "both":
            return "hospitalized"

        if order_status == "ended":
            return "discharged"

        if order_status == "executing":
            if pd.isna(discharged_at):
                return "hospitalized"
            
            return "discharged"
        
        return None

    @staticmethod
    def create_discharged_json(row, admission_id):
        
        request_data = PutHistoryService.get_latest_successful_request(admission_id)

        if request_data is None:
            return None
        
        data = request_data.copy()
        
        data["status"] = "discharged"
        data["dischargedAt"] = DataManipulationService.to_json_value(
            row["admission_dischargedAt"]
        )

        #滞在情報はnullに変換
        data["ward"] = None
        data["room"] = None
        data["bed"] = None

        return data

    @staticmethod
    def to_json_value(value):
        if pd.isna(value):
            return None
        
        if isinstance(value, (pd.Timestamp, datetime)):
            if isinstance(value, (pd.Timestamp, datetime)):
                if timezone.is_aware(value):
                    value = timezone.localtime(value)
                
            return value.strftime("%Y-%m-%d %H:%M:%S")
        
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        
        return value

    @staticmethod
    def create_json(row, admission_id, status, events):

        data = {
            "id": admission_id,
            "status": status,
            "hospitalizedAt": DataManipulationService.to_json_value(row["hospitalizedAt"]),
            "dischargedAt": DataManipulationService.to_json_value(row["dischargedAt"]),
            "ward": {
                "id": DataManipulationService.to_json_value(row["ward_id"]),
                "name": DataManipulationService.to_json_value(row["ward_name"]),
            },
            "room": {
                "id": DataManipulationService.to_json_value(row["room_id"]),
                "name" : DataManipulationService.to_json_value(row["room_name"]),
            },
            "bed":{
                "id": DataManipulationService.to_json_value(row["bed_id"]),
                "name": DataManipulationService.to_json_value(row["bed_no_master"]),
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
    

        