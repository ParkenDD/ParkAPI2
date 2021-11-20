from django.utils.translation import gettext_lazy as _
# from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db import models


class City(models.Model):

    class Meta:
        verbose_name = _("City")
        verbose_name_plural = _("Cities")

    created_at = models.DateTimeField(
        verbose_name=_("Date of creation"),
        auto_now_add=True,
        db_index=True,
        editable=False,
    )

    name = models.CharField(
        verbose_name=_("Name of city"),
        max_length=64,
        db_index=True,
    )

    country = models.ForeignKey(
        verbose_name=_("Country"),
        to="park_data.Country",
        on_delete=models.CASCADE,
        related_name="cities",  # Manager available at `Country.cities`
        db_index=True,
    )

    state = models.ForeignKey(
        verbose_name=_("State"),
        to="park_data.State",
        on_delete=models.CASCADE,
        related_name="cities",  # Manager available at `State.cities`
        null=True,
        db_index=True,
    )

    geo_point = models.PointField(
        verbose_name=_("Geographic center of city"),
        null=True,
        db_index=True,
    )

    geo_polygon = models.PolygonField(
        verbose_name=_("Outline of city"),
        null=True,
        db_index=True,
    )

