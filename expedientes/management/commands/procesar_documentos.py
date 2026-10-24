from contextlib import suppress
from time import sleep

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError, connections

from expedientes.sentido import analizar_pendientes
from expedientes.services import (
    confrontar_automaticamente,
    preparar_vistas,
    procesar_documento,
    recuperar_documentos_vencidos,
    releer_borradores_desactualizados,
    tomar_pendiente,
)


class Command(BaseCommand):
    help = "Procesa los documentos pendientes de extracción."

    def add_arguments(self, parser):
        parser.add_argument(
            "--continuo",
            action="store_true",
            help="Mantiene el proceso activo y reutiliza modelos.",
        )

    def handle(self, *args, **options):
        try:
            while True:
                try:
                    self.procesar_vuelta()
                except DatabaseError:
                    if not options["continuo"]:
                        raise
                    # F63: la base se reinició o cortó la conexión. Se descarta la
                    # conexión rota y la próxima vuelta abre otra.
                    self.stderr.write(
                        "Sin conexión con la base de datos; se reintenta."
                    )
                    with suppress(DatabaseError):
                        connections.close_all()
                if not options["continuo"]:
                    break
                sleep(2)
        except KeyboardInterrupt:
            return

    def procesar_vuelta(self):
        if settings.ERP_ESTADO_DIR:
            # F8: latido para el aviso «procesamiento no activo»; si no se puede
            # escribir, el propio aviso lo hace visible.
            with suppress(OSError):
                (settings.ERP_ESTADO_DIR / "worker.latido").touch()
        recuperar_documentos_vencidos()
        releer_borradores_desactualizados()
        procesados = 0
        diferidos = []
        confrontar_automaticamente(limite=1)
        preparar_vistas(limite=1)
        while documento := (
            tomar_pendiente(excluir=diferidos) if diferidos else tomar_pendiente()
        ):
            if procesar_documento(documento) is None:
                diferidos.append(documento.pk)
            else:
                procesados += 1
            confrontar_automaticamente(limite=1)
            preparar_vistas(limite=1)
        self.stdout.write(f"Documentos procesados: {procesados}")
        confrontar_automaticamente()
        preparar_vistas()
        # F61: después de las reglas, una corrida por vuelta (la capa de sentido
        # tarda más y no debe frenar la lectura de documentos).
        analizar_pendientes(limite=1)
