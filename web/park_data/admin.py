from typing import Optional

from django.utils.translation import gettext_lazy as _
from django.contrib import admin, messages
from django.contrib.admin.decorators import register
from django.contrib.gis.admin import OSMGeoAdmin
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.contrib.gis.geos import Point
from django.db import models

from .models import *


def short_link(url: str, max_length=20) -> str:
    if "//" in url:
        url = url.split("//")[1]
    if len(url) >= max_length - 2:
        url = url[:max_length] + ".."
    return url


def location_decorator(point: Optional[Point]):
    if not point:
        return "-"
    lon, lat = point.tuple
    markup = f"{lon},{lat}"
    markup += (
        f""" <a href="https://nominatim.openstreetmap.org/ui/reverse.html"""
        f"""?lat={lat}&lon={lon}&zoom=16" title="osm nominatim reverse search (street level)" target="_blank">N</a>"""
    )
    return mark_safe(markup)


@register(ParkingPool)
class ParkingPoolAdmin(admin.ModelAdmin):
    list_display = (
        "pool_id",
        "name",
        "num_lots_decorator",
        "public_url_decorator",
        "source_url_decorator",
        "date_created",
        "date_updated",
    )

    def public_url_decorator(self, model: ParkingPool):
        if not model.public_url:
            return "-"
        return mark_safe(format_html(
            """<a href="{}">{}</a>""", model.public_url, short_link(model.public_url)
        ))
    public_url_decorator.short_description = _("Public website")
    public_url_decorator.admin_order_field = "public_url"

    def source_url_decorator(self, model: ParkingPool):
        if not model.source_url:
            return "-"
        return mark_safe(format_html(
            """<a href="{}">{}</a>""", model.source_url, short_link(model.source_url)
        ))
    public_url_decorator.short_description = _("Data website")
    public_url_decorator.admin_order_field = "source_url"

    def num_lots_decorator(self, model: ParkingPool):
        return model.num_lots
    num_lots_decorator.short_description = _("Lots count")
    num_lots_decorator.admin_order_field = "num_lots"

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .annotate(num_lots=models.Count("parkinglot"))
        )


@register(ParkingLot)
class ParkingLotAdmin(OSMGeoAdmin):
    list_display = (
        "lot_id",
        "pool",
        "location",
        "name",
        "type",
        "max_capacity",
        "num_snapshots_decorator",
        "latest_timestamp",
        "latest_status",
        "latest_num_free",
        "public_url_decorator",
        "source_url_decorator",
        "location_decorator",
        "date_created",
        "date_updated",
    )
    search_fields = ["lot_id", "name", "address"]
    ordering = ("lot_id", )

    def public_url_decorator(self, model: ParkingLot):
        if not model.public_url:
            return "-"
        return mark_safe(format_html(
            """<a href="{}">{}</a>""", model.public_url, short_link(model.public_url)
        ))
    public_url_decorator.short_description = _("Public website")
    public_url_decorator.admin_order_field = "public_url"

    def source_url_decorator(self, model: ParkingLot):
        if not model.source_url:
            return "-"
        return mark_safe(format_html(
            """<a href="{}">{}</a>""", model.source_url, short_link(model.source_url)
        ))
    source_url_decorator.short_description = _("Data website")
    source_url_decorator.admin_order_field = "source_url"

    def latest_timestamp(self, model: ParkingLot):
        if not model.latest_data:
            return "-"
        return model.latest_data.timestamp
    latest_timestamp.short_description = _("Latest timestamp")
    latest_timestamp.admin_order_field = "latest_data__timestamp"

    def latest_status(self, model: ParkingLot):
        if not model.latest_data:
            return "-"
        return model.latest_data.status
    latest_status.short_description = _("Latest status")
    latest_status.admin_order_field = "latest_data__status"

    def latest_num_free(self, model: ParkingLot):
        if not model.latest_data:
            return "-"
        return model.latest_data.num_free
    latest_num_free.short_description = _("Latest num_free")
    latest_num_free.admin_order_field = "latest_data__num_free"

    def location_decorator(self, model: ParkingLot) -> str:
        return location_decorator(model.geo_point)
    location_decorator.short_description = _("Location")
    location_decorator.admin_order_field = "geo_point"

    def num_snapshots_decorator(self, model: ParkingPool):
        return model.num_snapshots
    num_snapshots_decorator.short_description = _("Snapshots count")
    num_snapshots_decorator.admin_order_field = "num_snapshots"

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
                .annotate(num_snapshots=models.Count("parkingdata"))
        )


@register(ParkingData)
class ParkingDataAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = (
        "timestamp",
        "lot_decorator",
        "status",
        "capacity",
        "num_free",
        "num_occupied",
        "percent_free",
    )
    list_filter = ("lot", )
    ordering = ("-timestamp", "lot__lot_id")

    def lot_decorator(self, model: ParkingData) -> str:
        text = str(model.lot)
        if model.lot.public_url:
            return mark_safe(format_html(
                """{} (<a href="{}">{}</a>)""", text, model.lot.public_url, short_link(model.lot.public_url)
            ))
        return text
    lot_decorator.short_description = _("Parking lot")
    lot_decorator.admin_order_field = "lot__id"

