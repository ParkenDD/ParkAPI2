from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models

from .osm_base import OSMBase


class State(OSMBase):

    class Meta:
        verbose_name = _("State")
        verbose_name_plural = _("States")

    country = models.ForeignKey(
        verbose_name=_("Country"),
        to="park_data.Country",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="states",  # Manager available at `Country.states`
    )
