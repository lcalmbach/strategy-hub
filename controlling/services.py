from django.db import transaction

from core.models import Code
from strategies.models import MeasureResponsibility, StrategyLevel, StrategyLevelType

from .models import ControllingRecord, ControllingRecordResponsibility, ControllingRecordStatus


def get_controlling_status_code(status_code: str) -> Code:
    return Code.objects.get(category_id=1, code=status_code)


@transaction.atomic
def open_period(period, *, created_by=None):
    measures = (
        StrategyLevel.objects.filter(
            strategy_id=period.strategy_id,
            level=StrategyLevelType.MASSNAHME,
        )
        .select_related("strategy")
        .order_by("short_code", "pk")
    )

    created_records = []
    existing_count = 0
    default_status = get_controlling_status_code(ControllingRecordStatus.OPEN)
    for measure in measures:
        record, created = ControllingRecord.objects.get_or_create(
            period=period,
            measure=measure,
            defaults={
                "status": default_status,
                "created_by": created_by,
                "updated_by": created_by,
            },
        )
        if created:
            created_records.append(record)
            responsibilities = MeasureResponsibility.objects.filter(measure=measure)
            ControllingRecordResponsibility.objects.bulk_create(
                [
                    ControllingRecordResponsibility(
                        controlling_record=record,
                        person=responsibility.person,
                        role=responsibility.role,
                        created_by=created_by,
                        updated_by=created_by,
                    )
                    for responsibility in responsibilities
                ]
            )
        else:
            existing_count += 1

    return created_records, existing_count
