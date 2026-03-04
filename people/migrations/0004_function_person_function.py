from django.db import migrations, models
import django.db.models.deletion


FUNCTION_CODE_MAP = {
    "Amtsleitung": "AL",
    "Bereichsleitung": "BL",
    "Fachteam Leiter": "FTL",
    "Datenmanagement": "DM",
    "Mitarbeitende": "MA",
}


def populate_functions(apps, schema_editor):
    Function = apps.get_model("people", "Function")
    Person = apps.get_model("people", "Person")

    labels = list(Person.objects.order_by().values_list("function_title", flat=True).distinct())
    sort_order = 10
    for label in labels:
        if not label:
            continue
        code = FUNCTION_CODE_MAP.get(label)
        if code is None:
            letters = "".join(character for character in label.upper() if character.isalnum())
            code = letters[:10] or f"F{sort_order}"
        function, _ = Function.objects.get_or_create(
            code=code,
            defaults={
                "label": label,
                "sort_order": sort_order,
                "is_active": True,
            },
        )
        Person.objects.filter(function_title=label).update(function_id=function.pk)
        sort_order += 10


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0003_alter_person_short_code"),
    ]

    operations = [
        migrations.CreateModel(
            name="Function",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")),
                ("code", models.CharField(max_length=50, unique=True, verbose_name="Code")),
                ("label", models.CharField(max_length=255, unique=True, verbose_name="Bezeichnung")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Sortierung")),
                ("is_active", models.BooleanField(default=True, verbose_name="Aktiv")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="auth.user",
                        verbose_name="Erstellt von",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="auth.user",
                        verbose_name="Aktualisiert von",
                    ),
                ),
            ],
            options={
                "verbose_name": "Funktion",
                "verbose_name_plural": "Funktionen",
                "ordering": ["sort_order", "label"],
            },
        ),
        migrations.AddField(
            model_name="person",
            name="function",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="people",
                to="people.function",
                verbose_name="Funktion",
            ),
        ),
        migrations.RunPython(populate_functions, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="person",
            name="function",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="people",
                to="people.function",
                verbose_name="Funktion",
            ),
        ),
        migrations.RemoveField(
            model_name="person",
            name="function_title",
        ),
    ]
