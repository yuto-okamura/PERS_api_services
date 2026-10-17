from django.db import models
from django.conf import settings
from django.utils import timezone
from masters.models import (
    Ward,
    Room,
    Bed,
    PersResponseMaster,
)


class PutHistory(models.Model):
    class PutType(models.TextChoices):
        AUTO = "auto", "自動"
        MANUAL = "manual", "手動"
        
    id = models.BigAutoField(
        primary_key=True,
    )

    order_code = models.CharField(
        "オーダーコード",
        max_length=50,
        blank=True,
        default="",
        db_index=True,
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
        null=True,
        blank=True,
    )

    request_data = models.JSONField(
        "送信データ",
        null=True,
        blank=True,
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

    pers_response = models.ForeignKey(
        PersResponseMaster,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="PERSレスポンス",
    )

    is_communication_success = models.BooleanField(
        "通信成功",
        default=False,
    )

    is_integration_success = models.BooleanField(
        "連携成功",
        default=False,
    )

    is_put_target = models.BooleanField(
        "PUT対象",
        default=True,
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
        put_at = timezone.localtime(self.put_at)
        return f"{put_at:%Y-%m-%d %H:%M:%S} {self.get_put_type_display()}"

class StayHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    
    admission_id = models.CharField(
        "入院ID",
        max_length=20,
    )

    stayed_at = models.DateTimeField(
        "滞在日時",
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
        verbose_name="病室"
    )

    bed = models.ForeignKey(
        Bed,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="ベッド",
    )

    created_at = models.DateTimeField(
        "作成日時",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "滞在履歴"
        verbose_name_plural = "滞在履歴"
        ordering = ["-stayed_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["admission_id", "stayed_at"],
                name="unique_admission_stayed_at",
            ),
        ]

class ImportHistory(StayHistory):
    #Csv取込専用の管理画面用モデル
    
    class Meta:
        proxy = True,
        verbose_name = "Csv取込"
        verbose_name_plural = "Csv取込"

class Patient(models.Model):
    patient_id = models.CharField(
        "患者ID",
        max_length=10,
        db_index=True,
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
        unique=True,
        db_index=True,
    )

    order_code = models.CharField(
        "オーダーコード",
        max_length=20,
        null=True,
        blank=True,
    )

    birth_date = models.DateField(
        "生年月日"
    )

    hospitalized_at = models.DateTimeField(
        "入院日",
    )

    discharged_at = models.DateTimeField(
        "退院日",
        null=True,
        blank=True,
    )

    service_start_date = models.DateField(
        "サービス利用開始日",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        "作成日時",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "更新日時",
        auto_now=True,
    )

    class Meta:
        db_table = "patient"
        verbose_name = "利用者"
        verbose_name_plural = "利用者"
        ordering = ["-hospitalized_at"]

    def __str__(self):
        return f"{self.patient_id} {self.patient_name}"
