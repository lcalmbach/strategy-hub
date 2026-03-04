from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("strategies", "0009_alter_measureresponsibility_role_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="measureresponsibility",
            name="description",
            field=models.TextField(blank=True, verbose_name="Beschreibung"),
        ),
    ]
