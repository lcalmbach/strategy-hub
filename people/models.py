from django.conf import settings
from django.db import models

from core.models import TimestampedModel, UserStampedModel


class Person(TimestampedModel, UserStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name="Benutzer", on_delete=models.CASCADE)
    short_code = models.CharField("Kuerzel", max_length=50, unique=True)
    function_title = models.CharField("Funktion", max_length=255)
    organizational_unit = models.CharField("Organisationseinheit", max_length=255, blank=True)
    is_active_profile = models.BooleanField("Aktiv", default=True)

    class Meta:
        ordering = ["user__last_name", "user__first_name", "short_code"]
        verbose_name = "Person"
        verbose_name_plural = "Personen"

    def __str__(self) -> str:
        return self.short_code
