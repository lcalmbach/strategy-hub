from django.db import transaction

from strategies.models import MeasureResponsibility, StrategyLevel, StrategyLevelType

from .models import ControllingRecord, ControllingRecordResponsibility


@transaction.atomic
def open_period(period, *, created_by=None):
    active_measures = (
        StrategyLevel.objects.filter(
            level=StrategyLevelType.MASSNAHME,
            is_active=True,
            strategy__is_active=True,
        )
        .select_related("strategy")
        .prefetch_related("responsibilities")
    )

    created_records = []
    for measure in active_measures:
        record, created = ControllingRecord.objects.get_or_create(
            period=period,
            measure=measure,
            defaults={"created_by": created_by, "updated_by": created_by},
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
    return created_records
