from django.core.management.base import BaseCommand

from expedientes.services import (
    procesar_documento,
    recuperar_documentos_vencidos,
    tomar_pendiente,
)


class Command(BaseCommand):
    help = "Procesa los documentos pendientes de extracción."

    def handle(self, *args, **options):
        recuperar_documentos_vencidos()
        procesados = 0
        while documento := tomar_pendiente():
            procesar_documento(documento)
            procesados += 1
        self.stdout.write(f"Documentos procesados: {procesados}")
