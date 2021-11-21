from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models

from .osm_base import OSMBase


class ParkingLot(OSMBase):

    class Meta:
        verbose_name = _("Parking lot")
        verbose_name_plural = _("Parking lots")

    lot_id = models.CharField(
        verbose_name=_("ID of parking lot"),
        help_text=_("This ID uniquely identifies a single parking lot through all history"),
        max_length=64,
        unique=True,
    )

    # override to make nullable and non-unique
    osm_id = models.CharField(
        verbose_name=_("OpenStreetMap ID"),
        help_text=_("The ID must be prefixed with N, W or R (for Node, Way or Relation)"),
        max_length=32,
        null=True, blank=True,
        db_index=True,
    )

    created_at = models.DateTimeField(
        verbose_name=_("Date of creation"),
        auto_now_add=True, editable=False,
        db_index=True,
    )

    city = models.ForeignKey(
        verbose_name=_("City"),
        to="park_data.City",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="parking_lots",  # Manager available at `City.parking_lots`
    )

    address = models.TextField(
        verbose_name=_("Address of parking lot"),
        max_length=1024,
        null=True, blank=True,
    )

    lot_type = models.CharField(
        verbose_name=_("Type of lot"),
        help_text=_("Let's see what base types we can crystalize"),
        max_length=64,
        null=True, blank=True,
        db_index=True,
    )

    max_num_total = models.IntegerField(
        verbose_name=_("Maximum total spaces"),
        help_text=_("The number of maximum total spaces that have been encountered"),
        null=True, blank=True,
        db_index=True,
    )

    public_url = models.URLField(
        verbose_name=_("Public website"),
        max_length=4096,
        null=True, blank=True,
    )
