from django.core.exceptions import ValidationError
from django.db import models

from core.models import OrderedModel, TimestampedModel, UserStampedModel


class StrategyStatus(models.TextChoices):
    PLANNED = "planned", "Geplant"
    ACTIVE = "active", "Aktiv"
    INACTIVE = "inactive", "Inaktiv"
    COMPLETED = "completed", "Abgeschlossen"


class StrategyLevelType(models.TextChoices):
    HANDLUNGSFELD = "handlungsfeld", "Handlungsfeld"
    ZIEL = "ziel", "Ziel"
    MASSNAHME = "massnahme", "Massnahme"


class ResponsibilityRole(models.TextChoices):
    RESPONSIBLE = "responsible", "Verantwortlich"
    CO_RESPONSIBLE = "co_responsible", "Mitverantwortlich"
    SUPPORTING = "supporting", "Unterstuetzend"
    APPROVER = "approver", "Freigebend"


class MeasureStatus(models.TextChoices):
    PLANNED = "planned", "Geplant"
    IN_PROGRESS = "in_progress", "In Arbeit"
    COMPLETED = "completed", "Abgeschlossen"
    POSTPONED = "postponed", "Verschoben"


class Strategy(TimestampedModel, UserStampedModel):
    title = models.CharField("Titel", max_length=255)
    short_description = models.TextField("Kurzbeschreibung")
    image = models.ImageField("Bild", upload_to="strategies/", blank=True)
    document_url = models.URLField("Dokument-Link", blank=True)
    valid_from = models.DateField("Gueltig von")
    valid_until = models.DateField("Gueltig bis", null=True, blank=True)
    status = models.CharField("Status", max_length=20, choices=StrategyStatus.choices, default=StrategyStatus.PLANNED)
    vision = models.TextField("Vision")
    mission = models.TextField("Mission")
    is_active = models.BooleanField("Aktiv", default=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "Strategie"
        verbose_name_plural = "Strategien"

    def clean(self) -> None:
        if self.valid_until and self.valid_until < self.valid_from:
            raise ValidationError({"valid_until": "Gueltig bis darf nicht vor Gueltig von liegen."})

    def __str__(self) -> str:
        return self.title


class MeasureType(TimestampedModel, UserStampedModel):
    code = models.CharField("Code", max_length=50, unique=True)
    label = models.CharField("Bezeichnung", max_length=255)
    is_active = models.BooleanField("Aktiv", default=True)

    class Meta:
        ordering = ["label"]
        verbose_name = "Massnahmentyp"
        verbose_name_plural = "Massnahmentypen"

    def __str__(self) -> str:
        return self.label


class StrategyLevel(TimestampedModel, UserStampedModel, OrderedModel):
    strategy = models.ForeignKey(Strategy, verbose_name="Strategie", on_delete=models.CASCADE, related_name="levels")
    level = models.CharField("Ebene", max_length=20, choices=StrategyLevelType.choices)
    title = models.CharField("Titel", max_length=255)
    short_code = models.CharField("Kuerzel", max_length=50)
    description = models.TextField("Beschreibung", blank=True)
    parent = models.ForeignKey(
        "self",
        verbose_name="Parent",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )
    measure_type = models.ForeignKey(
        MeasureType,
        verbose_name="Massnahme-Typ",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="strategy_levels",
    )
    start_date = models.DateField("Startdatum", null=True, blank=True)
    end_date = models.DateField("Enddatum", null=True, blank=True)
    status = models.CharField(
        "Status",
        max_length=20,
        choices=MeasureStatus.choices,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["strategy", "sort_order", "title"]
        verbose_name = "Strategieebene"
        verbose_name_plural = "Strategieebenen"
        constraints = [
            models.UniqueConstraint(fields=["strategy", "short_code"], name="uniq_strategy_level_code"),
        ]

    @property
    def display_label(self) -> str:
        return f"{self.short_code} {self.title}".strip()

    @property
    def start_year_display(self) -> str:
        return str(self.start_date.year) if self.start_date else ""

    @property
    def end_year_display(self) -> str:
        return str(self.end_date.year) if self.end_date else ""

    def clean(self) -> None:
        errors = {}
        if self.parent and self.parent.strategy_id != self.strategy_id:
            errors["parent"] = "Parent muss zur gleichen Strategie gehoeren."

        if self.level == StrategyLevelType.HANDLUNGSFELD:
            if self.parent_id:
                errors["parent"] = "Handlungsfelder duerfen keinen Parent haben."
            if self.measure_type_id:
                errors["measure_type"] = "Massnahme-Typ ist nur fuer Massnahmen erlaubt."
            if self.start_date:
                errors["start_date"] = "Startdatum ist nur fuer Massnahmen erlaubt."
            if self.end_date:
                errors["end_date"] = "Enddatum ist nur fuer Massnahmen erlaubt."
            if self.status:
                errors["status"] = "Status ist nur fuer Massnahmen erlaubt."

        if self.level == StrategyLevelType.ZIEL:
            if not self.parent_id:
                errors["parent"] = "Ziele brauchen ein Handlungsfeld als Parent."
            elif self.parent.level != StrategyLevelType.HANDLUNGSFELD:
                errors["parent"] = "Ziele duerfen nur unter Handlungsfeldern liegen."
            if self.measure_type_id:
                errors["measure_type"] = "Massnahme-Typ ist nur fuer Massnahmen erlaubt."
            if self.start_date:
                errors["start_date"] = "Startdatum ist nur fuer Massnahmen erlaubt."
            if self.end_date:
                errors["end_date"] = "Enddatum ist nur fuer Massnahmen erlaubt."
            if self.status:
                errors["status"] = "Status ist nur fuer Massnahmen erlaubt."

        if self.level == StrategyLevelType.MASSNAHME:
            if not self.parent_id:
                errors["parent"] = "Massnahmen brauchen ein Ziel als Parent."
            elif self.parent.level != StrategyLevelType.ZIEL:
                errors["parent"] = "Massnahmen duerfen nur unter Zielen liegen."
            if self.start_date and self.end_date and self.end_date < self.start_date:
                errors["end_date"] = "Enddatum darf nicht vor Startdatum liegen."

        if self.level != StrategyLevelType.MASSNAHME and self.measure_type_id:
            errors["measure_type"] = "Massnahme-Typ ist nur fuer Massnahmen erlaubt."

        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return self.display_label


class MeasureResponsibility(TimestampedModel, UserStampedModel):
    measure = models.ForeignKey(
        StrategyLevel,
        verbose_name="Massnahme",
        on_delete=models.CASCADE,
        related_name="responsibilities",
    )
    person = models.ForeignKey(
        "people.Person",
        verbose_name="Person",
        on_delete=models.CASCADE,
        related_name="measure_responsibilities",
    )
    role = models.CharField("Rolle", max_length=30, choices=ResponsibilityRole.choices)
    valid_from = models.DateField("Gueltig von", null=True, blank=True)
    valid_until = models.DateField("Gueltig bis", null=True, blank=True)

    class Meta:
        ordering = ["measure", "role", "person"]
        verbose_name = "Massnahmenverantwortlichkeit"
        verbose_name_plural = "Massnahmenverantwortlichkeiten"

    def clean(self) -> None:
        errors = {}
        if self.measure.level != StrategyLevelType.MASSNAHME:
            errors["measure"] = "Verantwortlichkeiten duerfen nur Massnahmen zugeordnet werden."
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            errors["valid_until"] = "Gueltig bis darf nicht vor Gueltig von liegen."
        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return f"{self.measure} - {self.person} ({self.get_role_display()})"
