from django.utils.translation import gettext_lazy as _
from django.db import models

from .timestamped import TimestampedMixin


class ParkingPool(TimestampedMixin, models.Model):

    class Meta:
        verbose_name = _("Pool")
        verbose_name_plural = _("Pools")

    pool_id = models.CharField(
        verbose_name=_("Pool ID"),
        help_text=_("This ID uniquely identifies a pool through all history"),
        max_length=64,
        unique=True,
    )

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=128,
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

    license = models.TextField(
        verbose_name=_("License"),
        null=True, blank=True,
    )

    def __str__(self):
        s = self.pool_id
        if self.name:
            s = f"{s}/{self.name}"
        return s
