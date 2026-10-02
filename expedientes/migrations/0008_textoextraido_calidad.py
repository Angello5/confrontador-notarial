from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("expedientes", "0007_expediente_codigo_activo_unico")]
    operations = [
        migrations.AddField(
            model_name="textoextraido",
            name="calidad",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
