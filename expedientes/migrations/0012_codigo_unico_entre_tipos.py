from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("expedientes", "0011_tipo_vehicular"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="expediente",
            name="expediente_codigo_activo_unico",
        ),
        migrations.AddConstraint(
            model_name="expediente",
            constraint=models.UniqueConstraint(
                condition=models.Q(("archivado_el__isnull", True)),
                fields=("codigo",),
                name="expediente_codigo_activo_unico",
            ),
        ),
    ]
