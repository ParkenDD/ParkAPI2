from django.contrib import admin
from django.contrib.admin.decorators import register
from django.contrib.gis.admin import OSMGeoAdmin
from .models import *


class OSMModelAdmin(OSMGeoAdmin):
    save_on_top = True

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Overridden to handle the 'query nominatim' button
        """
        query_nominatim = "_query_nominatim" in request.POST
        if query_nominatim:
            # change from our special button to the 'save and continue' button
            qdict = request.POST.copy()
            qdict.pop("_query_nominatim")
            qdict["_continue"] = 1
            request.POST = qdict

        # save model
        response = super().change_view(request, object_id, form_url, extra_context)

        if object_id and query_nominatim:
            model = self.model.objects.get(id=object_id)
            model.update_from_nominatim_api()
            model.save()

        return response


@register(Country)
class CountryAdmin(OSMModelAdmin):
    list_display = (
        "created_at",
        "osm_id",
        "geo_point",
        "name",
        "iso_code",
    )

    fieldsets = (
        (None, {
            "fields": (
                ("osm_id",),
                ("name", "iso_code"),
            )
        }),
        (None, {
            "fields": (
                ("geo_point", "geo_polygon")
            )
        })
    )


@register(State)
class StateAdmin(OSMModelAdmin):
    list_display = (
        "created_at",
        "osm_id",
        "geo_point",
        "name",
        "country",
    )

    fieldsets = (
        (None, {
            "fields": (
                ("osm_id",),
                ("name", "country"),
            )
        }),
        (None, {
            "fields": (
                ("geo_point", "geo_polygon")
            )
        })
    )


@register(City)
class CityAdmin(OSMModelAdmin):
    list_display = (
        "created_at",
        "osm_id",
        "geo_point",
        "name",
        "state",
        "country",
    )

    fieldsets = (
        (None, {
            "fields": (
                ("osm_id",),
                ("name", "country", "state"),
            )
        }),
        (None, {
            "fields": (
                ("geo_point", "geo_polygon")
            )
        })
    )


@register(ParkingLot)
class ParkingLotAdmin(OSMModelAdmin):
    list_display = (
        "created_at",
        "osm_id",
        "geo_point",
        "name",
        "city",
        "lot_type",
        "max_num_total",
    )

    fields = (
        "lot_id",
        "city",
        "name",
        "lot_type",
        "max_num_total",
        "osm_id",
        "address",
        "public_url",
        "geo_point",
        "geo_polygon",
    )


@register(ParkingData)
class ParkingDataAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = (
        "timestamp",
        "lot",
        "status",
        "num_free",
        "num_total",
        "num_occupied",
        "percent_free",
    )
