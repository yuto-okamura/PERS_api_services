from integration.models import PutHistory


class PutHistoryService:
    
    @staticmethod
    def save(
        *,
        post_type,
        user,
        request_data,
        status_code=None,
        response_data=None,
        is_success=False,
        error_message="",
    ):
        return PutHistory.objects.create(
            post_type=post_type,
            user=user,
            request_data=request_data,
            status_code=status_code,
            response_data=response_data,
            is_success=is_success,
            error_message=error_message,
        )


