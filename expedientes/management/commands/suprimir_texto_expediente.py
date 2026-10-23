from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from expedientes.models import Documento, Expediente, TextoExtraido
from expedientes.sentido import suprimir as suprimir_sentido
from expedientes.services import borrar_originales


class Command(BaseCommand):
    help = "Suprime el texto extraído y los borradores conservados de un expediente."

    def add_arguments(self, parser):
        parser.add_argument("codigo")

    def handle(self, *args, **options):
        # F50: decisión del usuario (2026-10-16): solo el activo, nunca un
        # archivado que repita el código (F28).
        try:
            expediente = Expediente.objects.get(
                codigo=options["codigo"], archivado_el__isnull=True
            )
        except Expediente.DoesNotExist as exc:
            raise CommandError(
                "No hay un expediente activo con ese código. No se suprimió nada."
            ) from exc
        except Expediente.MultipleObjectsReturned as exc:
            raise CommandError(
                "Hay un kardex y una transferencia vehicular activos con ese código."
                " No se suprimió nada."
            ) from exc

        with transaction.atomic():
            textos = TextoExtraido.objects.filter(
                documentos__expediente=expediente
            ).distinct()
            afectados = (
                Documento.objects.filter(texto_extraido__in=textos)
                .values("expediente_id")
                .distinct()
                .count()
            )
            claves = list(textos.values_list("hash_archivo", "version_extractor"))
            textos.update(texto="", calidad={})
            # F61: las anotaciones de sentido guardan oraciones de estos textos.
            # Después de vaciarlos: un análisis en curso bloquea los textos al
            # guardar, así que su registro ya está a la vista o verá el texto vacío.
            suprimir_sentido(claves)
        borrar_originales(expediente.pk)
        solicitado = min(afectados, 1)
        self.stdout.write(
            f"Expediente solicitado incluido: {solicitado}; "
            f"Otros expedientes que compartían el texto: {afectados - solicitado}"
        )
