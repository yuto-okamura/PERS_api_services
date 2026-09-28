import csv

from django.core.management.base import BaseCommand
from masters.models import (
    Ward,
    Room,
    Bed,
)

PATH_WARD = "integration/input/ward_master.csv"
PATH_ROOM = "integration/input/room_master.csv"
PATH_BED = "integration/input/bed_master.csv"
#uv run python manage.py import_masters ターミナルで実行

class Command(BaseCommand):
    help = "マスタcsvを取り込む"

    def handle(self, *args, **options):
        self.import_wards()
        self.import_rooms()
        self.import_beds()
        
        self.stdout.write(
            self.style.SUCCESS("マスタの取り込み完了")
        )        

    def import_wards(self):
        with open(
            PATH_WARD,
            encoding="utf-8-sig",
            newline="",
        ) as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                Ward.objects.update_or_create(
                    id=row["id"],
                    defaults={
                        "emr_id": row["emr_id"],
                        "name": row["name"],
                        "is_active": row["is_active"].upper() == "TRUE",
                    },
                )
        
    def import_rooms(self):
        with open(
            PATH_ROOM,
            encoding="utf-8-sig",
            newline="",
        ) as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                ward = Ward.objects.get(id=row["ward_id"])
                
                Room.objects.update_or_create(
                    id=row["id"],
                    defaults={
                        "emr_id": row["emr_id"],
                        "name": row["name"],
                        "ward": ward,
                        "is_private_room": row["is_private_room"].upper() == "TRUE",
                        "is_active": row["is_active"].upper() == "TRUE",
                    },
                )
        
    def import_beds(self):
        with open(
            PATH_BED,
            encoding="utf-8-sig",
            newline="",
        ) as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                room = Room.objects.get(id=row["room_id"])
                
                Bed.objects.update_or_create(
                    id=row["id"],
                    defaults={
                        "emr_id": row["emr_id"],
                        "room": room,
                        "bed_no": row["bed_no"],
                        "is_active": row["is_active"].upper() == "TRUE",
                    },
                )
