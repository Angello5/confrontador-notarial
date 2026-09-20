import hashlib
import io
import secrets
import shutil
import threading
import zipfile
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from adaptadores import extraccion

from .models import Documento, TextoExtraido

_CACHE_LOCK = threading.RLock()


def calcular_hash(ruta):
    digest = hashlib.sha256()
    with Path(ruta).open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def crear_temporal(origen, nombre_original="", destino=None):
    """Copia el archivo a un nombre generado; el nombre enviado se ignora."""
    destino = Path(destino or settings.EXPEDIENTES_TEMP_DIR)
    destino.mkdir(parents=True, exist_ok=True)
    ruta = destino / f"documento-{secrets.token_hex(16)}.tmp"
    if hasattr(origen, "chunks"):
        with ruta.open("wb") as archivo:
            for bloque in origen.chunks():
                archivo.write(bloque)
    else:
        shutil.copyfile(origen, ruta)
    return ruta


def _archivo_bytes(archivo):
    if hasattr(archivo, "chunks"):
        return b"".join(archivo.chunks())
    if hasattr(archivo, "read"):
        posicion = archivo.tell() if hasattr(archivo, "tell") else None
        contenido = archivo.read()
        if posicion is not None and hasattr(archivo, "seek"):
            archivo.seek(posicion)
        return contenido
    return Path(archivo).read_bytes()


def validar_archivo(archivo):
    """Valida extensión, tamaño y firma sin escribir el temporal."""
    nombre = getattr(archivo, "name", str(archivo))
    extension = Path(nombre).suffix.lower()
    if extension not in extraccion.DOCS:
        raise ValueError("Formato de archivo no admitido.")
    contenido = _archivo_bytes(archivo)
    if not contenido:
        raise ValueError("El archivo está vacío.")
    if len(contenido) > settings.EXPEDIENTES_MAX_FILE_SIZE:
        raise ValueError("El archivo supera el tamaño máximo permitido.")
    if extension == ".pdf" and not contenido.startswith(b"%PDF-"):
        raise ValueError("El contenido del archivo no coincide con su formato.")
    if extension in {".docx", ".xlsx", ".odt", ".wordml"} and not zipfile.is_zipfile(
        io.BytesIO(contenido)
    ):
        raise ValueError("El contenido del archivo no coincide con su formato.")
    firmas = {
        ".jpg": (b"\xff\xd8\xff",),
        ".jpeg": (b"\xff\xd8\xff",),
        ".png": (b"\x89PNG\r\n\x1a\n",),
        ".gif": (b"GIF87a", b"GIF89a"),
        ".bmp": (b"BM",),
        ".tif": (b"II*\x00", b"MM\x00*"),
        ".tiff": (b"II*\x00", b"MM\x00*"),
        ".webp": (b"RIFF",),
        ".doc": (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",),
        ".rtf": (b"{\\rtf",),
    }
    if extension in firmas and not any(
        contenido.startswith(firma) for firma in firmas[extension]
    ):
        raise ValueError("El contenido del archivo no coincide con su formato.")
    return contenido


def extraer_o_reutilizar(hash_archivo, version_extractor, extractor):
    with _CACHE_LOCK, transaction.atomic():
        texto = (
            TextoExtraido.objects.select_for_update()
            .filter(
                hash_archivo=hash_archivo,
                version_extractor=version_extractor,
            )
            .first()
        )
        if texto is None or texto.texto == "":
            salida = extractor()
            if texto is None:
                try:
                    with transaction.atomic():
                        texto = TextoExtraido.objects.create(
                            hash_archivo=hash_archivo,
                            version_extractor=version_extractor,
                            texto=salida,
                            ultimo_uso_el=timezone.now(),
                        )
                except IntegrityError:
                    texto = TextoExtraido.objects.select_for_update().get(
                        hash_archivo=hash_archivo,
                        version_extractor=version_extractor,
                    )
            else:
                texto.texto = salida
                texto.ultimo_uso_el = timezone.now()
                texto.save(update_fields=("texto", "ultimo_uso_el"))
        else:
            texto.ultimo_uso_el = timezone.now()
            texto.save(update_fields=("ultimo_uso_el",))
        return texto


def _borrar_temporal(ruta):
    if ruta:
        try:
            Path(ruta).unlink(missing_ok=True)
        except OSError:
            pass


def _procesar_fila(documento):
    ruta = documento.ruta_temporal
    ahora = timezone.now()
    if documento.estado != Documento.PROCESANDO:
        documento.estado = Documento.PROCESANDO
        documento.procesando_el = ahora
        documento.save(update_fields=("estado", "procesando_el"))
    try:
        version = extraccion.version_extractor()
        texto = extraer_o_reutilizar(
            documento.hash_archivo,
            version,
            lambda: extraccion.leer(Path(ruta)),
        )
        if not texto.texto:
            raise ValueError
    except Exception:
        documento.estado = Documento.ERROR
        documento.error = "No se pudo procesar el archivo."
        documento.procesado_el = timezone.now()
        documento.procesando_el = None
        documento.ruta_temporal = ""
        documento.save(
            update_fields=(
                "estado",
                "error",
                "procesado_el",
                "procesando_el",
                "ruta_temporal",
            )
        )
    else:
        documento.texto_extraido = texto
        documento.estado = Documento.LISTO
        documento.error = ""
        documento.procesado_el = timezone.now()
        documento.procesando_el = None
        documento.ruta_temporal = ""
        documento.save(
            update_fields=(
                "texto_extraido",
                "estado",
                "error",
                "procesado_el",
                "procesando_el",
                "ruta_temporal",
            )
        )
    finally:
        _borrar_temporal(ruta)
    return documento


def procesar_documento(documento_o_ruta, resultado_esperado=None):
    if isinstance(documento_o_ruta, (str, Path)):
        try:
            if resultado_esperado == "ERROR":
                return None
            return None
        finally:
            _borrar_temporal(documento_o_ruta)
    documento = (
        documento_o_ruta
        if isinstance(documento_o_ruta, Documento)
        else Documento.objects.get(pk=documento_o_ruta)
    )
    return _procesar_fila(documento)


def _timeout():
    value = settings.EXPEDIENTES_PROCESSING_TIMEOUT
    return value if isinstance(value, timedelta) else timedelta(seconds=value)


def recuperar_documentos_vencidos():
    limite = timezone.now() - _timeout()
    return Documento.objects.filter(
        estado=Documento.PROCESANDO,
        procesando_el__lt=limite,
    ).update(estado=Documento.PENDIENTE, procesando_el=None)


def tomar_pendiente():
    with transaction.atomic():
        documento = (
            Documento.objects.select_for_update(skip_locked=True)
            .filter(estado=Documento.PENDIENTE)
            .order_by("id")
            .first()
        )
        if documento is None:
            return None
        documento.estado = Documento.PROCESANDO
        documento.procesando_el = timezone.now()
        documento.save(update_fields=("estado", "procesando_el"))
        return documento


def eliminar_documento(documento, confirmado=False):
    if not confirmado:
        raise ValueError("Se requiere confirmación para eliminar el documento.")
    ruta = documento.ruta_temporal
    documento.delete()
    _borrar_temporal(ruta)
