import django.db.models.deletion
from django.db import migrations, models


def split_periods_by_strategy(apps, schema_editor):
    ControllingPeriod = apps.get_model("controlling", "ControllingPeriod")
    ControllingRecord = apps.get_model("controlling", "ControllingRecord")
    Strategy = apps.get_model("strategies", "Strategy")

    default_strategy = Strategy.objects.order_by("pk").first()
    if default_strategy is None:
        raise RuntimeError("At least one strategy is required before migrating controlling periods.")

    for period in ControllingPeriod.objects.order_by("pk"):
        records = list(
            ControllingRecord.objects.filter(period_id=period.pk)
            .select_related("measure")
            .order_by("pk")
        )
        strategy_ids = []
        for record in records:
            strategy_id = record.measure.strategy_id
            if strategy_id not in strategy_ids:
                strategy_ids.append(strategy_id)

        if not strategy_ids:
            period.strategy_id = default_strategy.pk
            period.save(update_fields=["strategy"])
            continue

        period.strategy_id = strategy_ids[0]
        period.save(update_fields=["strategy"])

        for extra_strategy_id in strategy_ids[1:]:
            duplicate = ControllingPeriod.objects.create(
                strategy_id=extra_strategy_id,
                name=period.name,
                year=period.year,
                month=period.month,
                start_date=period.start_date,
                end_date=period.end_date,
                planning_deadline=period.planning_deadline,
                actuals_deadline=period.actuals_deadline,
                status=period.status,
                is_locked=period.is_locked,
                created_at=period.created_at,
                updated_at=period.updated_at,
                created_by_id=period.created_by_id,
                updated_by_id=period.updated_by_id,
            )
            ControllingRecord.objects.filter(
                period_id=period.pk,
                measure__strategy_id=extra_strategy_id,
            ).update(period_id=duplicate.pk)


class Migration(migrations.Migration):

    dependencies = [
        ("controlling", "0002_alter_controllingperiod_options_and_more"),
        ("strategies", "0003_alter_measureresponsibility_options_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="controllingperiod",
            name="uniq_period_year_month",
        ),
        migrations.AddField(
            model_name="controllingperiod",
            name="strategy",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="controlling_periods",
                to="strategies.strategy",
                verbose_name="Strategie",
            ),
        ),
        migrations.RunPython(split_periods_by_strategy, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="controllingperiod",
            name="strategy",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="controlling_periods",
                to="strategies.strategy",
                verbose_name="Strategie",
            ),
        ),
        migrations.AddConstraint(
            model_name="controllingperiod",
            constraint=models.UniqueConstraint(
                fields=("strategy", "year", "month"),
                name="uniq_period_strategy_year_month",
            ),
        ),
    ]
