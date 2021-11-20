from django.utils.translation import gettext_lazy as _
# from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db import models


class Country(models.Model):

    class Meta:
        verbose_name = _("Country")
        verbose_name_plural = _("Country")

    created_at = models.DateTimeField(
        verbose_name=_("Date of creation"),
        auto_now_add=True,
        db_index=True,
        editable=False,
    )

    iso_code = models.CharField(
        verbose_name=_("country code"),
        help_text=_("two-letter ISO 3166 country code"),
        max_length=64,
        db_index=True,
    )

    name = models.CharField(
        verbose_name=_("Name of country"),
        max_length=64,
        db_index=True,
    )

    geo_point = models.PointField(
        verbose_name=_("Geographic center of country"),
        null=True,
        db_index=True,
    )

    geo_polygon = models.PolygonField(
        verbose_name=_("Outline of country"),
        null=True,
        db_index=True,
    )

