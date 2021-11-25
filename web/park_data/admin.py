from django.utils.translation import gettext_lazy as _
from django.contrib import admin, messages
from django.contrib.admin.decorators import register
from django.contrib.gis.admin import OSMGeoAdmin
from django.utils.safestring import mark_safe
from django.utils.html import format_html

from .models import *


def short_link(url: str, max_length=20) -> str:
    if "//" in url:
        url = url.split("//")[1]
    if len(url) >= max_length - 2:
        url = url[:max_length] + ".."
    return url


@register(ParkingPool)
class ParkingPoolAdmin(admin.ModelAdmin):
    list_display = (
        "pool_id",
        "name",
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


@register(ParkingLot)
class ParkingLotAdmin(OSMGeoAdmin):
    list_display = (
        "lot_id",
        "pool",
        "name",
        "type",
        "max_capacity",
        "public_url_decorator",
        "source_url_decorator",
        "date_created",
        "date_updated",
    )

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
    public_url_decorator.short_description = _("Data website")
    public_url_decorator.admin_order_field = "source_url"


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

    def lot_decorator(self, model: ParkingData) -> str:
        text = str(model.lot)
        if model.lot.public_url:
            return mark_safe(format_html(
                """{} (<a href="{}">{}</a>)""", text, model.lot.public_url, short_link(model.lot.public_url)
            ))
        return text
    lot_decorator.short_description = _("Parking lot")
    lot_decorator.admin_order_field = "lot__id"
