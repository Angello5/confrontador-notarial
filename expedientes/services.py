import hashlib
import io
import logging
import os
import secrets
import shutil
import zipfile
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from adaptadores import extraccion
from adaptadores import diccionario
from nucleo import ortografia, verificar

from .models import Documento, Expediente, TextoExtraido

logger = logging.getLogger(__name__)

ESTADOS_VISIBLES = {
    Documento.PENDIENTE: "Pendiente",
    Documento.PROCESANDO: "Procesando",
    Documento.LISTO: "Listo",
    Documento.ERROR: "No se pudo procesar",
}

_UMBRAL_PARRAFO = 88


class DocumentoDuplicado(ValueError):
    """El hash y rol ya están registrados en el expediente."""


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
    destino.chmod(0o700)
    ruta = destino / f"documento-{secrets.token_hex(16)}.tmp"
    if hasattr(origen, "chunks"):
        with ruta.open("wb") as archivo:
            for bloque in origen.chunks():
                archivo.write(bloque)
    else:
        shutil.copyfile(origen, ruta)
    return ruta


def registrar_documento(expediente, archivo, rol, usuario):
    """Valida que el temporal persistido solo sobreviva si se crea la fila."""
    temporal = crear_temporal(archivo, archivo.name)
    persistido = False
    try:
        hash_archivo = calcular_hash(temporal)
        try:
            with transaction.atomic():
                documento = Documento.objects.create(
                    expediente=expediente,
                    rol=rol,
                    nombre_original=Path(archivo.name).name,
                    hash_archivo=hash_archivo,
                    tamano_bytes=archivo.size,
                    ruta_temporal=str(temporal),
                    subido_por=usuario,
                )
        except IntegrityError as exc:
            raise DocumentoDuplicado from exc
        persistido = True
        return documento
    finally:
        if not persistido:
            temporal.unlink(missing_ok=True)


def _archivo_tamano(archivo):
    tamano = getattr(archivo, "size", None)
    if isinstance(tamano, int):
        return tamano
    try:
        return Path(archivo).stat().st_size
    except (OSError, TypeError):
        pass
    try:
        return os.fstat(archivo.fileno()).st_size
    except (AttributeError, OSError, ValueError):
        return None


def _archivo_prefijo(archivo, limite=16):
    if hasattr(archivo, "read"):
        posicion = archivo.tell() if hasattr(archivo, "tell") else None
        prefijo = archivo.read(limite)
        if posicion is not None and hasattr(archivo, "seek"):
            archivo.seek(posicion)
        return prefijo
    if hasattr(archivo, "chunks"):
        return next(archivo.chunks(), b"")[:limite]
    return Path(archivo).read_bytes()[:limite]


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
    tamano = _archivo_tamano(archivo)
    if tamano is not None and tamano > settings.EXPEDIENTES_MAX_FILE_SIZE:
        raise ValueError("El archivo supera el tamaño máximo permitido.")
    extensiones_zip = {".docx", ".xlsx", ".odt", ".wordml"}
    contenido = (
        _archivo_bytes(archivo)
        if extension in extensiones_zip
        else _archivo_prefijo(archivo)
    )
    if not contenido or (tamano is not None and tamano == 0):
        raise ValueError("El archivo está vacío.")
    if len(contenido) > settings.EXPEDIENTES_MAX_FILE_SIZE:
        raise ValueError("El archivo supera el tamaño máximo permitido.")
    if extension == ".pdf" and not contenido.startswith(b"%PDF-"):
        raise ValueError("El contenido del archivo no coincide con su formato.")
    if extension in extensiones_zip and not zipfile.is_zipfile(io.BytesIO(contenido)):
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
    with transaction.atomic():
        texto = TextoExtraido.objects.filter(
            hash_archivo=hash_archivo, version_extractor=version_extractor
        ).first()
        if texto is not None and texto.texto != "":
            texto.ultimo_uso_el = timezone.now()
            texto.save(update_fields=("ultimo_uso_el",))
            return texto

    salida = extractor()
    with transaction.atomic():
        if texto is not None:
            texto = TextoExtraido.objects.select_for_update().get(pk=texto.pk)
            if texto.texto == "":
                texto.texto = salida
            texto.ultimo_uso_el = timezone.now()
            texto.save(update_fields=("texto", "ultimo_uso_el"))
            return texto
        try:
            with transaction.atomic():
                return TextoExtraido.objects.create(
                    hash_archivo=hash_archivo,
                    version_extractor=version_extractor,
                    texto=salida,
                    ultimo_uso_el=timezone.now(),
                )
        except IntegrityError:
            return TextoExtraido.objects.select_for_update().get(
                hash_archivo=hash_archivo, version_extractor=version_extractor
            )


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
    except Exception as exc:
        logger.error(
            "Falló el procesamiento del documento id=%s tipo=%s",
            documento.pk,
            type(exc).__name__,
        )
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


def procesar_documento(documento_o_id):
    documento = (
        documento_o_id
        if isinstance(documento_o_id, Documento)
        else Documento.objects.get(pk=documento_o_id)
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


def resumen_expediente(expediente):
    """Devuelve el estado derivado y contadores que puede mostrar la UI."""
    estados = list(expediente.documentos.values_list("estado", flat=True))
    contadores = {
        "total": len(estados),
        "pendientes": estados.count(Documento.PENDIENTE),
        "procesando": estados.count(Documento.PROCESANDO),
        "listos": estados.count(Documento.LISTO),
        "errores": estados.count(Documento.ERROR),
    }
    if not estados:
        estado = "VACIO"
    elif Documento.ERROR in estados:
        estado = Documento.ERROR
    elif any(
        estado_documento in estados
        for estado_documento in (Documento.PENDIENTE, Documento.PROCESANDO)
    ):
        estado = Documento.PROCESANDO
    else:
        estado = Documento.LISTO
    return {"estado": estado, **contadores}


def resumen_documento(documento):
    """Reduce un Documento al conjunto seguro que necesita el endpoint."""
    error = (
        "No se pudo procesar el archivo." if documento.estado == Documento.ERROR else ""
    )
    return {
        "id": documento.pk,
        "rol": documento.rol,
        "estado": documento.estado,
        "estado_texto": ESTADOS_VISIBLES[documento.estado],
        "error": error,
        "subido_el": documento.subido_el.isoformat() if documento.subido_el else None,
        "procesando_el": (
            documento.procesando_el.isoformat() if documento.procesando_el else None
        ),
        "procesado_el": (
            documento.procesado_el.isoformat() if documento.procesado_el else None
        ),
    }


def _texto_listo(documento):
    if documento.estado != Documento.LISTO or documento.texto_extraido_id is None:
        return None
    texto = documento.texto_extraido.texto
    return texto if texto else None


def _resultado_no_disponible(mensaje):
    return {
        "estado": "NO_DISPONIBLE",
        "mensaje": mensaje,
        "regla": [],
        "ortografia": [],
    }


def estado_confrontacion(expediente, borrador, fuentes=None):
    """Indica si el borrador tiene los textos necesarios para confrontar."""
    if fuentes is None:
        fuentes = list(
            expediente.documentos.filter(rol=Documento.FUENTE).order_by("pk")
        )
    if borrador.rol != Documento.BORRADOR or not fuentes:
        return {
            "disponible": False,
            "mensaje": "Cargue al menos una fuente y un borrador para confrontar.",
        }
    if borrador.estado in (Documento.PENDIENTE, Documento.PROCESANDO) or any(
        fuente.estado in (Documento.PENDIENTE, Documento.PROCESANDO)
        for fuente in fuentes
    ):
        return {
            "disponible": False,
            "mensaje": "Espere a que termine la extracción de los documentos.",
        }
    if borrador.estado == Documento.ERROR or any(
        fuente.estado == Documento.ERROR for fuente in fuentes
    ):
        return {
            "disponible": False,
            "mensaje": "No se pudo procesar un documento. Elimínelo y vuelva a subirlo.",
        }
    if _texto_listo(borrador) is None:
        return {
            "disponible": False,
            "mensaje": "El texto del borrador ya no está disponible. Vuelva a subirlo para confrontar.",
        }
    if any(_texto_listo(fuente) is None for fuente in fuentes):
        return {
            "disponible": False,
            "mensaje": "El texto de una fuente ya no está disponible. Vuelva a subirla para confrontar.",
        }
    return {"disponible": True, "mensaje": ""}


def confrontar_borrador(expediente, borrador):
    """Ejecuta regla y ortografía sobre un borrador listo, sin persistir."""
    if borrador.expediente_id != expediente.pk or borrador.rol != Documento.BORRADOR:
        raise ValueError("El documento no es un borrador de este expediente.")

    fuentes_documentos = list(
        expediente.documentos.filter(rol=Documento.FUENTE).order_by("pk")
    )
    disponibilidad = estado_confrontacion(expediente, borrador, fuentes_documentos)
    if not disponibilidad["disponible"]:
        return _resultado_no_disponible(disponibilidad["mensaje"])

    fuentes = {
        documento.nombre_original: documento.texto_extraido.texto
        for documento in fuentes_documentos
    }
    texto_borrador = borrador.texto_extraido.texto
    aviso = verificar.diagnostico(fuentes, texto_borrador)
    if aviso:
        return {
            "estado": "ADVERTENCIA_CORRESPONDENCIA",
            "mensaje": aviso,
            "regla": [],
            "ortografia": [],
        }

    catalogo = verificar.catalogo(fuentes)
    reglas = verificar.revisar(catalogo, texto_borrador, _UMBRAL_PARRAFO)
    minutas = [
        texto
        for nombre, texto in fuentes.items()
        if Path(nombre).suffix.lower() not in verificar.IMGS
    ]
    reglas.extend(verificar.revisar_parrafos(minutas, texto_borrador, _UMBRAL_PARRAFO))
    try:
        dic, lemas = diccionario.diccionario()
    except diccionario.DiccionarioNoAprovisionado:
        return _resultado_no_disponible(
            "Falta aprovisionar el diccionario es_PE antes de iniciar el servicio."
        )
    propios = {palabra for nombre in catalogo["NOMBRE"] for palabra in nombre.split()}
    faltas = ortografia.revisar(
        texto_borrador,
        dic,
        lemas,
        diccionario.lista_casa(),
        propios,
    )
    return {
        "estado": "RESULTADO",
        "mensaje": "",
        "regla": reglas,
        "ortografia": faltas,
    }


def usuario_puede_ver_expediente(usuario, expediente):
    if not usuario.is_authenticated:
        return False
    if usuario.groups.filter(name="Administrador").exists():
        return True
    return (
        expediente.creado_por_id == usuario.pk
        and usuario.groups.filter(name="Usuario").exists()
    )


def expedientes_visibles(usuario):
    queryset = Expediente.objects.all()
    if usuario.groups.filter(name="Administrador").exists():
        return queryset
    return queryset.filter(creado_por=usuario)
