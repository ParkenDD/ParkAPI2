from django.contrib import admin
from django.contrib.admin.decorators import register

from .models import *


class OSMModelAdmin(admin.ModelAdmin):
    save_on_top = True

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Overridden to handle the 'Query Nominatim' button
        """
        if object_id and "_query_nominatim" in request.POST:
            model = self.model.objects.get(osm_id=object_id)
            model.update_from_nominatim_api()
            model.save()

            # this is quite hacky, but seems to work
            request.method = "GET"

        return super().change_view(request, object_id, form_url, extra_context)


@register(Country)
class CountryAdmin(OSMModelAdmin):
    list_display = (
        "created_at",
        "osm_id",
        "geo_point",
        "name",
        "iso_code",
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
