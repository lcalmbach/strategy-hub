from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("controlling", "0008_controllingrecord_aufwand_status_manual_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="controllingperiod",
            name="invitation_controlling_mail_text",
            field=models.TextField(blank=True, verbose_name="Mailtext Einladung Controlling"),
        ),
        migrations.AddField(
            model_name="controllingperiod",
            name="invitation_planning_mail_text",
            field=models.TextField(blank=True, verbose_name="Mailtext Einladung Planung"),
        ),
        migrations.AddField(
            model_name="controllingperiod",
            name="reminder_days_before_deadline",
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Tage Mail vor Termin"),
        ),
        migrations.AddField(
            model_name="controllingperiod",
            name="reminder_mail_enabled",
            field=models.BooleanField(default=False, verbose_name="Erinnerungsmail aktiv"),
        ),
    ]
