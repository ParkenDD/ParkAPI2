from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models

from park_data.models import TimestampedGeoModel


class Location(TimestampedGeoModel):

    class Meta:
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")

    osm_id = models.CharField(
        verbose_name=_("OpenStreetMap ID"),
        help_text=_("The ID is prefixed with N, W or R (for Node, Way or Relation)"),
        max_length=32,
        unique=True,
        db_index=True,
    )

    geo_point = models.PointField(
        verbose_name=_("Geographic center"),
        null=True, blank=True,
        db_index=True,
    )

    geo_polygon = models.MultiPolygonField(
        verbose_name=_("Geographic outline"),
        null=True, blank=True,
        db_index=True,
    )

    osm_properties = models.JSONField(
        verbose_name=_("Properties from OSM"),
        null=True, blank=True,
    )

    city = models.CharField(
        verbose_name=_("City"),
        help_text=_("Native language name"),
        max_length=64,
        null=True, blank=True,
        db_index=True,
    )

    state = models.CharField(
        verbose_name=_("State"),
        help_text=_("Native language name"),
        max_length=64,
        null=True, blank=True,
        db_index=True,
    )

    country = models.CharField(
        verbose_name=_("Country"),
        help_text=_("Native language name"),
        max_length=64,
        null=True, blank=True,
        db_index=True,
    )

    country_code = models.CharField(
        verbose_name=_("Countrycode"),
        help_text=_("two-letter ISO 3166 lowercase"),
        max_length=2,
        null=True, blank=True,
        db_index=True,
    )

    def __str__(self):
        return f"{self.osm_id}/{self.city}"
