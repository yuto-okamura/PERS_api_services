from django.contrib import admin

from .models import (
    Ward,
    Room,
    Bed,
)


class RoomInline(admin.TabularInline):
    model = Room
    extra = 1
    fields = (
        "id",
        "name",
        "is_price_difference",
        "is_active",
    )

class BedInline(admin.TabularInline):
    model = Bed
    extra = 1
    fields = (
        "id",
        "bed_no",
        "is_active",
    )

@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "is_active",
    )

    fields = (
        "id",
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
        "name",
        "is_price_difference",
        "is_active",
    )

    fields = (
        "id",
        "name",
        "is_price_difference",
        "is_active",
    )

    inlines = (
        BedInline,
    )
