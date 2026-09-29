import boto3
import requests

HOST_NAME = "dev.medical-system.perspay.jp"
HOSPITAL_CODE = "Lb3yq7RPBmKx1Y25pWngVlX8K19M0adjJvDN9oLr4wkEQZeOz6"

PERS_API_BASE_URL = f"https://{HOST_NAME}/api/v1/medical-system"
PERS_API_KEY_PARAMETER = "/pers/api/api-key"
PERS_API_URL = f"{PERS_API_BASE_URL}/hospitals/{HOSPITAL_CODE}/orders"

class PersApiService:

    #APIキー取得
    @staticmethod
    def get_api_key():
        ssm = boto3.client(
            "ssm",
            region_name="ap-northeast-1",
        )
        
        response = ssm.get_parameter(
            Name=PERS_API_KEY_PARAMETER,
            WithDecryption=True,
        )

        return response["Parameter"]["Value"]

    #RequestAPI
    @staticmethod
    def get_request_data():
        api_key = PersApiService.get_api_key()
        
        response = requests.get(
            PERS_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
            timeout=30,
        )

        response.raise_for_status()
        
        return response.json()

    #PutAPI
    @staticmethod
    def put_request_data(json_data, order_code):
        api_key = PersApiService.get_api_key()

        request_url = f"{PERS_API_URL}/{order_code}/admission"

        response = requests.put(
            request_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=json_data,
            timeout=30,
        )
        
        return response
