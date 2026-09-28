import csv

from django.core.management.base import BaseCommand
from masters.models import PersResponseMaster


PATH_PERS_RESPONSE_MASTER = "integration/input/pers_response_master.csv"
#uv run python manage.py import_pers_response_masters ターミナルで実行

class Command(BaseCommand):  

    def import_pers_response_masters(self):
        with open(
            PATH_PERS_RESPONSE_MASTER,
            encoding="utf-8-sig",
            newline="",
        ) as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                PersResponseMaster.objects.update_or_create(
                    status_code=int(row["status_code"]),
                    result=row["result"],
                    defaults={
                        "name": row["name"],
                        "description": row["description"],
                        "action": row["action"],
                    },
                )