import shutil
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from expedientes.models import Documento


class Command(BaseCommand):
    help = "Elimina temporales referenciados antiguos y huérfanos."

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

        referenciados = {
            Path(ruta).resolve()
            for ruta in Documento.objects.filter(ruta_temporal__gt="").values_list(
                "ruta_temporal", flat=True
            )
        }
        huerfanos_eliminados = 0
        try:
            temporales = tuple(Path(settings.EXPEDIENTES_TEMP_DIR).iterdir())
        except OSError:
            temporales = ()
        for temporal in temporales:
            try:
                # Carpeta de una conversión cortada (worker detenido a mitad).
                if (
                    temporal.is_dir()
                    and temporal.name.startswith("tmp")
                    and temporal.stat().st_mtime < limite.timestamp()
                ):
                    shutil.rmtree(temporal)
                    huerfanos_eliminados += 1
                    continue
                if (
                    not temporal.is_file()
                    or temporal.resolve() in referenciados
                    or temporal.stat().st_mtime >= limite.timestamp()
                ):
                    continue
                temporal.unlink()
            except OSError:
                continue
            huerfanos_eliminados += 1

        total = eliminados + huerfanos_eliminados
        self.stdout.write(
            "Temporales referenciados eliminados: "
            f"{eliminados}; Temporales huérfanos eliminados: "
            f"{huerfanos_eliminados}; Total de temporales eliminados: {total}"
        )
