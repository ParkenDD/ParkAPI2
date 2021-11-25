from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.gis.db import models as gismodels

class TimestampedMixin:
    pass

class TimestampedModel(models.Model):

    class Meta:
        abstract = True

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


class TimestampedGeoModel(gismodels.Model):

    class Meta:
        abstract = True

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
