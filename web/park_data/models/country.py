from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models

from .osm_base import OSMBase


class Country(OSMBase):

    class Meta:
        verbose_name = _("Country")
        verbose_name_plural = _("Country")

    iso_code = models.CharField(
        verbose_name=_("country code"),
        help_text=_("two-letter ISO 3166 country code"),
        max_length=64,
        unique=True,
        db_index=True,
    )

    def clean_fields(self, exclude=None):
        self.iso_code = self.iso_code.lower()
