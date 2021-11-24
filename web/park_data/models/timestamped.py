from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models


class TimestampedMixin:

    date_created = models.DateTimeField(
        verbose_name=_("Created at"),
        auto_now_add=True, editable=False,
        db_index=True,
    )

    date_updated = models.DateTimeField(
        verbose_name=_("Last update"),
        auto_now=True, editable=False,
        db_index=True,
    )
