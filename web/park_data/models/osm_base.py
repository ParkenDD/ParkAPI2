from django.utils.translation import gettext_lazy as _
# from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db import models


class OSMBase(models.Model):

    class Meta:
        abstract = True

    osm_id = models.BigIntegerField(
        verbose_name=_("OpenStreetMap ID"),
        primary_key=True,
    )

    created_at = models.DateTimeField(
        verbose_name=_("Date of creation"),
        auto_now_add=True,
        db_index=True,
        editable=False,
    )

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=64,
        null=True,
        db_index=True,
    )

    geo_point = models.PointField(
        verbose_name=_("Geographic center"),
        null=True,
        db_index=True,
    )

    geo_polygon = models.PolygonField(
        verbose_name=_("Geographic outline"),
        null=True,
        db_index=True,
    )

