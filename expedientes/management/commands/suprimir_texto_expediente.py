from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from expedientes.models import Documento, Expediente, TextoExtraido
from expedientes.services import borrar_originales


class Command(BaseCommand):
    help = "Suprime el texto extraído y los borradores conservados de un expediente."

    def add_arguments(self, parser):
        parser.add_argument("codigo")

    def handle(self, *args, **options):
        try:
            expediente = Expediente.objects.get(codigo=options["codigo"])
        except Expediente.DoesNotExist as exc:
            raise CommandError("El expediente no existe.") from exc

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
            textos.update(texto="")
        borrar_originales(expediente.pk)
        solicitado = min(afectados, 1)
        self.stdout.write(
            f"Expediente solicitado incluido: {solicitado}; "
            f"Otros expedientes que compartían el texto: {afectados - solicitado}"
        )
