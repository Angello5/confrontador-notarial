from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from adaptadores.modelos_sentido import verificar, version


class Command(BaseCommand):
    help = "F61: verifica los modelos de la capa de sentido contra su SHA-256."

    def handle(self, *args, **options):
        problemas = verificar(settings.SENTIDO_MODELOS_DIR)
        if problemas:
            raise CommandError(
                "Modelos de la capa de sentido incompletos: " + "; ".join(problemas)
            )
        estado = "activa" if settings.SENTIDO_ACTIVO else "apagada (SENTIDO_ACTIVO)"
        self.stdout.write(f"Modelos verificados ({version()}). Capa {estado}.")
