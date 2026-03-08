import random
from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Code
from controlling.models import (
    ControllingPeriod,
    ControllingRecord,
    ControllingRecordResponsibility,
    ControllingRecordStatus,
)
from people.models import Person
from strategies.models import MeasureResponsibility, ResponsibilityRole, StrategyLevel, StrategyLevelType


class Command(BaseCommand):
    help = (
        "Generate one controlling record per controlling period and massnahme within the same strategy, "
        "then backfill missing record responsibilities and fake planning/controlling values."
    )

    @staticmethod
    def _is_planning_missing(record: ControllingRecord) -> bool:
        return (
            record.plan_effort_person_days == Decimal("0.00")
            and record.plan_cost_chf == Decimal("0.00")
            and not record.plan_result_description.strip()
            and not record.plan_effort_description.strip()
            and not record.plan_cost_description.strip()
            and not record.remarks_planning.strip()
        )

    @staticmethod
    def _is_controlling_missing(record: ControllingRecord) -> bool:
        return (
            record.actual_fulfillment_percent == Decimal("0.00")
            and record.actual_effort_person_days == Decimal("0.00")
            and record.actual_cost_chf == Decimal("0.00")
            and not record.actual_result_description.strip()
            and not record.actual_effort_description.strip()
            and not record.actual_cost_description.strip()
            and not record.remarks_controlling.strip()
        )

    @staticmethod
    def _quantize(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _backfill_responsibilities(self, record: ControllingRecord) -> int:
        if record.responsibilities.exists():
            return 0

        created_count = 0
        existing_keys = set(
            ControllingRecordResponsibility.objects.filter(controlling_record=record).values_list("person_id", "role")
        )
        measure_responsibilities = list(
            MeasureResponsibility.objects.filter(measure=record.measure).select_related("person")
        )

        if not measure_responsibilities:
            fallback_person = (
                Person.objects.filter(is_active_profile=True)
                .select_related("user")
                .order_by("short_code", "user__last_name", "user__first_name")
                .first()
            )
            if fallback_person is None:
                return 0
            measure_responsibilities = [
                MeasureResponsibility(
                    measure=record.measure,
                    person=fallback_person,
                    role=ResponsibilityRole.RESPONSIBLE,
                )
            ]

        for measure_responsibility in measure_responsibilities:
            key = (measure_responsibility.person_id, measure_responsibility.role)
            if key in existing_keys:
                continue
            record_responsibility = ControllingRecordResponsibility(
                controlling_record=record,
                person=measure_responsibility.person,
                role=measure_responsibility.role,
            )
            record_responsibility.full_clean()
            record_responsibility.save()
            existing_keys.add(key)
            created_count += 1

        return created_count

    def _backfill_fake_values(self, record: ControllingRecord) -> bool:
        planning_missing = self._is_planning_missing(record)
        controlling_missing = self._is_controlling_missing(record)
        if not planning_missing and not controlling_missing:
            return False

        seed = (record.pk or 0) * 10_000 + record.measure_id * 100 + record.period_id
        generator = random.Random(seed)

        if planning_missing:
            plan_effort = Decimal(generator.randint(8, 60))
            plan_cost = Decimal(generator.randint(15, 320)) * Decimal("1000")
            record.plan_result_description = f"Geplantes Ergebnis für {record.measure.short_code}"
            record.plan_effort_person_days = self._quantize(plan_effort)
            record.plan_effort_description = "Geplanter Aufwand gemäss initialer Schätzung."
            record.plan_cost_chf = self._quantize(plan_cost)
            record.plan_cost_description = "Geplante Kosten gemäss initialem Budget."
            record.remarks_planning = "Auto-generierte Planungsdaten."

        if controlling_missing:
            if record.plan_effort_person_days <= Decimal("0.00"):
                record.plan_effort_person_days = self._quantize(Decimal(generator.randint(8, 60)))
            if record.plan_cost_chf <= Decimal("0.00"):
                record.plan_cost_chf = self._quantize(Decimal(generator.randint(15, 320)) * Decimal("1000"))

            effort_factor = Decimal(str(generator.uniform(0.75, 1.30)))
            cost_factor = Decimal(str(generator.uniform(0.75, 1.30)))
            fulfillment = Decimal(generator.randint(35, 100))

            record.actual_fulfillment_percent = self._quantize(fulfillment)
            record.actual_result_description = f"Ist-Ergebnis für {record.measure.short_code}"
            record.actual_effort_person_days = self._quantize(record.plan_effort_person_days * effort_factor)
            record.actual_effort_description = "Ist-Aufwand basierend auf Fortschrittsmeldung."
            record.actual_cost_chf = self._quantize(record.plan_cost_chf * cost_factor)
            record.actual_cost_description = "Ist-Kosten basierend auf Fortschrittsmeldung."
            record.remarks_controlling = "Auto-generierte Controlling-Daten."

        record.full_clean()
        record.save()
        return True

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0
        existing_count = 0
        backfilled_responsibilities_count = 0
        backfilled_fake_values_count = 0
        default_status = Code.objects.get(category_id=1, code=ControllingRecordStatus.OPEN)

        periods = ControllingPeriod.objects.select_related("strategy").order_by("strategy_id", "start_date", "pk")

        for period in periods:
            measures = StrategyLevel.objects.filter(
                strategy_id=period.strategy_id,
                level=StrategyLevelType.MASSNAHME,
            ).order_by("short_code", "pk")

            for measure in measures:
                record, created = ControllingRecord.objects.get_or_create(
                    period=period,
                    measure=measure,
                    defaults={"status": default_status},
                )
                if created:
                    created_count += 1
                else:
                    existing_count += 1

                backfilled_responsibilities_count += self._backfill_responsibilities(record)
                if self._backfill_fake_values(record):
                    backfilled_fake_values_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Controlling record generation completed. "
                f"Created: {created_count}, already existed: {existing_count}, "
                f"responsibilities backfilled: {backfilled_responsibilities_count}, "
                f"records with fake values backfilled: {backfilled_fake_values_count}."
            )
        )
