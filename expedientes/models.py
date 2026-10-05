from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
import uuid


class Expediente(models.Model):
    codigo = models.CharField(max_length=100)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="expedientes_creados",
    )
    creado_el = models.DateTimeField(auto_now_add=True)
    actualizado_el = models.DateTimeField(auto_now=True)
    # F25: "Eliminar" archiva; el manifiesto de auditoría es inmutable.
    archivado_el = models.DateTimeField(null=True, blank=True)
    archivado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="expedientes_archivados",
    )

    class Meta:
        # F28: el código es único solo entre expedientes activos.
        constraints = [
            models.UniqueConstraint(
                fields=("codigo",),
                condition=Q(archivado_el__isnull=True),
                name="expediente_codigo_activo_unico",
            )
        ]

    def save(self, *args, **kwargs):
        self.codigo = self.codigo.strip()
        super().save(*args, **kwargs)


class TextoExtraido(models.Model):
    hash_archivo = models.CharField(max_length=64, db_index=True)
    version_extractor = models.CharField(max_length=128)
    texto = models.TextField(blank=True)
    calidad = models.JSONField(default=dict, blank=True)
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
        (CLIENTE, "Recaudos"),
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
    metricas = models.JSONField(default=dict, blank=True)

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


class SolicitudConfrontacion(models.Model):
    borrador = models.OneToOneField(
        Documento, on_delete=models.CASCADE, related_name="solicitud"
    )
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    token = models.UUIDField(default=uuid.uuid4)
    estado = models.CharField(
        max_length=12,
        default="PENDIENTE",
        choices=[
            (estado, estado)
            for estado in (
                "PENDIENTE",
                "PROCESANDO",
                "LISTO",
                "ERROR",
                "CANCELADA",
                "CAMBIADA",
            )
        ],
    )
    explicita = models.BooleanField(default=True)
    solicitada_el = models.DateTimeField(auto_now_add=True)
    actualizada_el = models.DateTimeField(auto_now=True)


class RegistroInmutable(Exception):
    """Un registro de auditoría no se modifica ni se borra."""


class _InmutableQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise RegistroInmutable("Registro de auditoría inmutable.")

    def delete(self):
        raise RegistroInmutable("Registro de auditoría inmutable.")


class Inmutable(models.Model):
    objects = _InmutableQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise RegistroInmutable("Registro de auditoría inmutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RegistroInmutable("Registro de auditoría inmutable.")


class Corrida(Inmutable):
    """Manifiesto de una confrontación (Anexo A, capa 7)."""

    RESULTADO = "RESULTADO"
    ADVERTENCIA = "ADVERTENCIA"
    NO_DISPONIBLE = "NO_DISPONIBLE"
    ERROR = "ERROR"
    ESTADOS = (
        (RESULTADO, "Resultado"),
        (ADVERTENCIA, "Advertencia"),
        (NO_DISPONIBLE, "No disponible"),
        (ERROR, "Error"),
    )
    AUTOMATICA = "AUTOMATICA"
    MANUAL = "MANUAL"
    ORIGENES = ((AUTOMATICA, "Automática"), (MANUAL, "Manual"))

    expediente = models.ForeignKey(
        Expediente, on_delete=models.PROTECT, related_name="corridas"
    )
    id_borrador = models.PositiveBigIntegerField()
    hash_borrador = models.CharField(max_length=64)
    # Borrador y fuentes en el orden usado: rol, nombre, hash_archivo,
    # version_extractor, hash_texto y estado del documento.
    entradas = models.JSONField()
    version_catalogo = models.CharField(max_length=64)
    version_software = models.CharField(max_length=32)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="corridas"
    )
    creado_el = models.DateTimeField(auto_now_add=True)
    fecha_referencia = models.DateField()
    estado = models.CharField(max_length=14, choices=ESTADOS)
    hallazgos = models.TextField()
    huella = models.CharField(max_length=64)
    origen = models.CharField(max_length=10, choices=ORIGENES, default=MANUAL)
    # Resumen de extracción y aviso lingüístico para mostrar el resultado sin
    # recalcular; fuera de la huella.
    presentacion = models.JSONField(default=dict)


class DecisionCorreccion(Inmutable):
    """Decisión sobre las correcciones de una corrida (fase de corrección)."""

    corrida = models.ForeignKey(
        Corrida, on_delete=models.PROTECT, related_name="decisiones"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="decisiones_correccion",
    )
    creado_el = models.DateTimeField(auto_now_add=True)
    correcciones_excluidas = models.JSONField(default=list, blank=True)
    # F21: {id: apariciones aplicadas} (A.3), ids no ubicados en el documento y
    # SHA-256 del documento corregido.
    apariciones = models.JSONField(default=dict, blank=True)
    correcciones_no_aplicadas = models.JSONField(default=list, blank=True)
    hash_corregido = models.CharField(max_length=64, blank=True)

    @property
    def correcciones_aplicadas(self):
        return list(self.apariciones)
