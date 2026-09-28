from django.contrib import admin

from .models import (
    Ward,
    Room,
    Bed,
    PersResponseMaster,
)


class RoomInline(admin.TabularInline):
    model = Room
    extra = 1
    fields = (
        "id",
        "emr_id",
        "name",
        "is_private_room",
        "is_active",
    )

class BedInline(admin.TabularInline):
    model = Bed
    extra = 1
    fields = (
        "id",
        "emr_id",
        "bed_no",
        "is_active",
    )

@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "emr_id",
        "name",
        "is_active",
    )

    fields = (
        "id",
        "emr_id",
        "name",
        "is_active",
    )

    inlines = (
        RoomInline,
    )

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "emr_id",
        "name",
        "is_private_room",
        "is_active",
    )

    fields = (
        "id",
        "emr_id",
        "name",
        "is_private_room",
        "is_active",
    )

    inlines = (
        BedInline,
    )

@admin.register(PersResponseMaster)
class PersResponseMasterAdmin(admin.ModelAdmin):
    list_display = (
        "status_code",
        "name",
        "description",
        "action",
    )

    fields = (
        "status_code",
        "name",
        "result",
        "description",
        "action",
    )
