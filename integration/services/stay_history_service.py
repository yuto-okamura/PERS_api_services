from integration.models import StayHistory
from masters.models import (
    Ward,
    Room,
    Bed,
)

class StayHistoryService:
    
    @staticmethod
    def save_stay_history(row, admission_id):
        StayHistory.objects.update_or_create(
            admission_id=admission_id,
            stayed_at=row["stayed_at"],
            defaults={
                "ward_id": row["ward_id"],
                "room_id": row["room_id"],
                "bed_id": row["bed_id"],
            }
        )
        
        return None

    @staticmethod
    def create_events(admission_id):
        
        stays = (
            StayHistory.objects
            .filter(admission_id=admission_id)
            .select_related("ward", "room", "bed")
            .order_by("stayed_at")
        )

        events = []
        previous_bed_id = None
        event = None
        event_no = 0

        for stay in stays:
            if stay.bed_id != previous_bed_id:
                event_no += 1
                
                event = {
                    "id": f"{admission_id}-{event_no:03d}",
                    "admission_id": admission_id,
                    "type": (
                        "hospitalize" if previous_bed_id is None else "move"
                    ),
                    "ward": {
                        "id": stay.ward.id,
                        "name": stay.ward.name,
                    },
                    "room": {
                        "id": stay.room.id,
                        "name": stay.room.name,
                    },
                    "bed": {
                        "id": stay.bed.id,
                        "name": stay.bed.bed_no,
                    },
                    "executedAt": stay.stayed_at.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "isPriceDifference":{},
                }

                events.append(event)
                previous_bed_id = stay.bed_id
                
            event["isPriceDifference"][
                stay.stayed_at.strftime("%Y-%m-%d")
            ] = False

        return events


