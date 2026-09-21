from django.db import migrations, models


def convertir_fuente_a_cliente(apps, schema_editor):
    Documento = apps.get_model("expedientes", "Documento")
    Documento.objects.filter(rol="FUENTE").update(rol="CLIENTE")


def revertir_cliente_a_fuente(apps, schema_editor):
    Documento = apps.get_model("expedientes", "Documento")
    Documento.objects.filter(rol__in=("CLIENTE", "MINUTA")).update(rol="FUENTE")


class Migration(migrations.Migration):
    dependencies = [("expedientes", "0001_initial")]

    operations = [
        migrations.RunPython(convertir_fuente_a_cliente, revertir_cliente_a_fuente),
        migrations.AlterField(
            model_name="documento",
            name="rol",
            field=models.CharField(
                choices=[
                    ("CLIENTE", "Documentos del cliente"),
                    ("MINUTA", "Minuta"),
                    ("BORRADOR", "Proyecto (borrador)"),
                ],
                max_length=10,
            ),
        ),
    ]
