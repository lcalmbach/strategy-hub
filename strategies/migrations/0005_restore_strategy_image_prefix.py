from django.db import migrations, models


def restore_strategy_image_prefix(apps, schema_editor):
    Strategy = apps.get_model("strategies", "Strategy")
    for strategy in Strategy.objects.exclude(image=""):
        image_name = str(strategy.image)
        if image_name and not image_name.startswith("strategies/"):
            strategy.image = f"strategies/{image_name}"
            strategy.save(update_fields=["image"])


class Migration(migrations.Migration):

    dependencies = [
        ("strategies", "0004_move_strategy_images_to_bucket_root"),
    ]

    operations = [
        migrations.AlterField(
            model_name="strategy",
            name="image",
            field=models.ImageField(blank=True, upload_to="strategies/", verbose_name="Bild"),
        ),
        migrations.RunPython(restore_strategy_image_prefix, migrations.RunPython.noop),
    ]
