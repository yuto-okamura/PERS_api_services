from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
import uuid
from django.core.validators import RegexValidator


class CustomUserManager(BaseUserManager):
    use_in_migrations = True
    
    def create_user(self,employee_no,password=None,**extra_fields):
        if not employee_no:
            raise ValueError('The employee_no must be set')
        user = self.model(employee_no=employee_no,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self,employee_no,password=None,**extra_fields):
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        if extra_fields.get('is_staff',True) is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(employee_no,password,**extra_fields)
    
class ActiveManager(CustomUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
class CustomUsers(AbstractUser):
    username = None
    
    user_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ユーザーID"
    )
    employee_no = models.CharField(
        "職員番号",
        max_length=7,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^\d{7}$",
                message="職員番号は7桁の数値で登録してください"
            )
        ]
    )
    first_name = models.CharField(
        "名",
        max_length=20,
        blank=True,
    )
    last_name = models.CharField(
        "姓",
        max_length=20,
        blank=True,
    )
    first_name_kana = models.CharField(
        "メイ",
        max_length=20,
        blank=True,
    )
    last_name_kana = models.CharField(
        "セイ",
        max_length=20,
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
    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_users",
        verbose_name="作成者",
    )
    updated_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_users",
        verbose_name="更新者",
    )

    USERNAME_FIELD = 'employee_no'
    REQUIRED_FIELDS = []

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name}"

    @property
    def full_name_kana(self):
        return f"{self.last_name_kana} {self.first_name_kana}"

    class Meta:
        verbose_name = "ユーザー"
        verbose_name_plural = "ユーザー"
    
    def __str__(self):
        return f"{self.employee_no} {self.last_name} {self.first_name}"

    objects = ActiveManager()
    all_objects = CustomUserManager()

