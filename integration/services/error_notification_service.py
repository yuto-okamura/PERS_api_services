import traceback
import boto3
from botocore.exceptions import ClientError

AWS_REGION = "ap-northeast-1"
FROM_ADDRESS = "dx-alert@sonodakai.or.jp"
TO_ADDRESS = "dx-dept@sonodakai.or.jp"


class ErrorNotificationService:
    
    @staticmethod
    def send_put_error_alert(errors):

        error_body = "\n\n".join(
            (
                f"{i}. オーダーコード: {result.order_code}\n"
                f"エラー内容: {result.error_message or '-'}"
            )
        for i, result in enumerate(errors, start=1)
        )
        

        try:
            
            ses = boto3.client("ses", region_name=AWS_REGION)

            response = ses.send_email(
                Source=FROM_ADDRESS,
                Destination={
                    "ToAddresses": [TO_ADDRESS],
                },
                Message={
                    "Subject": {
                        "Data": "PERS - ALERT",
                        "Charset": "UTF-8",
                    },
                    "Body": {
                        "Text": {
                            "Data": f"PUT処理で{len(errors)}件のエラーを確認 \n\n{error_body}",
                            "Charset": "UTF-8"
                        },
                    },
                },
            )

            print(
                f"SES accepted the message. MessageId={response['MessageId']}",
                flush=True,
            )
            
            return True

        except ClientError as exc:
            error = exc.response.get("Error", {})
            print(
                f"SES error: {error.get('Code')} - {error.get('Message')}",
                flush=True,
            )
            traceback.print_exc()
            return False

        except Exception:
            traceback.print_exc()
            return False
        