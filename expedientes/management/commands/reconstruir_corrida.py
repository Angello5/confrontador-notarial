from django.core.management.base import BaseCommand, CommandError

from expedientes.models import Corrida
from expedientes.services import CorridaNoReconstruible, reconstruir_corrida


class Command(BaseCommand):
    help = "Repite una corrida desde su manifiesto y compara la huella de hallazgos."

    def add_arguments(self, parser):
        parser.add_argument("corrida_id", type=int)

    def handle(self, *args, **options):
        try:
            corrida = Corrida.objects.select_related("expediente").get(
                pk=options["corrida_id"]
            )
        except Corrida.DoesNotExist as exc:
            raise CommandError("La corrida no existe.") from exc
        try:
            informe = reconstruir_corrida(corrida)
        except CorridaNoReconstruible as exc:
            raise CommandError(f"NO RECONSTRUIBLE: {exc}") from exc
        for aviso in informe["avisos"]:
            self.stdout.write(aviso)
        if not informe["conforme"]:
            raise CommandError(
                f"DIFERENTE: huella registrada {corrida.huella}, reconstruida "
                f"{informe['huella']}; hallazgos reconstruidos {informe['total']}."
            )
        self.stdout.write(f"CONFORME: huella {corrida.huella}")
