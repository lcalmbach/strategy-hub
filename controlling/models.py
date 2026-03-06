from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from core.models import TimestampedModel, UserStampedModel
from strategies.models import ResponsibilityRole, StrategyLevel, StrategyLevelType


class ControllingPeriodStatus(models.TextChoices):
    DRAFT = "draft", "Entwurf"
    OPEN_FOR_PLANNING = "open_for_planning", "Offen für Planung"
    OPEN_FOR_ACTUALS = "open_for_actuals", "Offen für Ist-Erfassung"
    CLOSED = "closed", "Abgeschlossen"


class ControllingRecordStatus(models.TextChoices):
    OPEN = "Offen", "Offen"
    PLANNING_IN_PROGRESS = "Planung läuft", "Planung läuft"
    PLANNING_COMPLETED = "Planung abgeschlossen", "Planung abgeschlossen"
    CONTROLLING_IN_PROGRESS = "Controlling läuft", "Controlling läuft"
    CONTROLLING_COMPLETED = "Controlling abgeschlossen", "Controlling abgeschlossen"


class AmpelStatus(models.TextChoices):
    GREEN = "green", "Grün"
    YELLOW = "yellow", "Gelb"
    RED = "red", "Rot"


class ControllingPeriod(TimestampedModel, UserStampedModel):
    strategy = models.ForeignKey(
        "strategies.Strategy",
        verbose_name="Strategie",
        on_delete=models.CASCADE,
        related_name="controlling_periods",
    )
    name = models.CharField("Name", max_length=255)
    start_date = models.DateField("Startdatum")
    end_date = models.DateField("Enddatum")
    planning_deadline = models.DateField("Planungsdeadline", null=True, blank=True)
    controlling_deadline = models.DateField("Controlling-Deadline", null=True, blank=True)
    reminder_mail_enabled = models.BooleanField("Erinnerungsmail aktiv", default=False)
    reminder_days_before_deadline = models.PositiveSmallIntegerField(
        "Tage Mail vor Termin",
        null=True,
        blank=True,
    )
    invitation_planning_mail_text = models.TextField("Mailtext Einladung Planung", blank=True)
    invitation_controlling_mail_text = models.TextField("Mailtext Einladung Controlling", blank=True)
    status = models.CharField(
        "Status",
        max_length=30,
        choices=ControllingPeriodStatus.choices,
        default=ControllingPeriodStatus.DRAFT,
    )

    class Meta:
        ordering = ["-start_date", "name"]
        verbose_name = "Controlling-Periode"
        verbose_name_plural = "Controlling-Perioden"
        constraints = [
            models.UniqueConstraint(fields=["strategy", "start_date", "end_date"], name="uniq_period_strategy_dates"),
        ]

    def clean(self) -> None:
        errors = {}
        if self.end_date < self.start_date:
            errors["end_date"] = "Periodenende darf nicht vor Periodenstart liegen."
        if self.planning_deadline and self.planning_deadline < self.start_date:
            errors["planning_deadline"] = "Planungsdeadline darf nicht vor Periodenstart liegen."
        if self.controlling_deadline and self.controlling_deadline < self.start_date:
            errors["controlling_deadline"] = "Controlling-Deadline darf nicht vor Periodenstart liegen."
        if self.reminder_mail_enabled and self.reminder_days_before_deadline is None:
            errors["reminder_days_before_deadline"] = "Bitte Anzahl Tage für Erinnerungsmail erfassen."
        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return self.name


class ControllingRecord(TimestampedModel, UserStampedModel):
    period = models.ForeignKey(
        ControllingPeriod,
        verbose_name="Controlling-Periode",
        on_delete=models.CASCADE,
        related_name="records",
    )
    measure = models.ForeignKey(
        StrategyLevel,
        verbose_name="Massnahme",
        on_delete=models.CASCADE,
        related_name="controlling_records",
    )
    status = models.ForeignKey(
        "core.Code",
        on_delete=models.PROTECT,
        verbose_name="Status",
        related_name="controlling_records",
        limit_choices_to={"category_id": 1},
    )
    umsetzung_status_manual = models.CharField(
        "Ampel Umsetzungsstand (manuell)",
        max_length=10,
        choices=AmpelStatus.choices,
        blank=True,
        default="",
    )
    kosten_status_manual = models.CharField(
        "Ampel Ausgaben (manuell)",
        max_length=10,
        choices=AmpelStatus.choices,
        blank=True,
        default="",
    )
    aufwand_status_manual = models.CharField(
        "Ampel Aufwand (manuell)",
        max_length=10,
        choices=AmpelStatus.choices,
        blank=True,
        default="",
    )
    plan_result_description = models.TextField("Plan-Ergebnis", blank=True)
    plan_effort_person_days = models.DecimalField(
        "Plan-Aufwand Personentage",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    plan_effort_description = models.TextField("Plan-Aufwand Beschreibung", blank=True)
    plan_cost_chf = models.DecimalField("Plan-Kosten CHF", max_digits=12, decimal_places=2, default=Decimal("0.00"))
    plan_cost_description = models.TextField("Plan-Kosten Beschreibung", blank=True)
    actual_fulfillment_percent = models.DecimalField(
        "Ist-Erfüllungsgrad Prozent",
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    actual_result_description = models.TextField("Ist-Ergebnis", blank=True)
    actual_effort_person_days = models.DecimalField(
        "Ist-Aufwand Personentage",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    actual_effort_description = models.TextField("Ist-Aufwand Beschreibung", blank=True)
    actual_cost_chf = models.DecimalField("Ist-Kosten CHF", max_digits=12, decimal_places=2, default=Decimal("0.00"))
    actual_cost_description = models.TextField("Ist-Kosten Beschreibung", blank=True)

    class Meta:
        ordering = ["-period__start_date", "measure__title"]
        verbose_name = "Controlling-Record"
        verbose_name_plural = "Controlling-Records"
        constraints = [
            models.UniqueConstraint(fields=["period", "measure"], name="uniq_period_measure"),
        ]

    def clean(self) -> None:
        errors = {}
        if self.measure.level != StrategyLevelType.MASSNAHME:
            errors["measure"] = "Controlling-Records dürfen nur Massnahmen referenzieren."
        if self.period_id and self.measure_id and self.period.strategy_id != self.measure.strategy_id:
            errors["period"] = "Periode und Massnahme müssen zur gleichen Strategie gehören."
        if self.status_id and self.status.category_id != 1:
            errors["status"] = "Status muss aus der Kategorie mit ID 1 stammen."
        if self.actual_fulfillment_percent < 0 or self.actual_fulfillment_percent > 100:
            errors["actual_fulfillment_percent"] = "Erfüllungsgrad muss zwischen 0 und 100 liegen."
        if errors:
            raise ValidationError(errors)

    @property
    def cost_delta_chf(self) -> Decimal:
        return self.actual_cost_chf - self.plan_cost_chf

    @property
    def effort_delta_days(self) -> Decimal:
        return self.actual_effort_person_days - self.plan_effort_person_days

    @staticmethod
    def _ratio_based_status(plan_value: Decimal, actual_value: Decimal) -> str:
        if plan_value == 0 and actual_value == 0:
            return ""
        if plan_value == actual_value:
            return AmpelStatus.GREEN
        if plan_value == 0 or actual_value == 0:
            return AmpelStatus.RED

        larger = max(plan_value, actual_value)
        smaller = min(plan_value, actual_value)
        ratio = larger / smaller
        if ratio < 2:
            return AmpelStatus.YELLOW
        return AmpelStatus.RED

    @property
    def umsetzung_status_calculated(self) -> str:
        if self.actual_fulfillment_percent == 0:
            return ""
        if self.actual_fulfillment_percent == 100:
            return AmpelStatus.GREEN
        if self.actual_fulfillment_percent >= 50:
            return AmpelStatus.YELLOW
        return AmpelStatus.RED

    @property
    def kosten_status_calculated(self) -> str:
        return self._ratio_based_status(self.plan_cost_chf, self.actual_cost_chf)

    @property
    def aufwand_status_calculated(self) -> str:
        return self._ratio_based_status(self.plan_effort_person_days, self.actual_effort_person_days)

    @property
    def umsetzung_status_effective(self) -> str:
        return self.umsetzung_status_manual or self.umsetzung_status_calculated

    @property
    def kosten_status_effective(self) -> str:
        return self.kosten_status_manual or self.kosten_status_calculated

    @property
    def aufwand_status_effective(self) -> str:
        return self.aufwand_status_manual or self.aufwand_status_calculated

    def __str__(self) -> str:
        return f"{self.measure} - {self.period}"


class ControllingRecordResponsibility(TimestampedModel, UserStampedModel):
    controlling_record = models.ForeignKey(
        ControllingRecord,
        verbose_name="Controlling-Record",
        on_delete=models.CASCADE,
        related_name="responsibilities",
    )
    person = models.ForeignKey(
        "people.Person",
        verbose_name="Person",
        on_delete=models.CASCADE,
        related_name="controlling_record_responsibilities",
    )
    role = models.CharField("Rolle", max_length=30, choices=ResponsibilityRole.choices)

    class Meta:
        ordering = ["controlling_record", "role", "person"]
        verbose_name = "Record-Verantwortlichkeit"
        verbose_name_plural = "Record-Verantwortlichkeiten"

    def __str__(self) -> str:
        return f"{self.controlling_record} - {self.person} ({self.get_role_display()})"
