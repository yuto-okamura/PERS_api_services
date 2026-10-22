import boto3
import requests
import logging


HOST_NAME = "medical-system.perspay.jp"
HOSPITAL_CODE = "JozjJWE21nqke7KYpBQO0DVbJ67bM5rvLa3yP9GNdx46RZlAXw"

PERS_API_BASE_URL = f"https://{HOST_NAME}/api/v1/medical-system"
PERS_API_KEY_PARAMETER = "/pers/api/api-key"
PERS_API_URL = f"{PERS_API_BASE_URL}/hospitals/{HOSPITAL_CODE}/orders"

logger = logging.getLogger("pers_api")

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
        try:
            api_key = PersApiService.get_api_key()
            
            response = requests.get(
                PERS_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json",
                },
                timeout=30,
            )

            print("APIステータスコード：", response.status_code)
            print("APIレスポンスヘッダー：", response.headers)
            print("APIレスポンス本文", response.text[:1000])

            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.HTTPError:
            logger.exception(
                "PERS API GET失敗：HTTPエラー status_code=%s, body=%s",
                response.status_code,
                response.text[:1000],
            )
            raise
        
        except requests.exceptions.RequestException:
            logger.exception("PERS API GET失敗：通信エラー")
            raise
        
        except ValueError:
            logger.exception("PERS API GET失敗：JSON解析エラー")
            raise
        
        except Exception:
            logger.exception("PERS API GET失敗：予期しないエラー")
            raise

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
