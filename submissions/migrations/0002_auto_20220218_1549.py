# Generated by Django 4.0 on 2022-02-18 15:49

from django.db import migrations


def apply_migration(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.bulk_create([
        Group(name="Student"),
        Group(name="Učitel"),
    ])

    State = apps.get_model("submissions", "State")
    State.objects.bulk_create([
        State(
            code="supervisor_approved",
            name="Vedoucí schválil", 
            description="Zadání práce bylo schválené vedoucím. Čeká se na schválení autorem.",
        ),
        State(
            code="author_approved",
            name="Autor schválil",
            description="Zadání práce bylo schválené autorem. Čeká se na schválení vedoucím.",
        ),
        State(
            code="approved",
            name="Zadání schváleno",
            description="Zadání bylo schválené vedoucím i autorem. Je možné přistoupit ke konzultacím a realizaci práce.",
        ),
        State(
            code="submitted",
            name="Odevzdáno",
            description="Práce byla odevzdána. Čeká se na dodání posudků",
        ),
        State(
            code="defense_ready",
            name="Připravena k obhajobě",
            description="Práce je připravena k obhajobě."
        ),
        State(
            code="postponed",
            name="Odložena",
            description="Práce byla odložena na pozdější termín.",
        ),
        State(
            code="defended",
            name="Obhájena",
            description="Práce byla úspěšně obhájena",
        ),
        State(
            code="failed",
            name="Neobhájena",
            description="Práce nebyla úspěšně obhájena."
        )
    ])


def revert_migration(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(
        name__in=["Student", "Učitel"]
    ).delete()

    State = apps.get_model("submissions", "State")
    State.objects.filter(
        code__in=[
            "supervisor_approved", 
            "author_approved",
            "approved",
            "submitted",
            "defense_ready",
            "postponed",
            "defended",
            "failed",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(apply_migration, revert_migration),
    ]
