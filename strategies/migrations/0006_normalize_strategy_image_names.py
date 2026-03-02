import re

from django.db import migrations


SUFFIX_PATTERN = re.compile(r"^(?P<base>.+)_[A-Za-z0-9]{7}(?P<ext>\.[^.]+)$")


def normalize_strategy_image_names(apps, schema_editor):
    Strategy = apps.get_model("strategies", "Strategy")
    for strategy in Strategy.objects.exclude(image=""):
        image_name = str(strategy.image)
        prefix = "strategies/"
        if not image_name.startswith(prefix):
            continue

        filename = image_name.removeprefix(prefix)
        match = SUFFIX_PATTERN.match(filename)
        if not match:
            continue

        strategy.image = f"{prefix}{match.group('base')}{match.group('ext')}"
        strategy.save(update_fields=["image"])


class Migration(migrations.Migration):

    dependencies = [
        ("strategies", "0005_restore_strategy_image_prefix"),
    ]

    operations = [
        migrations.RunPython(normalize_strategy_image_names, migrations.RunPython.noop),
    ]
