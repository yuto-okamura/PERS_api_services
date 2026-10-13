import os
import json

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.batch_settings",
)

import django

django.setup()

from integration.services.api_client_service import PersApiService


def main():
    print("PERS API service batch started", flush=True)

    try:

        json_data = PersApiService.get_request_data()

        print("PERS API response", flush=True)
        print(json.dumps(
            json_data,
            ensure_ascii=False,
            indent=4,
        ))

    except Exception:

        import traceback
        traceback.print_exc()

    print("PERS API finished", flush=True)

if __name__ == "__main__":
    main()
