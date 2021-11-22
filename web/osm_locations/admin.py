from django.contrib import admin, messages
from django.contrib.admin.decorators import register
from django.contrib.gis.admin import OSMGeoAdmin

from .models import *


@register(OSMLocation)
class OSMLocationAdmin(OSMGeoAdmin):
    save_on_top = True

    list_display = (
        "osm_id",
        "osm_place_rank",
        "name",
        "osm_feature_type",
        "osm_linked_place",
        "osm_parent",
        "geo_point",
        "date_created",
        "date_updated",
    )

    fieldsets = (
        (None, {
            "fields": (
                ("osm_id", "osm_parent",),
                ("osm_place_rank", "osm_feature_type", "osm_linked_place"),
                ("name",),
            )
        }),
        (None, {
            "fields": (
                ("geo_point", "geo_polygon")
            )
        }),
        (None, {
            "fields": (
                ("osm_properties",),
            )
        }),
    )
