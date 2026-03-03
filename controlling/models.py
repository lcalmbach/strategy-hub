from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from core.models import TimestampedModel, UserStampedModel
from strategies.models import ResponsibilityRole, StrategyLevel, StrategyLevelType


class ControllingPeriodStatus(models.TextChoices):
    DRAFT = "draft", "Entwurf"
    OPEN_FOR_PLANNING = "open_for_planning", "Offen fuer Planung"
    OPEN_FOR_ACTUALS = "open_for_actuals", "Offen fuer Ist-Erfassung"
    CLOSED = "closed", "Abgeschlossen"


class ControllingRecordStatus(models.TextChoices):
    OPEN = "open", "Offen"
    PLANNING_IN_PROGRESS = "planning_in_progress", "Planung laeuft"
    READY_FOR_ACTUALS = "ready_for_actuals", "Bereit fuer Ist-Erfassung"
    COMPLETED = "completed", "Abgeschlossen"


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
    status = models.CharField(
        "Status",
        max_length=30,
        choices=ControllingRecordStatus.choices,
        default=ControllingRecordStatus.OPEN,
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
        "Ist-Erfuellungsgrad Prozent",
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
            errors["measure"] = "Controlling-Records duerfen nur Massnahmen referenzieren."
        if self.period_id and self.measure_id and self.period.strategy_id != self.measure.strategy_id:
            errors["period"] = "Periode und Massnahme muessen zur gleichen Strategie gehoeren."
        if self.actual_fulfillment_percent < 0 or self.actual_fulfillment_percent > 100:
            errors["actual_fulfillment_percent"] = "Erfuellungsgrad muss zwischen 0 und 100 liegen."
        if errors:
            raise ValidationError(errors)

    @property
    def cost_delta_chf(self) -> Decimal:
        return self.actual_cost_chf - self.plan_cost_chf

    @property
    def effort_delta_days(self) -> Decimal:
        return self.actual_effort_person_days - self.plan_effort_person_days

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
