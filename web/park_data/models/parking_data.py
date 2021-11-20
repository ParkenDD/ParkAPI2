from django.utils.translation import gettext_lazy as _
from django.db import models


class ParkingLotState:
    OPEN = "open"           # website shows that lot is open
    CLOSED = "closed"       # website shows that lot is closed
    UNKNOWN = "unknown"     # website did not publish state
    NO_DATA = "nodata"      # website does not publish number of free lots
    ERROR = "error"         # a scraper or server error occurred


class ParkingData(models.Model):

    class Meta:
        verbose_name = _("Parking data")
        verbose_name_plural = _("Parking data")
        unique_together = ("timestamp", "place_id")

    timestamp = models.DateTimeField(
        verbose_name=_("Date of snapshot"),
        db_index=True,
    )

    lot = models.ForeignKey(
        verbose_name=_("Parking lot"),
        to="park_data.ParkingLot",
        on_delete=models.CASCADE,
        db_index=True,
    )

    status = models.CharField(
        verbose_name=_("State of parking lot (website)"),
        max_length=16,
        db_index=True,
        choices=(
            (ParkingLotState.OPEN, ParkingLotState.OPEN),
            (ParkingLotState.CLOSED, ParkingLotState.CLOSED),
            (ParkingLotState.UNKNOWN, ParkingLotState.UNKNOWN),
            (ParkingLotState.NO_DATA, ParkingLotState.NO_DATA),
            (ParkingLotState.ERROR, ParkingLotState.ERROR)
        )
    )

    num_free = models.IntegerField(
        verbose_name=_("Number of free spaces"),
        null=True,
        db_index=True,
    )

    num_total = models.IntegerField(
        verbose_name=_("Number of total available spaces"),
        null=True,
        db_index=True,
    )

    num_occupied = models.IntegerField(
        verbose_name=_("Number of occupied spaces"),
        null=True,
        db_index=True,
    )
