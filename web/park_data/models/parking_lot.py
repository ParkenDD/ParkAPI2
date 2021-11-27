from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models

from .timestamped import TimestampedGeoModel


class ParkingLot(TimestampedGeoModel):

    class Meta:
        verbose_name = _("Parking lot")
        verbose_name_plural = _("Parking lots")

    pool = models.ForeignKey(
        verbose_name=_("Pool"),
        to="park_data.ParkingPool",
        on_delete=models.CASCADE,
        db_index=True,
    )

    lot_id = models.CharField(
        verbose_name=_("ID of parking lot"),
        help_text=_("This ID uniquely identifies a single parking lot through all history"),
        max_length=64,
        unique=True,
    )

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=128,
        db_index=True,
    )

    address = models.TextField(
        verbose_name=_("Address of parking lot"),
        max_length=1024,
        null=True, blank=True,
    )

    type = models.CharField(
        verbose_name=_("Type of lot"),
        help_text=_("Let's see what base types we can crystalize"),
        max_length=64,
        null=True, blank=True,
        db_index=True,
    )

    max_capacity = models.IntegerField(
        verbose_name=_("Maximum total spaces"),
        help_text=_("The number of maximum total spaces that have been encountered"),
        null=True, blank=True,
        db_index=True,
    )

    has_live_capacity = models.BooleanField(
        verbose_name=_("Has live capacity?"),
        db_index=True,
    )

    public_url = models.URLField(
        verbose_name=_("Public website"),
        max_length=4096,
        null=True, blank=True,
    )

    source_url = models.URLField(
        verbose_name=_("Data website"),
        max_length=4096,
        null=True, blank=True,
    )

    geo_point = models.PointField(
        verbose_name=_("Geo point"),
        null=True, blank=True,
        db_index=True,
    )

    latest_data = models.OneToOneField(
        verbose_name=_("Latest data"),
        to="park_data.LatestParkingData",
        on_delete=models.SET_NULL,
        null=True, editable=False,
        db_index=True,
    )

    location = models.ForeignKey(
        verbose_name=_("Location"),
        help_text=_("A link to a location description"),
        to="locations.Location",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="parking_lots",
    )

    def __str__(self):
        s = self.lot_id
        if self.name:
            s = f"{s}/{self.name}"
        return s
