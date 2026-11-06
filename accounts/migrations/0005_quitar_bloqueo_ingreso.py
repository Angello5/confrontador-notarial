# El bloqueo por intentos fallidos se retiró a pedido de la notaría (2026-10-24).

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_login_lockout"),
    ]

    operations = [
        migrations.RemoveField(model_name="user", name="failed_login_attempts"),
        migrations.RemoveField(model_name="user", name="login_locked_until"),
    ]
