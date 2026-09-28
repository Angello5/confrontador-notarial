from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Expediente(models.Model):
    codigo = models.CharField(max_length=100, unique=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="expedientes_creados",
    )
    creado_el = models.DateTimeField(auto_now_add=True)
    actualizado_el = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.codigo = self.codigo.strip()
        super().save(*args, **kwargs)


class TextoExtraido(models.Model):
    hash_archivo = models.CharField(max_length=64, db_index=True)
    version_extractor = models.CharField(max_length=128)
    texto = models.TextField(blank=True)
    creado_el = models.DateTimeField(auto_now_add=True)
    ultimo_uso_el = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("hash_archivo", "version_extractor"),
                name="texto_hash_version_unicos",
            )
        ]


class Documento(models.Model):
    CLIENTE = "CLIENTE"
    MINUTA = "MINUTA"
    BORRADOR = "BORRADOR"
    ROLES_FUENTE = (CLIENTE, MINUTA)
    ROLES = (
        (CLIENTE, "Documentos del cliente"),
        (MINUTA, "Minuta"),
        (BORRADOR, "Proyecto (borrador)"),
    )

    PENDIENTE = "PENDIENTE"
    PROCESANDO = "PROCESANDO"
    LISTO = "LISTO"
    ERROR = "ERROR"
    ESTADOS = (
        (PENDIENTE, "Pendiente"),
        (PROCESANDO, "Procesando"),
        (LISTO, "Listo"),
        (ERROR, "Error"),
    )

    expediente = models.ForeignKey(
        Expediente, on_delete=models.CASCADE, related_name="documentos"
    )
    rol = models.CharField(max_length=10, choices=ROLES)
    nombre_original = models.CharField(max_length=255)
    hash_archivo = models.CharField(max_length=64, db_index=True)
    tamano_bytes = models.PositiveBigIntegerField(validators=[MinValueValidator(1)])
    estado = models.CharField(max_length=12, choices=ESTADOS, default=PENDIENTE)
    error = models.TextField(blank=True, default="")
    ruta_temporal = models.TextField(blank=True, default="")
    texto_extraido = models.ForeignKey(
        TextoExtraido,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="documentos",
    )
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="documentos_subidos",
    )
    subido_el = models.DateTimeField(auto_now_add=True)
    procesando_el = models.DateTimeField(null=True, blank=True)
    procesado_el = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("expediente", "rol", "hash_archivo"),
                name="documento_expediente_rol_hash_unicos",
            ),
            models.CheckConstraint(
                condition=Q(tamano_bytes__gt=0),
                name="documento_tamano_positivo",
            ),
        ]


class AplicacionCorreccion(models.Model):
    """F21: registro inmutable de una confirmación de correcciones.

    ``huella_corrida`` se enlazará a la Corrida de F20 al integrar (plan.md).
    """

    borrador = models.ForeignKey(
        Documento,
        null=True,
        on_delete=models.SET_NULL,
        related_name="aplicaciones_correccion",
    )
    huella_corrida = models.CharField(max_length=64, db_index=True)
    confirmado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="correcciones_confirmadas",
    )
    confirmado_el = models.DateTimeField(auto_now_add=True)
    aplicadas = models.JSONField(default=list)
    excluidas = models.JSONField(default=list)
    no_aplicadas = models.JSONField(default=list)
    corregido_hash = models.CharField(max_length=64)

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError("La aplicación de correcciones es inmutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("La aplicación de correcciones es inmutable.")
