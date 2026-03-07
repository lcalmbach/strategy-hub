from django.db import models

from core.models import TimestampedModel, UserStampedModel


class Report(TimestampedModel, UserStampedModel):
    name = models.CharField("Name", max_length=255, unique=True)
    sql = models.TextField("SQL")
    params = models.JSONField("Parameter", default=dict, blank=True)
    description = models.TextField("Beschreibung", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Auswertung"
        verbose_name_plural = "Auswertungen"

    def __str__(self) -> str:
        return self.name
