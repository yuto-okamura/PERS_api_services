import os
import logging

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.batch_settings",
)

import django

django.setup()

from integration.services.backup_service import BackupService

logger = logging.getLogger("batch")

def main():
    logging.info("SQLiteバックアップバッチ開始")
    
    try:
        s3_key = BackupService.create_and_upload_backup()
        
        logger.info(
            "SQLiteバックアップバッチ正常終了：%s",
            s3_key,
        )

    except Exception:
        logger.exception("SQLiteバックアップバッチ異常終了")
        raise
    
if __name__ == "__main__":
    main()
    