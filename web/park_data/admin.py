from django.contrib import admin, messages
from django.contrib.admin.decorators import register
from django.contrib.gis.admin import OSMGeoAdmin
from .models import *


@register(ParkingPool)
class ParkingPoolAdmin(admin.ModelAdmin):
    list_display = (
        "pool_id",
        "name",
        "public_url",
        "source_url",
        "date_created",
        "date_updated",
    )



@register(ParkingLot)
class ParkingLotAdmin(OSMGeoAdmin):
    list_display = (
        "lot_id",
        "pool",
        "name",
        "type",
        "max_capacity",
        "public_url",
        "source_url",
        "date_created",
        "date_updated",
    )


@register(ParkingData)
class ParkingDataAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = (
        "timestamp",
        "lot",
        "status",
        "capacity",
        "num_free",
        "num_occupied",
        "percent_free",
    )
