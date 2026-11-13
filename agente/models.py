from django.conf import settings
from django.db import models


class ConsultaAgente(models.Model):
    """Auditoría (constitución VI): quién consultó, con cuántos adjuntos y cuándo.
    Nunca guarda la pregunta ni la respuesta: pueden traer datos personales."""

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    adjuntos = models.PositiveSmallIntegerField(default=0)
    proveedor = models.CharField(max_length=10)
    ok = models.BooleanField()
    segundos = models.PositiveIntegerField()
    creada_el = models.DateTimeField(auto_now_add=True)
