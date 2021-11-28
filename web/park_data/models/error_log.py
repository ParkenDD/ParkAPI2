import datetime
from django.utils.translation import gettext_lazy as _
from django.db import models


class ErrorLogSources:
    module = "module"       # a scraper module
    pool = "pool"


class ErrorLog(models.Model):

    class Meta:
        verbose_name = _("Error log")
        verbose_name_plural = _("Error logs")

    timestamp = models.DateTimeField(
        verbose_name=_("Timestamp"),
        help_text=_("Datetime of snapshot (UTC)"),
        default=datetime.datetime.utcnow,
        db_index=True,
    )

    source = models.CharField(
        verbose_name=_("Source of error"),
        max_length=16,
        choices=(
            (ErrorLogSources.module, ErrorLogSources.module),
            (ErrorLogSources.pool, ErrorLogSources.pool),
        ),
        db_index=True,
    )

    module_name = models.CharField(
        verbose_name=_("Module name"),
        help_text=_("Name of the scraper module"),
        max_length=64,
        db_index=True,
    )

    pool_id = models.CharField(
        verbose_name=_("Pool ID"),
        max_length=64,
        null=True, blank=True,
        db_index=True,
    )

    text = models.TextField(
        verbose_name=_("Error text"),
        null=True, blank=True,
    )

    stacktrace = models.TextField(
        verbose_name=_("Stacktrace"),
        null=True, blank=True,
    )

    def __str__(self):
        return f"{self.module_name}@{self.timestamp}"

