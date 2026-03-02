from django.db import migrations, models


def move_strategy_images_to_bucket_root(apps, schema_editor):
    Strategy = apps.get_model("strategies", "Strategy")
    for strategy in Strategy.objects.exclude(image=""):
        image_name = str(strategy.image)
        if image_name.startswith("strategies/"):
            strategy.image = image_name.removeprefix("strategies/")
            strategy.save(update_fields=["image"])


class Migration(migrations.Migration):

    dependencies = [
        ("strategies", "0003_alter_measureresponsibility_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="strategy",
            name="image",
            field=models.ImageField(blank=True, upload_to="", verbose_name="Bild"),
        ),
        migrations.RunPython(move_strategy_images_to_bucket_root, migrations.RunPython.noop),
    ]
