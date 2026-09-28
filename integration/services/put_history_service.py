from integration.models import PutHistory


class PutHistoryService:
    
    @staticmethod
    def save(
        *,
        row,
        admission_id,
        request_data,
        response,
        put_type=PutHistory.PutType.AUTO,
        user=None,
        error_message="",
    ):

        response_data = response.json()

        integration_success = (
            response.status_code == 200
            and response_data.get("data", {}).get("result") in {
                "applied",
                "unchanged,"
                } 
        )
        
        return PutHistory.objects.create(
            put_type=put_type,
            user=user,
            patient_id=row["patient_id"],
            patient_name=row["patient_fullName"],
            patient_name_kana=row["patient_fullNameKana"],
            admission_id=admission_id,
            request_data=request_data,
            status_code=response.status_code,
            response_data=response_data,
            is_communication_success=True,
            is_integration_success=integration_success,
            error_message=error_message,
        )

    @staticmethod
    def get_latest_successful_request(admission_id):
        history = (
            PutHistory.objects
            .filter(
                admission_id=admission_id,
                is_communication_success=True,
                is_integration_success=True,
            )
            .order_by("-put_at")
            .first()
        )

        if history is None:
            return None
        
        return history.request_data

    @staticmethod
    def save_put_excluded(*, row, error_message=""):
        return PutHistory.objects.create(
            put_type=PutHistory.PutType.AUTO,
            user=None,
            patient_id=row["patient_id"],
            patient_name=row["patient_fullName"],
            patient_name_kana=row["patient_fullNameKana"],
            is_communication_success=False,
            is_integration_success=False,
            is_put_target=False,
            error_message=error_message,
        )
