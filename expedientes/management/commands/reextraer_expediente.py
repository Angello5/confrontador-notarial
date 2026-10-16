from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from expedientes import services
from expedientes.models import Documento, Expediente


def _archivo(documento):
    """El temporal si aún existe; si no, el borrador original conservado (F21)."""
    candidatas = [documento.ruta_temporal]
    # F21 aún no está en esta rama; al integrarse, ``ruta_original`` existe.
    if documento.rol == Documento.BORRADOR and hasattr(services, "ruta_original"):
        candidatas.append(services.ruta_original(documento))
    return next((Path(r) for r in candidatas if r and Path(r).is_file()), None)


class Command(BaseCommand):
    help = "Vuelve a poner en cola la extracción de los documentos de un expediente."

    def add_arguments(self, parser):
        parser.add_argument("codigo")

    def handle(self, *args, **options):
        # F50: un archivado puede repetir el código del activo (F28); se releen
        # los documentos de todos.
        documentos = Documento.objects.filter(
            expediente__codigo=options["codigo"]
        ).order_by("id")
        if not Expediente.objects.filter(codigo=options["codigo"]).exists():
            raise CommandError("El expediente no existe.")

        encolados = 0
        for documento in documentos:
            archivo = _archivo(documento)
            if archivo is None:
                self.stdout.write(f"Sin archivo: {documento.nombre_original}")
                continue
            # Copia: el worker borra el temporal al terminar y el original no se toca.
            temporal = services.crear_temporal(archivo, documento.nombre_original)
            anterior = documento.ruta_temporal
            with transaction.atomic():
                documento.ruta_temporal = str(temporal)
                documento.estado = Documento.PENDIENTE
                documento.procesando_el = None
                documento.save(
                    update_fields=("ruta_temporal", "estado", "procesando_el")
                )
            if anterior and Path(anterior) != temporal:
                services._borrar_temporal(anterior)
            encolados += 1
        self.stdout.write(f"En cola: {encolados}")
