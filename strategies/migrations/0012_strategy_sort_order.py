from django.db import migrations, models


def populate_strategy_sort_order(apps, schema_editor):
    Strategy = apps.get_model("strategies", "Strategy")
    for index, strategy in enumerate(Strategy.objects.order_by("title", "pk"), start=1):
        strategy.sort_order = index * 10
        strategy.save(update_fields=["sort_order"])


class Migration(migrations.Migration):
    dependencies = [
        ("strategies", "0011_strategy_short_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="strategy",
            name="sort_order",
            field=models.PositiveIntegerField(default=0, verbose_name="Sortierung"),
        ),
        migrations.RunPython(populate_strategy_sort_order, migrations.RunPython.noop),
    ]
