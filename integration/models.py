from django.db import models
from django.conf import settings

class PostHistory(models.Model):
    class PostType(models.TextChoices):
        AUTO = "auto", "自動"
        MANUAL = "manual", "手動"
        
    id = models.BigAutoField(
        primary_key=True,
    )
    
    post_type = models.CharField(
        "POST種別",
        max_length=10,
        choices=PostType.choices,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ユーザー",
    )
    
    request_data = models.JSONField(
        "送信データ",
    )

    missing_count = models.PositiveIntegerField(
        "突合できなかった件数",
        default=0,
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

    posted_at = models.DateTimeField(
        "POST日時",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "POST履歴"
        verbose_name_plural = "POST履歴"
        ordering = ["-posted_at"]
        
    def __str__(self):
        return f"{self.posted_at:%Y-%m-%d %H:%M:%S} {self.get_post_type_display()}"
