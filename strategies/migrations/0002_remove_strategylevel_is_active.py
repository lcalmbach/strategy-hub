from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("strategies", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="strategylevel",
            name="is_active",
        ),
    ]
