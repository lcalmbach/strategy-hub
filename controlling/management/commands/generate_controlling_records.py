from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Code
from controlling.models import ControllingPeriod, ControllingRecord, ControllingRecordStatus
from strategies.models import StrategyLevel, StrategyLevelType


class Command(BaseCommand):
    help = "Generate one controlling record per controlling period and massnahme within the same strategy."

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0
        existing_count = 0
        default_status = Code.objects.get(category_id=1, code=ControllingRecordStatus.OPEN)

        periods = ControllingPeriod.objects.select_related("strategy").order_by("strategy_id", "start_date", "pk")

        for period in periods:
            measures = StrategyLevel.objects.filter(
                strategy_id=period.strategy_id,
                level=StrategyLevelType.MASSNAHME,
            ).order_by("short_code", "pk")

            for measure in measures:
                _, created = ControllingRecord.objects.get_or_create(
                    period=period,
                    measure=measure,
                    defaults={"status": default_status},
                )
                if created:
                    created_count += 1
                else:
                    existing_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Controlling record generation completed. Created: {created_count}, already existed: {existing_count}."
            )
        )
