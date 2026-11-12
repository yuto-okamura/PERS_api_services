import os
import traceback

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

import django

django.setup()

import boto3
from botocore.exceptions import ClientError

AWS_REGION = "ap-northeast-1"
FROM_ADDRESS = "alert@sonodakai.or.jp"
TO_ADDRESS = "dx-dept@sonodakai.or.jp"

def main():

    print("SES test started", flush=True)
    
    try:
        
        ses = boto3.client("ses", region_name=AWS_REGION)

        response = ses.send_email(
            Source=FROM_ADDRESS,
            Destination={
                "ToAddresses": [TO_ADDRESS],
            },
            Message={
                "Subject": {
                    "Data": "SES送信テスト",
                    "Charset": "UTF-8",
                },
                "Body": {
                    "Text": {
                        "Data": "EC2からの Amazon SES の送信テスト",
                        "Charset": "UTF-8"
                    },
                },
            },
        )

        print(
            f"SES accepted the message. MessageId={response['MessageId']}",
            flush=True,
        )

    except ClientError as exc:
        error = exc.response.get("Error", {})
        print(
            f"SES error: {error.get('Code')} - {error.get('Message')}",
            flush=True,
        )
        traceback.print_exc()

    except Exception:
        traceback.print_exc()
        
    print("SES test finished", flush=True)

if __name__ == "__main__":
    main()
