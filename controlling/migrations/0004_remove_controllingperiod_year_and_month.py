from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("controlling", "0003_controllingperiod_strategy"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="controllingperiod",
            name="uniq_period_strategy_year_month",
        ),
        migrations.RemoveField(
            model_name="controllingperiod",
            name="month",
        ),
        migrations.RemoveField(
            model_name="controllingperiod",
            name="year",
        ),
        migrations.AddConstraint(
            model_name="controllingperiod",
            constraint=models.UniqueConstraint(
                fields=("strategy", "start_date", "end_date"),
                name="uniq_period_strategy_dates",
            ),
        ),
        migrations.AlterModelOptions(
            name="controllingperiod",
            options={
                "ordering": ["-start_date", "name"],
                "verbose_name": "Controlling-Periode",
                "verbose_name_plural": "Controlling-Perioden",
            },
        ),
    ]
