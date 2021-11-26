from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from django.contrib.gis.db.models import functions as F
from rest_framework import serializers, viewsets, filters
from rest_framework.compat import coreapi, coreschema, distinct


class SpatialFilter(filters.BaseFilterBackend):

    class DEFAULTS:
        radius = "100"

    def get_params(self, request) -> dict:
        location = request.GET.get("location")
        radius = request.GET.get("radius") or self.DEFAULTS.radius

        params = {
            "point": None,
            "distance": None,
        }

        if location is not None:
            try:
                lon, lat = tuple(float(l) for l in location.split(","))
                params["point"] = Point(lon, lat)
            except:
                raise serializers.ValidationError(
                    f"'position' must be two comma-separated float values"
                )

        try:
            params["distance"] = Distance(km=radius)
        except:
            raise serializers.ValidationError(
                f"'radius' must be a float value"
            )

        return params

    def filter_queryset(self, request, queryset, view):
        params = self.get_params(request)
        if params["point"] is None:
            return queryset
        qset = queryset.filter(geo_point__distance_lte=(params["point"], params["distance"]))

        qset = (
            qset
            .annotate(distance=F.Distance('geo_point', params["point"]))
            .order_by("distance")
        )
        return qset

    def get_schema_fields(self, view):
        assert coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        assert coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'
        return [
            coreapi.Field(
                name="location",
                required=False,
                location='query',
                schema=coreschema.String(
                    title=force_str(_("location")),
                    description=force_str(_("comma-separated longitude and latitude")),
                )
            ),
            coreapi.Field(
                name="radius",
                required=False,
                location='query',
                schema=coreschema.Number(
                    title=force_str(_("radius")),
                    description=force_str(_("Maximum radius around location in kilometers")),
                    default=self.DEFAULTS.radius,
                )
            ),
        ]
