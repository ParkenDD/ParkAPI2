from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models

from .osm_base import OSMBase


class City(OSMBase):

    class Meta:
        verbose_name = _("City")
        verbose_name_plural = _("Cities")

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
