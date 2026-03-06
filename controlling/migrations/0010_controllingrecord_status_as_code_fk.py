from django.db import migrations, models
import django.db.models.deletion


STATUS_CODE_ROWS = [
    ("Offen", "Offen", 10),
    ("Planung läuft", "Planung läuft", 20),
    ("Planung abgeschlossen", "Planung abgeschlossen", 30),
    ("Controlling läuft", "Controlling läuft", 40),
    ("Controlling abgeschlossen", "Controlling abgeschlossen", 50),
]

OLD_TO_NEW_STATUS_MAP = {
    "open": "Offen",
    "planning_in_progress": "Planung läuft",
    "planning_completed": "Planung abgeschlossen",
    "ready_for_actuals": "Controlling läuft",
    "controlling_in_progress": "Controlling läuft",
    "completed": "Controlling abgeschlossen",
    "controlling_completed": "Controlling abgeschlossen",
}


def ensure_status_codes(apps, schema_editor):
    Code = apps.get_model("core", "Code")
    CodeCategory = apps.get_model("core", "CodeCategory")
    if not CodeCategory.objects.filter(pk=1).exists():
        raise RuntimeError("Code category with ID 1 is required for controlling record statuses.")

    for code, name, sort_order in STATUS_CODE_ROWS:
        Code.objects.update_or_create(
            category_id=1,
            code=code,
            defaults={
                "name": name,
                "short_name": "",
                "sort_order": sort_order,
            },
        )


def backfill_status_fk(apps, schema_editor):
    Code = apps.get_model("core", "Code")
    ControllingRecord = apps.get_model("controlling", "ControllingRecord")

    code_id_by_code = {
        row["code"]: row["id"]
        for row in Code.objects.filter(category_id=1, code__in=[item[0] for item in STATUS_CODE_ROWS]).values("id", "code")
    }
    default_status_id = code_id_by_code["Offen"]

    for old_value, new_code in OLD_TO_NEW_STATUS_MAP.items():
        ControllingRecord.objects.filter(status=old_value).update(status_code_id=code_id_by_code[new_code])

    ControllingRecord.objects.filter(status_code_id__isnull=True).update(status_code_id=default_status_id)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("controlling", "0009_controllingperiod_mail_settings"),
    ]

    operations = [
        migrations.RunPython(ensure_status_codes, migrations.RunPython.noop),
        migrations.AddField(
            model_name="controllingrecord",
            name="status_code",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="controlling_records_tmp",
                to="core.code",
                verbose_name="Status",
            ),
        ),
        migrations.RunPython(backfill_status_fk, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="controllingrecord",
            name="status",
        ),
        migrations.RenameField(
            model_name="controllingrecord",
            old_name="status_code",
            new_name="status",
        ),
        migrations.AlterField(
            model_name="controllingrecord",
            name="status",
            field=models.ForeignKey(
                limit_choices_to={"category_id": 1},
                on_delete=django.db.models.deletion.PROTECT,
                related_name="controlling_records",
                to="core.code",
                verbose_name="Status",
            ),
        ),
    ]
