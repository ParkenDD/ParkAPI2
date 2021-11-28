from django.utils.translation import gettext_lazy as _
from django.db import models


class ParkingLotState:
    OPEN = "open"           # website shows that lot is open
    CLOSED = "closed"       # website shows that lot is closed
    UNKNOWN = "unknown"     # website did not publish state
    NODATA = "nodata"       # website does not publish number of free lots
    ERROR = "error"         # a scraper or server error occurred


class ParkingDataBase(models.Model):

    class Meta:
        abstract = True

    timestamp = models.DateTimeField(
        verbose_name=_("Timestamp"),
        help_text=_("Datetime of snapshot (UTC)"),
        db_index=True,
    )

    lot_timestamp = models.DateTimeField(
        verbose_name=_("Last update"),
        help_text=_("Last update of published lot data"),
        null=True, blank=True,
        db_index=True,
    )

    status = models.CharField(
        verbose_name=_("Status"),
        help_text=_("Status of parking lot (website)"),
        max_length=16,
        db_index=True,
        choices=(
            (ParkingLotState.OPEN, ParkingLotState.OPEN),
            (ParkingLotState.CLOSED, ParkingLotState.CLOSED),
            (ParkingLotState.UNKNOWN, ParkingLotState.UNKNOWN),
            (ParkingLotState.NODATA, ParkingLotState.NODATA),
            (ParkingLotState.ERROR, ParkingLotState.ERROR)
        )
    )

    num_free = models.IntegerField(
        verbose_name=_("Free"),
        help_text=_("Number of free spaces"),
        null=True, blank=True,
        db_index=True,
    )

    capacity = models.IntegerField(
        verbose_name=_("Capacity"),
        help_text=_("Number of total available spaces"),
        null=True, blank=True,
        db_index=True,
    )

    num_occupied = models.IntegerField(
        verbose_name=_("Occupied"),
        help_text=_("Number of occupied spaces"),
        null=True, blank=True,
        db_index=True,
    )

    percent_free = models.FloatField(
        verbose_name=_("Free %"),
        help_text=_("Percentage of free spaces"),
        null=True, blank=True,
        db_index=True,
    )

    def save(self, **kwargs):
        if self.capacity is not None:
            if self.num_free is not None:
                if self.num_occupied is None:
                    self.num_occupied = self.capacity - self.num_free
                else:
                    if self.num_occupied != self.capacity - self.num_free:
                        raise ValueError(
                            f"Data '{self}' has invalid 'num_occupied' {self.num_occupied}"
                            f", expected {self.capacity - self.num_free}"
                            f" (free={self.num_free}, capacity={self.capacity})"
                        )

            elif self.num_occupied is not None:
                if self.num_free is None:
                    self.num_free = self.capacity - self.num_occupied
                else:
                    if self.num_free != self.capacity - self.num_occupied:
                        raise ValueError(
                            f"Data '{self}' has invalid 'num_free' {self.num_free}"
                            f", expected {self.capacity - self.num_occupied}"
                            f" (occupied={self.num_occupied}, capacity={self.capacity})"
                        )

            if self.num_free is not None and self.capacity:
                self.percent_free = round(self.num_free * 100. / self.capacity, 2)

        super().save(**kwargs)


class ParkingData(ParkingDataBase):

    class Meta:
        verbose_name = _("Parking data")
        verbose_name_plural = _("Parking data")
        unique_together = ("timestamp", "lot")

    lot = models.ForeignKey(
        verbose_name=_("Parking lot"),
        to="park_data.ParkingLot",
        on_delete=models.CASCADE,
        db_index=True,
    )

    def __str__(self):
        return f"{self.timestamp}/{self.lot.lot_id}"


class LatestParkingData(ParkingDataBase):
    class Meta:
        verbose_name = _("Latest parking data")
        verbose_name_plural = _("Latest parking data")
