from django.conf import settings
from django.db import models

from core.models import TimestampedModel, UserStampedModel


class Function(TimestampedModel, UserStampedModel):
    code = models.CharField("Code", max_length=50, unique=True)
    label = models.CharField("Bezeichnung", max_length=255, unique=True)
    sort_order = models.PositiveIntegerField("Sortierung", default=0)
    is_active = models.BooleanField("Aktiv", default=True)

    class Meta:
        ordering = ["sort_order", "label"]
        verbose_name = "Funktion"
        verbose_name_plural = "Funktionen"

    def __str__(self) -> str:
        return f"{self.code} {self.label}".strip()


class Organization(TimestampedModel, UserStampedModel):
    short_code = models.CharField("Kürzel", max_length=50, blank=True)
    bereich = models.CharField("Bereich", max_length=255)
    abteilung = models.CharField("Abteilung", max_length=255, blank=True)
    sort_order = models.PositiveIntegerField("Sortierung", default=0)
    is_active = models.BooleanField("Aktiv", default=True)

    class Meta:
        ordering = ["sort_order", "short_code", "bereich", "abteilung"]
        verbose_name = "Organisation"
        verbose_name_plural = "Organisationen"
        constraints = [
            models.UniqueConstraint(fields=["bereich", "abteilung"], name="uniq_organization_bereich_abteilung"),
        ]

    def __str__(self) -> str:
        if self.abteilung:
            return f"{self.bereich} - {self.abteilung}"
        return self.bereich


class Person(TimestampedModel, UserStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name="Benutzer", on_delete=models.CASCADE)
    short_code = models.CharField("Kürzel", max_length=50, unique=True)
    function = models.ForeignKey(
        Function,
        verbose_name="Funktion",
        on_delete=models.PROTECT,
        related_name="people",
    )
    organization = models.ForeignKey(
        Organization,
        verbose_name="Organisation",
        on_delete=models.PROTECT,
        related_name="people",
        null=True,
        blank=True,
    )
    is_active_profile = models.BooleanField("Aktiv", default=True)

    class Meta:
        ordering = ["user__last_name", "user__first_name", "short_code"]
        verbose_name = "Person"
        verbose_name_plural = "Personen"

    def __str__(self) -> str:
        return self.short_code
