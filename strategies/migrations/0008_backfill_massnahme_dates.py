from datetime import date

from django.db import migrations


def backfill_massnahme_dates(apps, schema_editor):
    StrategyLevel = apps.get_model("strategies", "StrategyLevel")
    StrategyLevel.objects.filter(level="massnahme").update(
        start_date=date(2022, 1, 1),
        end_date=date(2025, 12, 31),
    )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("strategies", "0007_strategylevel_end_date_strategylevel_start_date_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_massnahme_dates, noop_reverse),
    ]
