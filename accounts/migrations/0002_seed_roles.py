from django.db import migrations


ROLE_NAMES = ("Administrador", "Usuario")


def create_roles(apps, schema_editor):
    group = apps.get_model("auth", "Group")
    for name in ROLE_NAMES:
        group.objects.using(schema_editor.connection.alias).get_or_create(name=name)


def remove_roles(apps, schema_editor):
    group = apps.get_model("auth", "Group")
    group.objects.using(schema_editor.connection.alias).filter(
        name__in=ROLE_NAMES
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [migrations.RunPython(create_roles, remove_roles)]
