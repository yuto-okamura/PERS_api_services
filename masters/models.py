from django.db import models


class Ward(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=20,
    )

    emr_id =models.CharField(
        "電カルID",
        max_length=10,
    )
    
    name = models.CharField(
        "病棟名称",
        max_length=10,
    )

    is_active = models.BooleanField(
        "有効",
        default=True,
    )
    
    class Meta:
        verbose_name = "病棟"
        verbose_name_plural = "病棟"
        ordering = ["name"]
        
    def __str__(self):
        return self.name

class Room(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=20,
    )

    emr_id =models.CharField(
        "電カルID",
        max_length=10,
    )

    ward = models.ForeignKey(
        Ward,
        on_delete=models.CASCADE,
        related_name="rooms",
        verbose_name="病棟"
    )

    name = models.CharField(
        "病室",
        max_length=10,
    )
    
    is_price_difference = models.BooleanField(
        "室料差額",
        default=False,
    )

    is_active = models.BooleanField(
        "有効",
        default=True,
    )

    class Meta:
        verbose_name = "病室"
        verbose_name_plural = "病室"
        ordering = ["name"]

    def __str__(self):
        return f"{self.ward.name} {self.name}号室"

class Bed(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=20,
    )

    emr_id =models.CharField(
        "電カルID",
        max_length=10,
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="beds",
        verbose_name="病室",
    )

    bed_no = models.CharField(
        "ベッド番号",
        max_length=10,
    )

    is_active = models.BooleanField(
        "有効",
        default=True,
    )

    class Meta:
        verbose_name = "ベッド番号"
        verbose_name_plural = "ベッド番号"
        ordering = ["bed_no"]

    def __str__(self):
        return f"{self.room.name}号室 - {self.bed_no}"
