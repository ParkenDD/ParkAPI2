from django.utils.translation import gettext_lazy as _
# from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db import models


class ParkingLot(models.Model):

    class Meta:
        verbose_name = _("Parking lot")
        verbose_name_plural = _("Parking lots")

    created_at = models.DateTimeField(
        verbose_name=_("Date of creation"),
        auto_now_add=True,
        db_index=True,
        editable=False,
    )

    lot_id = models.CharField(
        verbose_name=_("ID of parking lot"),
        help_text=_("This ID uniquely identifies a single parking lot through all history"),
        max_length=64,
        primary=True,
    )

    city = models.ForeignKey(
        verbose_name=_("City"),
        to="park_data.City",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="parking_lots",  # Manager available at `City.parking_lots`
    )

    name = models.CharField(
        verbose_name=_("Name of parking lot"),
        max_length=64,
        db_index=True,
    )

    address = models.TextField(
        verbose_name=_("Address of parking lot"),
        max_length=1024,
        null=True,
    )

    lot_type = models.CharField(
        verbose_name=_("Type of lot"),
        help_text=_("Let's see what base types we can crystalize"),
        max_length=64,
        null=True,
        db_index=True,
    )

    max_num_total = models.IntegerField(
        verbose_name=_("Maximum total spaces"),
        help_text=_("The number of maximum total spaces that have been encountered"),
        null=True,
        db_index=True,
    )

    geo_coords = models.PointField(
        verbose_name=_("Location of parking lot"),
        null=True,
        db_index=True,
    )

    geo_polygon = models.PolygonField(
        verbose_name=_("Outline of parking lot"),
        null=True,
        db_index=True,
    )
