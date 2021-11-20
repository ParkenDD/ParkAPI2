from django.utils.translation import gettext_lazy as _
# from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db import models


class State(models.Model):

    class Meta:
        verbose_name = _("State")
        verbose_name_plural = _("States")

    created_at = models.DateTimeField(
        verbose_name=_("Date of creation"),
        auto_now_add=True,
        db_index=True,
        editable=False,
    )

    name = models.CharField(
        verbose_name=_("Name of state"),
        max_length=64,
        db_index=True,
        unique=True,
    )

    country = models.ForeignKey(
        verbose_name=_("Country"),
        to="park_data.Country",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="states",  # Manager available at `Country.states`
    )

    geo_point = models.PointField(
        verbose_name=_("Geographic center of state"),
        null=True,
        db_index=True,
    )

    geo_polygon = models.PolygonField(
        verbose_name=_("Outline of state"),
        null=True,
        db_index=True,
    )

