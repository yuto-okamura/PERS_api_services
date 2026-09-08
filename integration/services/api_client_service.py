import boto3
import requests

PERS_API_URL = "https://api"
PERS_API_KEY_PARAMETER = "/pers/api/api-key"

class PersApiService:

    #APIキー取得
    @staticmethod
    def get_api_key():
        ssm = boto3.client(
            "ssm",
            region_name="ap-northeast",
        )
        
        responce = ssm.get_parameter(
            Name=PERS_API_KEY_PARAMETER,
            WithDecryption=True,
        )

        return responce["Parameter"]["Value"]

    #RequestAPI
    @staticmethod
    def get_request_data():
        api_key = PersApiService.get_api_key()
        
        responce = requests.get(
            PERS_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            timeout=30,
        )

        responce.raise_for_status()
        
        return responce.json()

    #PostAPI
    @staticmethod
    def post_request_data(json_data):
        api_key = PersApiService.get_api_key()
        
        responce = requests.post(
            PERS_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=json_data,
            timeout=30,
        )

        responce.raise_for_status()
        
        return responce.json()
