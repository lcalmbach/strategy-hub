from django.db import migrations, models


def populate_strategy_short_codes(apps, schema_editor):
    Strategy = apps.get_model("strategies", "Strategy")
    for strategy in Strategy.objects.filter(short_code__isnull=True).order_by("pk"):
        strategy.short_code = f"STR-{strategy.pk}"
        strategy.save(update_fields=["short_code"])


class Migration(migrations.Migration):
    dependencies = [
        ("strategies", "0010_measureresponsibility_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="strategy",
            name="short_code",
            field=models.CharField("Kürzel", max_length=50, null=True),
        ),
        migrations.RunPython(populate_strategy_short_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="strategy",
            name="short_code",
            field=models.CharField("Kürzel", max_length=50, unique=True),
        ),
    ]
