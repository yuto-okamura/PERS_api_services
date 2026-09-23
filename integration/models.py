from django.db import models
from django.conf import settings
from masters.models import (
    Ward,
    Room,
    Bed,
)


class PutHistory(models.Model):
    class PutType(models.TextChoices):
        AUTO = "auto", "自動"
        MANUAL = "manual", "手動"
        
    id = models.BigAutoField(
        primary_key=True,
    )
    
    put_type = models.CharField(
        "PUT種別",
        max_length=10,
        choices=PutType.choices,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ユーザー",
    )

    patient_id = models.CharField(
        "患者ID",
        max_length=20,
    )

    patient_name = models.CharField(
        "患者氏名",
        max_length=50,
    )

    patient_name_kana = models.CharField(
        "患者氏名カナ",
        max_length=50,
    )
    
    admission_id = models.CharField(
        "入院ID",
        max_length=20,
    )

    ward = models.ForeignKey(
        Ward,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="病棟",
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="put_histories",
        verbose_name="病室",
    )

    bed = models.ForeignKey(
        Bed,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="ベッド番号",
    )

    request_data = models.JSONField(
        "送信データ",
    )

    status_code = models.PositiveIntegerField(
        "ステータスコード",
        null=True,
        blank=True,
    )

    response_data = models.JSONField(
        "レスポンス",
        null=True,
        blank=True,
    )

    is_success = models.BooleanField(
        "成功",
        default=False,
    )

    error_message = models.TextField(
        "エラー内容",
        blank=True,
    )

    put_at = models.DateTimeField(
        "PUT日時",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "PUT履歴"
        verbose_name_plural = "PUT履歴"
        ordering = ["-put_at"]
        
    def __str__(self):
        return f"{self.put_at:%Y-%m-%d %H:%M:%S} {self.get_put_type_display()}"
