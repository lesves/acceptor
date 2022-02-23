# Generated by Django 4.0 on 2022-02-18 15:49

from django.db import migrations
from django.contrib.auth.management import create_permissions


def apply_migration(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.bulk_create([
        Group(name="Studenti"),
        Group(name="Učitelé"),
    ])

    # Need this to create permissions beforehand
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, verbosity=0)
        app_config.models_module = None

    Permission = apps.get_model("auth", "Permission")
    Group.objects.get(name="Studenti").permissions.add(
        Permission.objects.get(codename="add_thesis"),
        Permission.objects.get(codename="view_thesis"),
        Permission.objects.get(codename="author"),
    )
    Group.objects.get(name="Učitelé").permissions.add(
        Permission.objects.get(codename="add_thesis"),
        Permission.objects.get(codename="view_thesis"),
        Permission.objects.get(codename="change_thesis"),
        Permission.objects.get(codename="delete_thesis"),
        *Permission.objects.filter(codename__in=["supervisor", "opponent"])
    )

    State = apps.get_model("submissions", "State")
    State.objects.bulk_create([
        State(
            code="supervisor_approved",
            name="Vedoucí schválil", 
            description="Zadání práce bylo schválené vedoucím. Čeká se na schválení autorem.",
            is_approved=False,
        ),
        State(
            code="author_approved",
            name="Autor schválil",
            description="Zadání práce bylo schválené autorem. Čeká se na schválení vedoucím.",
            is_approved=False,
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
            is_closed=True,
            is_public=True,
        ),
        State(
            code="failed",
            name="Neobhájena",
            description="Práce nebyla úspěšně obhájena.",
            is_closed=True,
        )
    ])


def revert_migration(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(
        name__in=["Studenti", "Učitelé"]
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
