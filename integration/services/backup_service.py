import logging
import sqlite3
import tempfile
from pathlib import Path
from contextlib import closing

import boto3
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("batch")

class BackupService:
    
    S3_BUCKET_NAME = "pers-api-backup-management"
    
    S3_PREFIX = "sqlite-backups"
    
    @staticmethod
    def create_and_upload_backup():
        
        db_path = Path(settings.DATABASES["default"]["NAME"])
        
        if not db_path.exists():
            raise FileNotFoundError(
                f"SQLiteデータベースが見つかりません：{db_path}"
            )

        timestamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"db_{timestamp}.sqlite3"
        s3_key = f"{BackupService.S3_PREFIX}/{backup_filename}"
        
        logger.info("SQLiteバックアップ開始")
        
        temp_path = None
        
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".sqlite3",
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)

            with sqlite3.connect(db_path) as source_conn:
                with closing(sqlite3.connect(temp_path)) as backup_conn:
                    source_conn.backup(backup_conn)
                    
            logger.info("SQLiteバックアップ作成完了")
            
            s3 = boto3.client(
                "s3",
                region_name = "ap-northeast-1",
            )

            s3.upload_file(
                str(temp_path),
                BackupService.S3_BUCKET_NAME,
                s3_key,
            )
            
            logger.info(
                "S3バックアップアップロード完了：s3://%s/%s",
                BackupService.S3_BUCKET_NAME,
                s3_key,
            )

            return s3_key
        
        except Exception:
            logger.exception("SQLiteバックアップ処理エラー")
            raise
        
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()
                logger.info("一時バックアップファイル削除完了")
