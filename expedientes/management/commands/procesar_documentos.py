from django.core.management.base import BaseCommand
from time import sleep

from expedientes.services import (
    confrontar_automaticamente,
    preparar_vistas,
    procesar_documento,
    recuperar_documentos_vencidos,
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
                self.procesar_vuelta()
                if not options["continuo"]:
                    break
                sleep(2)
        except KeyboardInterrupt:
            return

    def procesar_vuelta(self):
        recuperar_documentos_vencidos()
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
