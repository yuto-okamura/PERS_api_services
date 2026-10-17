import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.batch_settings",
)

import django

django.setup()

from integration.services.data_loader_service import DataManipulationService
from integration.services.patient_service import PatientService

def main():

    #データフレームの作成
    print("[1] df作成開始")
    all_patient_df = DataManipulationService.create_all_patient_df()

    print(all_patient_df)

    print(f"取得件数: {len(all_patient_df)}")

    all_patient_df.to_csv(
        "debug_all_patient.csv",
        index=False,
        encoding="utf-8-sig",
    )

    success_count = 0
    error_count = 0

    for _, row in all_patient_df.iterrows():
        try:
            PatientService.save_patient(row)
            success_count += 1
            
        except Exception as e:
            error_count += 1
            print(
                f"[ERROR] patient_id={row.get('patient_id')}, "
                f"error={e}"
            )
            
    print(f"成功件数：{success_count}")
    print(f"エラー件数：{error_count}")

    return None

if __name__ == "__main__":
    main()
