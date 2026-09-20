from datetime import timedelta
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from expedientes.models import Documento


class Command(BaseCommand):
    help = "Elimina temporales huérfanos con más de 24 horas."

    def handle(self, *args, **options):
        limite = timezone.now() - timedelta(hours=24)
        eliminados = 0
        documentos = Documento.objects.filter(
            ruta_temporal__gt="", subido_el__lt=limite
        ).exclude(estado=Documento.PROCESANDO)
        for documento in documentos.iterator():
            try:
                Path(documento.ruta_temporal).unlink(missing_ok=True)
            except OSError:
                continue
            documento.ruta_temporal = ""
            documento.save(update_fields=("ruta_temporal",))
            eliminados += 1
        self.stdout.write(f"Temporales eliminados: {eliminados}")
