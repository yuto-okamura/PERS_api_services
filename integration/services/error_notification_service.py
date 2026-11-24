import traceback
import boto3
from dataclasses import dataclass
from botocore.exceptions import ClientError

AWS_REGION = "ap-northeast-1"
FROM_ADDRESS = "dx-alert@sonodakai.or.jp"
TO_ADDRESS = "dx-dept@sonodakai.or.jp"


@dataclass
class BatchError:
    key_value: str
    message: str
    category: str
    importance: str


class ErrorNotificationService:
    
    @staticmethod
    def send_error_alert(errors):

        error_body = "\n\n".join(
            (
                f"{i}. 重要度: {error.importance}\n"
                f"種別: {error.category}\n"
                f"識別値: {error.key_value}\n"
                f"メッセージ: {error.message or '-'}"
            )
        for i, error in enumerate(errors, start=1)
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
                            "Data": f"バッチ処理で{len(errors)}件のエラーを確認しました。\n\n{error_body}",
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
        
