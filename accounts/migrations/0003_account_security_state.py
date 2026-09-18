from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_seed_roles")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="force_password_change",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="session_version",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
