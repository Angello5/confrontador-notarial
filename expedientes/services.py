import hashlib
import io
import json
import logging
import os
import re
import secrets
import shutil
import tomllib
import unicodedata
import zipfile
from collections import Counter
from datetime import date, datetime, time, timedelta
from pathlib import Path
from time import perf_counter

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.db.models import Count, DateField, F, Max, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce, TruncMonth, TruncWeek
from django.urls import reverse

from .bloqueos import exclusivo

from adaptadores import diccionario, docx_corregido, extraccion, paginas
from nucleo import correccion, ortografia, vehicular, verificar

from .models import Corrida, DecisionCorreccion, Documento, Expediente, TextoExtraido

logger = logging.getLogger(__name__)

ESTADOS_VISIBLES = {
    Documento.PENDIENTE: "Pendiente",
    Documento.PROCESANDO: "Procesando",
    Documento.LISTO: "Listo",
    Documento.ERROR: "No se pudo procesar",
}

_UMBRAL_PARRAFO = 88
_CAMPOS_CATALOGO = ("NOMBRE", "DNI", "PARTIDA", "MONTO")
_ESTADOS_PERSONA = {
    "CONFIRMADA": "Confirmada",
    "SIN_DOCUMENTO": "Sin documento",
    "REVISION_MANUAL": "Revisión manual",
    "SIN_FICHA": "Sin ficha",
}

_RE_OBSERVACION_CAMPO = re.compile(
    r"^\[(?P<campo>[^]]+)\]\s+«(?P<hallado>[^»]*)»\s+(?P<resto>.*)$"
)
_RE_OBSERVACION_PARRAFO = re.compile(
    r"^\[PARRAFO\]\s+(?P<tipo>falta o alterado|falta)"
    r"(?:\s+\((?P<porcentaje>[\d.]+)%\))?:\s*(?P<fragmento>.*)$",
    re.IGNORECASE,
)
_RE_OBSERVACION_FALTA = re.compile(
    r"^\[(?P<campo>[^]]+)\]\s+FALTA:\s+«(?P<esperado>[^»]*)»",
    re.IGNORECASE,
)
_RE_OBSERVACION_SIN_COMPROBAR = re.compile(
    r"^\[(?P<campo>[^]]+)\]\s+SIN COMPROBAR:\s+«(?P<esperado>[^»]*)»"
)
_RE_DEBE_DECIR = re.compile(
    r"^debe decir\s+«(?P<esperado>[^»]*)»(?P<resto>.*)$", re.IGNORECASE
)
_RE_MOTIVO_CARATULA = re.compile(r"\s+(?P<motivo>\(caratula\))\s*$", re.IGNORECASE)
# F64: lo que dice la minuta y la sugerencia, al final de estas observaciones
_CON_SUGERENCIA = {"NUMERO_EN_LETRAS", "AREA", "COPROPIEDAD"}
_RE_DETALLE = re.compile(r"^\s+\((?P<detalle>.*)\)\s*$")
# F39: el aviso de persona sin ficha conserva cómo escribe la minuta el nombre
_RE_MINUTA_DICE = re.compile(r"; la minuta dice «[^»]*»")
_RE_MOTIVO_MONTO = re.compile(
    r"\s+\(concepto: (?P<concepto>[^;]*); fuente: (?P<archivo>.*), p\. (?P<pagina>\d+)\)\s*$"
)


class DocumentoDuplicado(ValueError):
    """El hash y rol ya están registrados en el expediente."""


class CorreccionNoAplicable(ValueError):
    """La corrida confirmada ya no coincide o el borrador no admite corrección."""


def _carpeta_originales(expediente_id):
    return Path(settings.EXPEDIENTES_ORIGINALES_DIR) / str(expediente_id)


def ruta_original(documento):
    """Original inalterable del borrador .docx (F21); nunca se muestra."""
    return (
        _carpeta_originales(documento.expediente_id)
        / str(documento.pk)
        / "original.docx"
    )


def ruta_corregido(decision):
    corrida = decision.corrida
    return (
        _carpeta_originales(corrida.expediente_id)
        / str(corrida.id_borrador)
        / f"corregido-{decision.hash_corregido}.docx"
    )


def _conservar_original(documento, temporal):
    ruta = ruta_original(documento)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    for carpeta in (ruta.parent.parent.parent, ruta.parent.parent, ruta.parent):
        carpeta.chmod(0o700)
    shutil.copyfile(temporal, ruta)
    ruta.chmod(0o400)


def borrar_originales(expediente_id, documento_id=None):
    """Supresión: el original y los corregidos del documento o del expediente."""
    borrar_vistas(expediente_id, documento_id)
    raiz = Path(settings.EXPEDIENTES_ORIGINALES_DIR).resolve()
    carpeta = raiz / str(int(expediente_id))
    if documento_id is not None:
        carpeta = carpeta / str(int(documento_id))
    if not carpeta.resolve().is_relative_to(raiz):
        raise ValueError("Directorio de originales no válido.")
    if not carpeta.exists():
        return

    def quitar_solo_lectura(funcion, ruta, error):
        # Windows no elimina los originales marcados como solo lectura.
        if os.name == "nt" and isinstance(error, PermissionError):
            Path(ruta).chmod(0o600)
            funcion(ruta)
        else:
            raise error

    shutil.rmtree(carpeta, onexc=quitar_solo_lectura)


# F32: vista del borrador. El PDF de vista es un derivado temporal del original:
# lo borran `limpiar_temporales` (24 h) y la supresión; su ruta nunca se muestra.
# La vista lo pide con un archivo `.pedido` y el worker lo convierte.
_RE_PEDIDO_VISTA = re.compile(r"^vista-(\d+)-(\d+)-([0-9a-f]{16})\.pedido$")
_VALOR_OBSERVADO = (
    ("p", "personas", "hallado"),
    ("r", "regla", "hallado"),
    ("o", "ortografia", "palabra"),
)


def _base_vista(documento):
    return Path(settings.EXPEDIENTES_TEMP_DIR) / (
        f"vista-{documento.expediente_id}-{documento.pk}-{documento.hash_archivo[:16]}"
    )


def ruta_vista(documento):
    return _base_vista(documento).with_suffix(".pdf")


def borrar_vistas(expediente_id, documento_id=None):
    """PDF de vista, pedidos y errores del documento o del expediente."""
    prefijo = f"vista-{int(expediente_id)}-"
    if documento_id is not None:
        prefijo += f"{int(documento_id)}-"
    for ruta in Path(settings.EXPEDIENTES_TEMP_DIR).glob(f"{prefijo}*"):
        if ruta.is_file():
            ruta.unlink(missing_ok=True)


def _original_no_utilizable(borrador):
    """Motivo por el que el original no sirve para la vista, o None."""
    if Path(borrador.nombre_original).suffix.lower() not in paginas.CONVERTIBLES:
        return "FORMATO"
    original = ruta_original(borrador)
    if not original.is_file():
        return "SIN_ORIGINAL"
    if calcular_hash(original) != borrador.hash_archivo:
        return "VERIFICACION"
    return None


def _estado_vista(borrador):
    """(pdf, motivo): el PDF de vista listo, o por qué todavía no está."""
    motivo = _original_no_utilizable(borrador)
    if motivo:
        return None, motivo
    pdf = ruta_vista(borrador)
    if pdf.is_file():
        return pdf, None
    base = _base_vista(borrador)
    error = base.with_suffix(".error")
    if error.is_file():
        error.unlink(missing_ok=True)
        return None, "CONVERSION"
    base.parent.mkdir(parents=True, exist_ok=True)
    base.parent.chmod(0o700)
    base.with_suffix(".pedido").touch()
    return None, "PREPARANDO"


def preparar_vistas(limite=None):
    """Worker: convierte los borradores cuya vista se pidió."""
    preparadas = 0
    for pedido in sorted(Path(settings.EXPEDIENTES_TEMP_DIR).glob("vista-*.pedido")):
        coincide = _RE_PEDIDO_VISTA.match(pedido.name)
        borrador = (
            coincide
            and Documento.objects.filter(
                pk=int(coincide[2]),
                expediente_id=int(coincide[1]),
                rol=Documento.BORRADOR,
                hash_archivo__startswith=coincide[3],
            ).first()
        )
        with exclusivo("vista", pedido.stem) as adquirido:
            if not adquirido:
                continue
            try:
                if borrador and not _original_no_utilizable(borrador):
                    if not ruta_vista(borrador).is_file():
                        inicio = perf_counter()
                        paginas.a_pdf(ruta_original(borrador), ruta_vista(borrador))
                        if _original_no_utilizable(borrador) or not (
                            Documento.objects.filter(
                                pk=borrador.pk, expediente__archivado_el__isnull=True
                            ).exists()
                        ):
                            # Suprimido, eliminado o archivado mientras convertía.
                            ruta_vista(borrador).unlink(missing_ok=True)
                            continue
                        logger.info(
                            "vista documento_id=%s segundos=%.4f",
                            borrador.pk,
                            perf_counter() - inicio,
                        )
                    preparadas += 1
            except Exception as exc:
                logger.error(
                    "No se pudo preparar la vista del borrador id=%s tipo=%s",
                    borrador.pk,
                    type(exc).__name__,
                )
                pedido.with_suffix(".error").touch()
            finally:
                pedido.unlink(missing_ok=True)
        if limite and preparadas >= limite:
            break
    return preparadas


def vista_borrador(borrador, corrida):
    """Páginas del borrador y recuadros de cada observación de la corrida."""
    pdf, motivo = _estado_vista(borrador)
    if pdf is None:
        return {
            "estado": "PREPARANDO" if motivo == "PREPARANDO" else "NO_DISPONIBLE",
            "motivo": None if motivo == "PREPARANDO" else motivo,
            "paginas": [],
            "marcas": {},
            "no_ubicadas": [],
        }
    hojas = paginas.paginas(pdf)
    segmentos = [paginas.segmentos(pdf, hoja["numero"]) for hoja in hojas]

    def rectangulos_de(valor):
        rectangulos, previas = [], 0
        for numero, de_pagina in enumerate(segmentos, 1):
            en_pagina = correccion.marcas(de_pagina, valor)
            rectangulos += [
                {**r, "pagina": numero, "aparicion": r["aparicion"] + previas}
                for r in en_pagina
            ]
            previas += len({r["aparicion"] for r in en_pagina})
        return rectangulos

    resultado = resultado_de_corrida(corrida)
    marcas, no_ubicadas = {}, []
    for prefijo, clave, campo in _VALOR_OBSERVADO:
        for i, observacion in enumerate(resultado.get(clave) or [], 1):
            identificador = f"{prefijo}{i}"
            ubicacion = observacion.get("ubicacion") or {}
            if not ubicacion.get("linea"):
                no_ubicadas.append({"id": identificador, "motivo": "AUSENTE"})
                continue
            rectangulos = rectangulos_de(observacion.get(campo) or "")
            if not rectangulos and "inicio" in ubicacion:
                # F52: el «Dice» no es texto del borrador (persona: «NOMBRE: …»).
                # Se marca lo que el panel resalta en la línea, y solo su primera
                # aparición, que es la de esa línea (ubicar_valor toma la primera).
                resaltado = ubicacion["fragmento"][
                    ubicacion["inicio"] : ubicacion["fin"]
                ]
                rectangulos = [
                    r for r in rectangulos_de(resaltado) if r["aparicion"] == 0
                ]
            if rectangulos:
                marcas[identificador] = rectangulos
            else:
                no_ubicadas.append({"id": identificador, "motivo": "NO_EN_PAGINA"})
    return {
        "estado": "LISTA",
        "motivo": None,
        "paginas": hojas,
        "marcas": marcas,
        "no_ubicadas": no_ubicadas,
    }


def png_de_vista(borrador, numero):
    """Imagen de una página del borrador, o None si no está disponible."""
    pdf = ruta_vista(borrador)
    if _original_no_utilizable(borrador) or not pdf.is_file():
        return None
    try:
        return paginas.png(pdf, numero)
    except IndexError:
        return None


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
    # La extension decide como lee extraccion.leer(); si se pierde, el archivo
    # se lee como texto plano y sale basura binaria. Se toma solo el sufijo, y
    # solo si pertenece a la lista cerrada: el nombre del navegador no es fiable.
    nombre = nombre_original or getattr(origen, "name", "") or str(origen)
    extension = Path(nombre).suffix.lower()
    if extension not in extraccion.DOCS:
        extension = ""
    ruta = destino / f"documento-{secrets.token_hex(16)}{extension}"
    if hasattr(origen, "chunks"):
        with ruta.open("wb") as archivo:
            for bloque in origen.chunks():
                archivo.write(bloque)
    else:
        shutil.copyfile(origen, ruta)
    return ruta


def registrar_documento(expediente, archivo, rol, usuario):
    """Valida que el temporal persistido solo sobreviva si se crea la fila."""
    inicio = perf_counter()
    temporal = crear_temporal(archivo, archivo.name)
    persistido = False
    try:
        hash_archivo = calcular_hash(temporal)
        try:
            with transaction.atomic():
                Expediente.objects.select_for_update().get(pk=expediente.pk)
                documento = Documento.objects.create(
                    expediente=expediente,
                    rol=rol,
                    nombre_original=Path(archivo.name).name,
                    hash_archivo=hash_archivo,
                    tamano_bytes=archivo.size,
                    ruta_temporal=str(temporal),
                    subido_por=usuario,
                )
                if (
                    rol == Documento.BORRADOR
                    and Path(archivo.name).suffix.lower() == ".docx"
                ):
                    _conservar_original(documento, temporal)
                documento.metricas = {
                    "recepcion_servidor_segundos": round(perf_counter() - inicio, 4)
                }
                documento.save(update_fields=["metricas"])
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
    # F45: el celular o el escáner guarda a veces un JPEG como .png; el OCR lee
    # el contenido, así que una imagen vale con la firma de cualquier imagen.
    imagenes = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp")
    validas = (
        tuple(firma for formato in imagenes for firma in firmas[formato])
        if extension in imagenes
        else firmas.get(extension)
    )
    if validas and not contenido.startswith(validas):
        raise ValueError("El contenido del archivo no coincide con su formato.")
    return contenido


class ExtraccionOcupada(Exception):
    """Otro proceso está preparando esta misma entrada."""


def extraer_o_reutilizar(hash_archivo, version_extractor, extractor):
    with exclusivo("texto", f"{hash_archivo}:{version_extractor}") as adquirido:
        if not adquirido:
            raise ExtraccionOcupada
        return _extraer_o_reutilizar(hash_archivo, version_extractor, extractor)


def _extraer_o_reutilizar(hash_archivo, version_extractor, extractor):
    with transaction.atomic():
        texto = TextoExtraido.objects.filter(
            hash_archivo=hash_archivo, version_extractor=version_extractor
        ).first()
        if texto is not None and texto.texto != "":
            texto.ultimo_uso_el = timezone.now()
            texto.save(update_fields=("ultimo_uso_el",))
            return texto

    salida = extractor()
    calidad = salida.get("calidad", {}) if isinstance(salida, dict) else {}
    salida = salida["texto"] if isinstance(salida, dict) else salida
    with transaction.atomic():
        if texto is not None:
            texto = TextoExtraido.objects.select_for_update().get(pk=texto.pk)
            if texto.texto == "":
                texto.texto = salida
                texto.calidad = calidad
            texto.ultimo_uso_el = timezone.now()
            texto.save(update_fields=("texto", "calidad", "ultimo_uso_el"))
            return texto
        try:
            with transaction.atomic():
                return TextoExtraido.objects.create(
                    hash_archivo=hash_archivo,
                    version_extractor=version_extractor,
                    texto=salida,
                    calidad=calidad,
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


def reencolar(documento, archivo, **condicion):
    """Devuelve el documento a la cola con una copia temporal de ``archivo``.

    Copia: el worker borra el temporal al terminar y el original no se toca.
    ``condicion`` filtra la fila (p. ej. ``estado``); si ya no cumple, nada cambia.
    """
    temporal = crear_temporal(archivo, documento.nombre_original)
    encolado = Documento.objects.filter(pk=documento.pk, **condicion).update(
        ruta_temporal=str(temporal), estado=Documento.PENDIENTE, procesando_el=None
    )
    _borrar_temporal(documento.ruta_temporal if encolado else temporal)
    return encolado


def releer_borradores_desactualizados():
    """F50: relee el borrador cuyo texto viene de otra versión del extractor.

    Solo el borrador con original conservado (F21), LISTO y de un expediente
    activo. Al cambiar su versión cambian las entradas, y el worker vuelve a
    confrontar (F26). Si la relectura falla queda en ERROR y no vuelve a entrar.
    """
    desactualizados = Documento.objects.filter(
        rol=Documento.BORRADOR,
        estado=Documento.LISTO,
        expediente__archivado_el__isnull=True,
    ).exclude(texto_extraido__version_extractor=extraccion.version_extractor())
    return sum(
        reencolar(documento, ruta_original(documento), estado=Documento.LISTO)
        for documento in desactualizados
        if _original_no_utilizable(documento) is None
    )


def documentos_por_volver_a_subir(expediente):
    """F50: documentos leídos con otra versión del extractor que no se releen
    solos: la minuta, los recaudos y el borrador sin original conservado."""
    desactualizados = (
        expediente.documentos.filter(estado=Documento.LISTO)
        .exclude(texto_extraido__version_extractor=extraccion.version_extractor())
        .order_by("pk")
    )
    return [
        documento
        for documento in desactualizados
        if documento.rol != Documento.BORRADOR or _original_no_utilizable(documento)
    ]


def _procesar_fila(documento):
    ruta = documento.ruta_temporal
    ahora = timezone.now()
    if documento.estado != Documento.PROCESANDO:
        documento.estado = Documento.PROCESANDO
        documento.procesando_el = ahora
        documento.save(update_fields=("estado", "procesando_el"))
    inicio = perf_counter()
    extraido = False

    def leer():
        nonlocal extraido
        extraido = True
        return extraccion.leer_con_calidad(Path(ruta))

    try:
        version = extraccion.version_extractor()
        texto = extraer_o_reutilizar(
            documento.hash_archivo,
            version,
            leer,
        )
        if not texto.texto:
            raise ValueError
    except ExtraccionOcupada:
        Documento.objects.filter(pk=documento.pk, estado=Documento.PROCESANDO).update(
            estado=Documento.PENDIENTE, procesando_el=None
        )
        return None
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
        Documento.objects.filter(pk=documento.pk).update(
            estado=documento.estado,
            error=documento.error,
            procesado_el=documento.procesado_el,
            procesando_el=None,
            ruta_temporal="",
        )
    else:
        documento.texto_extraido = texto
        documento.estado = Documento.LISTO
        documento.error = ""
        documento.procesado_el = timezone.now()
        documento.procesando_el = None
        documento.ruta_temporal = ""
        documento.metricas = {
            **documento.metricas,
            "cola_segundos": round(
                max(0, (ahora - documento.subido_el).total_seconds()), 4
            ),
            "lectura_segundos": round(perf_counter() - inicio, 4),
            "reutilizada": not extraido,
        }
        Documento.objects.filter(pk=documento.pk).update(
            texto_extraido=texto,
            estado=documento.estado,
            error="",
            procesado_el=documento.procesado_el,
            procesando_el=None,
            ruta_temporal="",
            metricas=documento.metricas,
        )
    finally:
        # La contención no consume ni elimina la entrada del intento pendiente.
        if documento.ruta_temporal == "":
            _borrar_temporal(ruta)
    return documento


def procesar_documento(documento_o_id):
    pk = documento_o_id.pk if isinstance(documento_o_id, Documento) else documento_o_id
    with exclusivo("documento", pk) as adquirido:
        if not adquirido:
            return None
        documento = Documento.objects.filter(pk=pk).first()
        if not documento or documento.estado not in (
            Documento.PENDIENTE,
            Documento.PROCESANDO,
        ):
            return documento
        return _procesar_fila(documento)


def _timeout():
    value = settings.EXPEDIENTES_PROCESSING_TIMEOUT
    return value if isinstance(value, timedelta) else timedelta(seconds=value)


def recuperar_documentos_vencidos():
    limite = timezone.now() - _timeout()
    vencidos = Documento.objects.filter(
        estado=Documento.PROCESANDO,
        procesando_el__lt=limite,
    )
    recuperados = 0
    for pk in vencidos.values_list("pk", flat=True):
        with exclusivo("documento", pk) as adquirido:
            if adquirido:
                recuperados += vencidos.filter(pk=pk).update(
                    estado=Documento.PENDIENTE, procesando_el=None
                )
    return recuperados


def tomar_pendiente(excluir=()):
    with transaction.atomic():
        documento = (
            Documento.objects.select_for_update(skip_locked=True)
            .filter(estado=Documento.PENDIENTE, expediente__archivado_el__isnull=True)
            .exclude(pk__in=excluir)
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
    expediente_id, documento_id = documento.expediente_id, documento.pk
    with transaction.atomic():
        Expediente.objects.select_for_update().get(pk=expediente_id)
        documento.delete()
    _borrar_temporal(ruta)
    borrar_originales(expediente_id, documento_id)


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
        "personas": [],
        "regla": [],
        "ortografia": [],
    }


def _catalogo_legible(catalogo):
    return {campo: sorted(catalogo.get(campo, ())) for campo in _CAMPOS_CATALOGO}


def _procedencias_legibles(procedencias):
    return [
        {
            "archivo": Path(procedencia.fuente).name,
            "pagina": procedencia.pagina,
        }
        for procedencia in procedencias
    ]


def _origen_legible(origen):
    return _procedencias_legibles((origen,))[0] if origen else None


def _personas_legibles(personas):
    return [
        {
            "nombre": persona.nombre or "No identificado",
            "documento": persona.documento or "Sin documento",
            "procedencias": _procedencias_legibles(persona.procedencias),
            "estado": _ESTADOS_PERSONA.get(persona.estado, "Revisión manual"),
            "estado_civil": persona.estado_civil,
            "fecha_nacimiento": persona.fecha_nacimiento.isoformat()
            if persona.fecha_nacimiento
            else None,
            "domicilio": persona.domicilio,
            "distrito": persona.distrito,
            **{
                f"procedencia_{campo}": _origen_legible(
                    getattr(persona, f"procedencia_{campo}")
                )
                for campo in (
                    "estado_civil",
                    "fecha_nacimiento",
                    "domicilio",
                    "distrito",
                )
            },
            "conyuge": persona.conyuge,
            "procedencia_conyuge": _origen_legible(persona.procedencia_conyuge),
            "adjuntos": [
                {
                    "nombre": adjunto.nombre or "Sin nombre",
                    "documento": adjunto.documento or "Sin documento",
                    "procedencias": _procedencias_legibles(adjunto.procedencias),
                }
                for adjunto in persona.adjuntos or ()
            ],
        }
        for persona in personas
    ]


def _paginas_legibles(paginas):
    return [
        {
            "archivo": Path(pagina.fuente).name,
            "pagina": pagina.pagina,
            "tipo": pagina.tipo,
        }
        for pagina in paginas
    ]


def _resumen_extraccion(fuentes_documentos, catalogo):
    documentos = []
    for documento in fuentes_documentos:
        texto = documento.texto_extraido.texto
        aporte_catalogo = verificar.catalogo({documento.nombre_original: texto})
        aporte = _catalogo_legible(aporte_catalogo)
        fila = {
            "nombre": documento.nombre_original,
            "caracteres": len(texto),
            "catalogo": aporte,
            "aporta": any(aporte.values())
            or bool(
                aporte_catalogo.personas or aporte_catalogo.menciones
                if isinstance(aporte_catalogo, verificar.Catalogo)
                else ()
            ),
        }
        if isinstance(aporte_catalogo, verificar.Catalogo):
            fila["personas"] = _personas_legibles(aporte_catalogo.personas)
            fila["menciones"] = _personas_legibles(aporte_catalogo.menciones)
        documentos.append(fila)
    es_catalogo = isinstance(catalogo, verificar.Catalogo)
    return {
        "catalogo": _catalogo_legible(catalogo),
        "personas": _personas_legibles(catalogo.personas) if es_catalogo else [],
        "menciones": _personas_legibles(catalogo.menciones) if es_catalogo else [],
        "paginas_descartadas": _paginas_legibles(catalogo.paginas_descartadas)
        if isinstance(catalogo, verificar.Catalogo)
        else [],
        "paginas_no_clasificadas": _paginas_legibles(catalogo.paginas_no_clasificadas)
        if isinstance(catalogo, verificar.Catalogo)
        else [],
        "documentos": documentos,
    }


def _observaciones_personas_legibles(observaciones, texto_borrador):
    return [
        {
            "formato": "persona",
            "tipo": observacion["tipo"],
            "nombre": observacion["nombre"] or "No identificado",
            "hallado": observacion["documento_hallado"],
            "esperado": observacion["documento_esperado"] or "Sin documento conocido",
            "motivo": (
                "El documento pertenece a otra persona según los recaudos."
                if observacion["tipo"] == "DOCUMENTO_CRUZADO"
                else "El documento no pertenece a una persona conocida en los recaudos."
            ),
            "procedencias": _procedencias_legibles(observacion["procedencias"]),
            "ubicacion": ubicar_valor(texto_borrador, observacion["documento_hallado"]),
        }
        for observacion in observaciones
    ]


def _normalizar_ubicacion(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c)).upper()
    return re.sub(r"\s+", " ", texto).strip()


def ubicar_valor(texto, valor):
    """Ubica un valor sin alterar el fragmento original que verá el usuario."""
    if not valor or not valor.strip():
        return {"linea": None, "fragmento": "No ubicada"}
    for numero, linea in enumerate(texto.splitlines(), start=1):
        linea = linea.strip()
        coincidencias = correccion.coincidencias(linea, valor)
        if coincidencias:
            inicio, fin = coincidencias[0]
            while fin > inicio and linea[fin - 1].isspace():
                fin -= 1
            # El recorte debe contener el error, incluso en párrafos extensos.
            desde = max(0, inicio - max(0, (160 - (fin - inicio)) // 2))
            desde = min(desde, max(0, len(linea) - 160))
            fragmento = linea[desde : desde + 160]
            return {
                "linea": numero,
                "fragmento": fragmento,
                "inicio": inicio - desde,
                "fin": min(fin - desde, len(fragmento)),
            }
    return {"linea": None, "fragmento": "No ubicada"}


def _observacion_regla(campo, hallado, esperado, motivo, texto_borrador):
    return {
        "formato": "regla",
        "campo": campo,
        "hallado": hallado,
        "esperado": esperado,
        "motivo": motivo,
        "porcentaje": "",
        "ubicacion": ubicar_valor(texto_borrador, hallado),
    }


def parsear_observacion_regla(salida, texto_borrador):
    """Convierte una salida textual del núcleo en una fila segura para la UI."""
    if not isinstance(salida, str):
        return {
            "formato": "desconocido",
            "campo": "FORMATO_DESCONOCIDO",
            "hallado": "No se pudo interpretar la observación",
            "esperado": "Revise el formato de la observación",
            "motivo": "La observación no usa un formato reconocido.",
            "porcentaje": "",
            "ubicacion": {"linea": None, "fragmento": "No ubicada"},
        }

    parrafo = _RE_OBSERVACION_PARRAFO.match(salida)
    if parrafo:
        porcentaje = parrafo.group("porcentaje")
        return {
            "formato": "regla",
            "campo": "PARRAFO",
            "hallado": "No aparece o fue alterado",
            "esperado": parrafo.group("fragmento"),
            "motivo": (
                f"Coincidencia: {porcentaje}%"
                if porcentaje
                else "No coincide con el borrador"
            ),
            "porcentaje": porcentaje or "",
            "ubicacion": {"linea": None, "fragmento": "No ubicada"},
        }

    falta = _RE_OBSERVACION_FALTA.match(salida)
    if falta:
        return _observacion_regla(
            falta.group("campo"),
            "No aparece en el borrador",
            falta.group("esperado"),
            "",
            texto_borrador,
        )

    # F58: el anexo insertado que no se puede cotejar por texto
    sin_comprobar = _RE_OBSERVACION_SIN_COMPROBAR.match(salida)
    if sin_comprobar:
        return _observacion_regla(
            sin_comprobar.group("campo"),
            "No se pudo comprobar el anexo",
            f"Verifique que «{sin_comprobar.group('esperado')}» esté insertado",
            "",
            texto_borrador,
        )

    coincidencia = _RE_OBSERVACION_CAMPO.match(salida)
    if coincidencia:
        campo = coincidencia.group("campo")
        hallado = coincidencia.group("hallado")
        resto = coincidencia.group("resto")
        debe_decir = _RE_DEBE_DECIR.match(resto)
        if debe_decir:
            monto = _RE_MOTIVO_MONTO.match(debe_decir.group("resto"))
            if monto:
                fuente = {
                    "archivo": Path(monto.group("archivo")).name,
                    "pagina": int(monto.group("pagina")),
                }
                return _observacion_regla(
                    campo,
                    hallado,
                    debe_decir.group("esperado"),
                    f"{monto.group('concepto')} · {fuente['archivo']}, "
                    f"página {fuente['pagina']}",
                    texto_borrador,
                ) | {"concepto": monto.group("concepto"), "fuente": fuente}
            motivo = _RE_MOTIVO_CARATULA.search(debe_decir.group("resto"))
            fila = _observacion_regla(
                campo,
                hallado,
                debe_decir.group("esperado"),
                motivo.group("motivo") if motivo else "",
                texto_borrador,
            )
            detalle = _RE_DETALLE.match(debe_decir.group("resto"))
            if campo in _CON_SUGERENCIA and detalle:
                fila["detalle"] = detalle.group("detalle")
            return fila
        for frase in (
            "No coincide con ninguna fuente",
            "Sin ficha RENIEC en los recaudos",
            "Sin ficha RUC en los recaudos",  # F45: transferencia vehicular
            "Debe tener 8 dígitos",
            "Posible Ñ por marca de agua; verifique el DNI",
        ):
            if resto.lower().startswith(frase.lower()):
                nota = _RE_MINUTA_DICE.search(resto)
                return _observacion_regla(
                    campo,
                    hallado,
                    frase + (nota[0] if nota else ""),
                    "",
                    texto_borrador,
                )

    return {
        "formato": "desconocido",
        "campo": "FORMATO_DESCONOCIDO",
        "hallado": "No se pudo interpretar la observación",
        "esperado": "Revise el formato de la observación",
        "motivo": "La observación no usa un formato reconocido.",
        "porcentaje": "",
        "ubicacion": {"linea": None, "fragmento": "No ubicada"},
    }


def adaptar_observaciones_regla(salidas, texto_borrador):
    observaciones = [
        parsear_observacion_regla(salida, texto_borrador) for salida in salidas
    ]
    esperados_en_discrepancias = {
        (observacion["campo"], observacion["esperado"])
        for observacion in observaciones
        if observacion["hallado"] != "No aparece en el borrador"
    }
    return [
        observacion
        for observacion in observaciones
        if not (
            observacion["hallado"] == "No aparece en el borrador"
            and (observacion["campo"], observacion["esperado"])
            in esperados_en_discrepancias
        )
    ]


def _observaciones_f12_legibles(observaciones, texto_borrador):
    filas = []
    for observacion in observaciones:
        tipo = observacion["tipo"]
        nombre = observacion["nombre"]
        origen = observacion["procedencia"]
        archivo = Path(origen.fuente).name if origen else "No ubicado"
        pagina = f", página {origen.pagina}" if origen else ""
        if tipo == "MENOR_DE_EDAD":
            hallado = (
                f"{nombre}: {observacion['edad']} años al "
                f"{observacion['fecha_referencia'].isoformat()}"
            )
            esperado = f"Fecha de nacimiento: {observacion['esperado'].isoformat()}"
        else:
            hallado = f"{nombre}: {observacion['hallado']}"
            esperado = (
                f"{observacion.get('referencia', 'RENIEC')}: {observacion['esperado']}"
            )
        filas.append(
            {
                "formato": "regla",
                "campo": tipo,
                "hallado": hallado,
                "esperado": esperado,
                "motivo": f"Fuente: {archivo}{pagina}",
                "porcentaje": "",
                "ubicacion": ubicar_valor(
                    texto_borrador, observacion.get("ubicar", nombre)
                ),
            }
        )
    return filas


def adaptar_observaciones_ortografia(salidas, texto_borrador):
    return [
        {
            "palabra": palabra,
            "motivo": motivo,
            "sugerencia": "Sin sugerencia" if sugerencia == "?" else sugerencia,
            "ubicacion": ubicar_valor(texto_borrador, palabra),
        }
        for palabra, motivo, sugerencia in salidas
    ]


def estado_confrontacion(expediente, borrador, fuentes=None):
    """Indica si el borrador tiene los textos necesarios para confrontar."""
    if fuentes is None:
        fuentes = list(
            expediente.documentos.filter(rol__in=Documento.ROLES_FUENTE).order_by("pk")
        )
    documentos = list(fuentes)
    if borrador is not None:
        documentos.append(borrador)
    roles = {documento.rol for documento in documentos}
    faltantes = [etiqueta for rol, etiqueta in expediente.roles if rol not in roles]
    if faltantes:
        verbo = "Falta" if len(faltantes) == 1 else "Faltan"
        return {
            "disponible": False,
            "mensaje": f"{verbo}: {', '.join(faltantes)}.",
        }
    if borrador is None or borrador.rol != Documento.BORRADOR:
        return {
            "disponible": False,
            "mensaje": "Falta: Proyecto (borrador).",
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


def _calidad_lectura(documentos):
    avisos = []
    for documento in documentos:
        calidad = (
            documento.texto_extraido.calidad if documento.texto_extraido_id else {}
        )
        if not calidad or not calidad.get("paginas"):
            avisos.append(
                {
                    "documento": documento.nombre_original,
                    "tipo": "SIN_MEDICION",
                    "paginas": [],
                }
            )
            continue
        paginas = [
            p["pagina"] for p in calidad["paginas"] if p.get("requiere_revision")
        ]
        if paginas:
            avisos.append(
                {
                    "documento": documento.nombre_original,
                    "tipo": "DUDOSA",
                    "paginas": paginas,
                }
            )
    return avisos


def confrontar_borrador(
    expediente, borrador, fecha=None, fuentes_documentos=None, metricas=None
):
    """Ejecuta la regla sobre un borrador listo, sin persistir.

    `fecha` y `fuentes_documentos` explícitos reconstruyen una corrida.
    """
    fecha = fecha or timezone.localdate()
    if borrador.expediente_id != expediente.pk or borrador.rol != Documento.BORRADOR:
        raise ValueError("El documento no es un borrador de este kardex.")

    if fuentes_documentos is None:
        fuentes_documentos = list(
            expediente.documentos.filter(rol__in=Documento.ROLES_FUENTE).order_by("pk")
        )
    disponibilidad = estado_confrontacion(expediente, borrador, fuentes_documentos)
    if not disponibilidad["disponible"]:
        return _resultado_no_disponible(disponibilidad["mensaje"])

    fuentes = {
        documento.nombre_original: documento.texto_extraido.texto
        for documento in fuentes_documentos
    }
    texto_borrador = borrador.texto_extraido.texto
    calidad_lectura = _calidad_lectura([borrador, *fuentes_documentos])
    # El catalogo se construye ANTES del diagnostico: si el aviso salta, el
    # usuario necesita ver que se extrajo para saber si el borrador es de otro
    # expediente o si el OCR no leyo los datos de las fuentes.
    inicio_campos = perf_counter()
    catalogo = verificar.catalogo(fuentes)
    extraccion = _resumen_extraccion(fuentes_documentos, catalogo)
    campos_segundos = round(perf_counter() - inicio_campos, 4)
    inicio_comparacion = perf_counter()
    aviso = verificar.diagnostico(fuentes, texto_borrador)
    if aviso:
        if metricas is not None:
            metricas.update(
                campos_segundos=campos_segundos,
                comparacion_segundos=round(perf_counter() - inicio_comparacion, 4),
            )
        return {
            "estado": "ADVERTENCIA_CORRESPONDENCIA",
            "calidad_lectura": calidad_lectura,
            "mensaje": aviso,
            "personas": [],
            "extraccion": extraccion,
            "regla": [],
            "ortografia": [],
        }

    observaciones_personas = (
        verificar.comparar_personas(catalogo, texto_borrador)
        if isinstance(catalogo, verificar.Catalogo)
        else ()
    )
    minutas = [
        documento.texto_extraido.texto
        for documento in fuentes_documentos
        if documento.rol == Documento.MINUTA
    ]
    # F39: el anexo que el borrador inserta como documento (Recaudos.pdf)
    minutas_sin_insertos = verificar.sin_anexos_insertados(
        minutas,
        texto_borrador,
        [
            documento.texto_extraido.texto
            for documento in fuentes_documentos
            if documento.rol == Documento.CLIENTE
        ],
    )
    reglas = verificar.revisar(
        catalogo,
        texto_borrador,
        _UMBRAL_PARRAFO,
        verificar.nombres_exigibles(catalogo, minutas)
        if isinstance(catalogo, verificar.Catalogo)
        else None,
        verificar.montos_exigibles(minutas_sin_insertos),
        {
            documento.nombre_original: documento.texto_extraido.texto
            for documento in fuentes_documentos
            if documento.rol == Documento.MINUTA
        },
    )
    reglas.extend(
        verificar.anexos_omitidos(minutas_sin_insertos, texto_borrador, _UMBRAL_PARRAFO)
    )
    if expediente.tipo == Expediente.VEHICULAR:
        # F43: sin minuta, la partida y los importes se cotejan con la boleta
        # informativa y los cheques; los de un poder no están entre las fuentes.
        reglas = [
            regla for regla in reglas if not regla.startswith(("[PARTIDA]", "[MONTO]"))
        ] + vehicular.revisar(fuentes, texto_borrador)
        if not getattr(catalogo, "rucs", None):
            # F45: sin ficha RUC entre la información el RUC no se puede verificar.
            reglas = [
                re.sub(
                    r"^\[RUC\] «([^»]+)» no coincide con ninguna fuente",
                    r"[SIN_FICHA] «\1» sin ficha RUC en los recaudos",
                    regla,
                )
                for regla in reglas
            ]
    reglas, observaciones_personas = verificar.sin_ficha_por_persona(
        reglas, observaciones_personas
    )
    observaciones_regla = adaptar_observaciones_regla(reglas, texto_borrador)
    correcciones = correccion.correcciones(reglas, fuentes)
    original = ruta_original(borrador)
    if original.is_file():
        cuenta = docx_corregido.apariciones(original, correcciones)
        for propuesta in correcciones:
            propuesta["apariciones"] = cuenta.get(propuesta["id"], 0)
    if isinstance(catalogo, verificar.Catalogo):
        observaciones_regla.extend(
            _observaciones_f12_legibles(
                verificar.revisar_persona_ampliada(
                    catalogo,
                    texto_borrador,
                    fecha,
                    verificar.domicilios_contractuales(minutas),
                ),
                texto_borrador,
            )
        )
    personas = _observaciones_personas_legibles(observaciones_personas, texto_borrador)
    linguistico, aviso = _capa_linguistica(
        catalogo, observaciones_regla + personas, texto_borrador, fuentes.values()
    )
    if metricas is not None:
        metricas.update(
            campos_segundos=campos_segundos,
            comparacion_segundos=round(perf_counter() - inicio_comparacion, 4),
        )
    return {
        "estado": "RESULTADO",
        "calidad_lectura": calidad_lectura,
        "mensaje": "",
        "fecha_referencia": fecha,
        "personas": personas,
        "extraccion": extraccion,
        "regla": observaciones_regla,
        # clave historica: lleva toda la capa linguistica (F23), solo se muestra
        "ortografia": linguistico,
        "linguistico_aviso": aviso,
        "correcciones": correcciones,
        "corregible": original.is_file(),
    }


def aplicar_correcciones(expediente, borrador, corrida_id, ids, usuario):
    """Aplica las correcciones confirmadas sobre una copia del original (P-10).

    Solo si las entradas actuales y los hallazgos recalculados coinciden con la
    corrida que vio el usuario; la decisión queda enlazada a esa corrida.
    """
    corrida = Corrida.objects.filter(
        pk=int(corrida_id) if str(corrida_id).isdigit() else None,
        expediente=expediente,
        id_borrador=borrador.pk,
        estado=Corrida.RESULTADO,
    ).first()
    fuentes = list(
        expediente.documentos.filter(rol__in=Documento.ROLES_FUENTE)
        .select_related("texto_extraido")
        .order_by("pk")
    )
    resultado = None
    if corrida and corrida.entradas == [
        _entrada_corrida(documento) for documento in (borrador, *fuentes)
    ]:
        resultado = confrontar_borrador(
            expediente, borrador, corrida.fecha_referencia, fuentes
        )
    if (
        resultado is None
        or resultado["estado"] != "RESULTADO"
        or (
            _sha256_texto(hallazgos_canonicos(_con_severidad(resultado)))
            != corrida.huella
        )
    ):
        raise CorreccionNoAplicable(
            "Los recaudos o el borrador cambiaron. Vuelva a confrontar antes de aplicar."
        )
    original = ruta_original(borrador)
    if not original.is_file() or calcular_hash(original) != borrador.hash_archivo:
        raise CorreccionNoAplicable(
            "Este borrador no admite corrección automática. Vuelva a subirlo en Word (.docx)."
        )
    ids = set(ids)
    propuestas = resultado["correcciones"]
    temporal = original.with_name(f"corregido-{secrets.token_hex(8)}.tmp")
    try:
        apariciones, no_aplicadas = docx_corregido.aplicar(
            original, temporal, [p for p in propuestas if p["id"] in ids]
        )
        corregido_hash = calcular_hash(temporal)
        destino = original.with_name(f"corregido-{corregido_hash}.docx")
        # El nombre es el hash: si ya existe (doble clic, reintento) es idéntico.
        # Windows no deja reemplazarlo porque queda de solo lectura.
        if not (destino.is_file() and calcular_hash(destino) == corregido_hash):
            os.replace(temporal, destino)
            destino.chmod(0o400)
    finally:
        temporal.unlink(missing_ok=True)
    return DecisionCorreccion.objects.create(
        corrida=corrida,
        usuario=usuario,
        apariciones=apariciones,
        correcciones_excluidas=[p["id"] for p in propuestas if p["id"] not in ids],
        correcciones_no_aplicadas=no_aplicadas,
        hash_corregido=corregido_hash,
    )


def _capa_linguistica(catalogo, observaciones, texto_borrador, textos_fuente):
    """F23: ortografia, tildes y redaccion sin autoridad sobre los datos del A.3."""
    protegidos = {v for campo in _CAMPOS_CATALOGO for v in catalogo.get(campo, ())}
    if isinstance(catalogo, verificar.Catalogo):
        protegidos |= {
            valor
            for registro in catalogo._registros()
            for valor in (registro.domicilio, registro.distrito)
            if valor
        }
    protegidos |= {
        fila["hallado"]
        for fila in observaciones
        if fila.get("campo") != "PARRAFO" and isinstance(fila.get("hallado"), str)
    }
    faltas = []
    aviso = ""
    try:
        dic, lemas = diccionario.diccionario()
    except diccionario.DiccionarioNoAprovisionado:
        aviso = "Ortografía y tildes no disponibles: falta aprovisionar el diccionario es_PE."
    else:
        propios = {p for valor in protegidos for p in re.findall(r"[^\W\d_]+", valor)}
        # FR-002b: el vocabulario literal del legajo se da por conocido
        propios |= {p for t in textos_fuente for p in re.findall(r"[^\W\d_]{3,}", t)}
        faltas = ortografia.revisar(
            texto_borrador, dic, lemas, diccionario.lista_casa(), propios
        )
    faltas += ortografia.redaccion(texto_borrador, protegidos)
    return adaptar_observaciones_ortografia(faltas, texto_borrador), aviso


def usuario_puede_ver_expediente(usuario, expediente):
    if not usuario.is_authenticated:
        return False
    if usuario.groups.filter(name="Administrador").exists():
        return True
    return (
        expediente.creado_por_id == usuario.pk
        and usuario.groups.filter(name="Usuario").exists()
    )


def expedientes_visibles(usuario, archivados=False):
    queryset = Expediente.objects.filter(archivado_el__isnull=not archivados)
    if usuario.groups.filter(name="Administrador").exists():
        return queryset
    return queryset.filter(creado_por=usuario)


def expedientes_con_resumen(usuario, archivados=False, tipo=None):
    """Expedientes visibles, del actualizado más reciente al más antiguo, con su resumen.

    F59: `actualizado` es la hora del último documento procesado, o la del kardex si
    aún no hay ninguno; `observaciones`, el total de su confrontación vigente.
    """
    expedientes = (
        expedientes_visibles(usuario, archivados)
        .annotate(
            actualizado=Coalesce(Max("documentos__procesado_el"), "actualizado_el")
        )
        .order_by("-actualizado", "-pk")
    )
    if tipo:
        expedientes = expedientes.filter(tipo=tipo)
    expedientes = list(expedientes)
    observaciones = observaciones_vigentes(expedientes)
    return [
        (e, {**resumen_expediente(e), "observaciones": observaciones.get(e.pk)})
        for e in expedientes
    ]


def cifras_por_tipo(usuario):
    """F53: kardex activos visibles por tipo; el total es su suma."""
    por_tipo = dict(
        expedientes_visibles(usuario)
        .values_list("tipo")
        .annotate(cantidad=Count("pk"))
        .order_by()
    )
    notariales = por_tipo.get(Expediente.NOTARIAL, 0)
    vehiculares = por_tipo.get(Expediente.VEHICULAR, 0)
    return {
        "notariales": notariales,
        "vehiculares": vehiculares,
        "total": notariales + vehiculares,
    }


PERIODOS = ("semana", "mes")
MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def rango_periodo(periodo, hoy=None):
    """F53: [desde, hasta) del periodo: 12 semanas o el año en curso, hora local."""
    hoy = hoy or timezone.localdate()
    if periodo == "mes":
        inicio = date(hoy.year, 1, 1)
        fin = date(hoy.year + hoy.month // 12, hoy.month % 12 + 1, 1)
    else:
        lunes = hoy - timedelta(days=hoy.weekday())
        inicio, fin = lunes - timedelta(weeks=11), lunes + timedelta(weeks=1)
    return tuple(
        timezone.make_aware(datetime.combine(dia, time.min)) for dia in (inicio, fin)
    )


def _kardex_por(truncar, desde, hasta):
    # Incluye kardex archivados: la actividad es un registro histórico.
    return dict(
        Corrida.objects.filter(creado_el__gte=desde, creado_el__lt=hasta)
        .annotate(tramo=truncar("creado_el", output_field=DateField()))
        .values_list("tramo")
        .annotate(kardex=Count("expediente", distinct=True))
        .order_by()
    )


def actividad_semanal(hoy=None):
    """F53: kardex distintos confrontados por semana (lunes, hora local)."""
    desde, hasta = rango_periodo("semana", hoy)
    por_semana = _kardex_por(TruncWeek, desde, hasta)
    inicios = [desde.date() + timedelta(weeks=numero) for numero in range(12)]
    return [
        {"inicio": inicio, "kardex": por_semana.get(inicio, 0)} for inicio in inicios
    ]


def actividad_mensual(hoy=None):
    """F53: kardex distintos confrontados por mes, de enero al mes de `hoy`."""
    hoy = hoy or timezone.localdate()
    por_mes = _kardex_por(TruncMonth, *rango_periodo("mes", hoy))
    inicios = [date(hoy.year, mes, 1) for mes in range(1, hoy.month + 1)]
    return [{"inicio": inicio, "kardex": por_mes.get(inicio, 0)} for inicio in inicios]


def avisos_documentos_ilegibles(usuario):
    """F53: kardex activos con algún documento ilegible que subió `usuario`."""
    return (
        Expediente.objects.filter(
            archivado_el__isnull=True,
            documentos__estado=Documento.ERROR,
            documentos__subido_por=usuario,
        )
        .distinct()
        .order_by("codigo")
    )


def ultimas_confrontaciones(limite=5):
    """F53: kardex activos confrontados más recientemente, con su última corrida."""
    ultima = Corrida.objects.filter(expediente=OuterRef("pk")).order_by(
        "-creado_el", "-pk"
    )
    expedientes = (
        Expediente.objects.filter(archivado_el__isnull=True)
        .annotate(
            fecha=Subquery(ultima.values("creado_el")[:1]),
            nombre=Subquery(ultima.values("usuario__first_name")[:1]),
            apellido=Subquery(ultima.values("usuario__last_name")[:1]),
            cuenta=Subquery(ultima.values("usuario__username")[:1]),
        )
        .filter(fecha__isnull=False)
        .order_by("-fecha", "-pk")[:limite]
    )
    # Mismo criterio que get_full_name(), con el usuario si no hay nombre.
    return [
        {
            "expediente": expediente,
            "usuario": f"{expediente.nombre} {expediente.apellido}".strip()
            or expediente.cuenta,
            "fecha": expediente.fecha,
        }
        for expediente in expedientes
    ]


def _nombre(usuario):
    return usuario.get_full_name() or usuario.username


def _observaciones(corrida):
    """(tipo, severidad) de cada observación de una corrida con resultado."""
    if corrida.estado not in (Corrida.RESULTADO, Corrida.ADVERTENCIA):
        return []
    try:
        hallazgos = json.loads(corrida.hallazgos)
    except ValueError:
        return []
    return [
        (fila.get(clave) if clave else "ORTOGRAFIA", fila.get("severidad"))
        for lista, clave in (
            ("personas", "tipo"),
            ("regla", "campo"),
            ("ortografia", None),
        )
        for fila in hallazgos.get(lista, [])
    ]


def _ancho(valor, maximo):
    return round(100 * valor / maximo) if maximo else 0


def indicadores_calidad(desde, hasta):
    """F53: calidad de las confrontaciones del periodo, por quien creó el kardex.

    Una confrontación repetida con los mismos documentos cuenta una sola vez.
    """
    gravedad = {"ALTA": 0, "MEDIA": 0, "BAJA": 0}
    personas, tipos, vistas = {}, Counter(), set()
    corridas = (
        Corrida.objects.filter(creado_el__gte=desde, creado_el__lt=hasta)
        .select_related("expediente__creado_por")
        .order_by("creado_el", "pk")
    )
    for corrida in corridas:
        clave = (
            corrida.expediente_id,
            corrida.hash_borrador,
            tuple(
                (e.get("hash_archivo"), e.get("hash_texto")) for e in corrida.entradas
            ),
        )
        if clave in vistas:
            continue
        vistas.add(clave)
        autor = corrida.expediente.creado_por
        persona = personas.setdefault(
            autor.pk,
            {
                "usuario": _nombre(autor),
                "kardex": set(),
                "observaciones": 0,
                "altas": 0,
                "medias": 0,
                "bajas": 0,
            },
        )
        persona["kardex"].add(corrida.expediente_id)
        for tipo, grado in _observaciones(corrida):
            gravedad[grado] = gravedad.get(grado, 0) + 1
            tipos[tipo] += 1
            persona["observaciones"] += 1
            persona["altas"] += grado == "ALTA"
            persona["medias"] += grado == "MEDIA"
            persona["bajas"] += grado == "BAJA"
    # F57: todas las del periodo, por total de observaciones; el promedio solo informa.
    usuarias = sorted(
        (
            {
                **p,
                "kardex": len(p["kardex"]),
                "promedio": round(p["observaciones"] / len(p["kardex"]), 1),
            }
            for p in personas.values()
        ),
        key=lambda p: (-p["observaciones"], p["usuario"]),
    )
    maximo = usuarias[0]["observaciones"] if usuarias else 0
    for persona in usuarias:
        persona["ancho"] = _ancho(persona["observaciones"], maximo)
        # Empate en el total, mismo puesto (1, 2, 2, 4); son ≤ 10 personas.
        persona["puesto"] = 1 + sum(
            otra["observaciones"] > persona["observaciones"] for otra in usuarias
        )
    frecuentes = sorted(tipos.items(), key=lambda par: (-par[1], par[0]))[:5]
    reglas = CATALOGO_REGLAS["reglas"]
    corregidos = DecisionCorreccion.objects.filter(
        creado_el__gte=desde, creado_el__lt=hasta
    ).exclude(hash_corregido="")
    return {
        "gravedad": gravedad,
        "usuarias": usuarias,
        "frecuentes": [
            {
                "tipo": tipo,
                "descripcion": reglas.get(tipo, {}).get("descripcion", tipo),
                "cantidad": cantidad,
                "ancho": _ancho(cantidad, frecuentes[0][1]),
            }
            for tipo, cantidad in frecuentes
        ],
        "correcciones": {
            "documentos": len(corregidos),
            "aplicadas": sum(len(d.correcciones_aplicadas) for d in corregidos),
        },
    }


def _explicar(inicio, periodo):
    """Etiqueta corta de la barra y cuándo, sin depender del idioma del sistema."""
    if periodo == "mes":
        mes = MESES[inicio.month - 1]
        return mes[:3].capitalize(), f"en {mes} de {inicio.year}"
    etiqueta = inicio.strftime("%d/%m")
    return etiqueta, f"en la semana del {etiqueta}"


def datos_inicio_administrador(usuario, periodo="semana"):
    """F53: todo el Inicio del administrador, serializable para la pantalla y el JSON."""
    periodo = periodo if periodo in PERIODOS else "semana"
    ahora = timezone.localtime()
    hoy = ahora.date()
    desde, hasta = rango_periodo(periodo, hoy)
    tramos = actividad_mensual(hoy) if periodo == "mes" else actividad_semanal(hoy)
    maximo = max(tramo["kardex"] for tramo in tramos)
    actividad = []
    for tramo in tramos:
        etiqueta, cuando = _explicar(tramo["inicio"], periodo)
        confrontados = "confrontado" if tramo["kardex"] == 1 else "confrontados"
        actividad.append(
            {
                "etiqueta": etiqueta,
                "kardex": tramo["kardex"],
                "alto": _ancho(tramo["kardex"], maximo),
                "explicacion": f"{tramo['kardex']} kardex {confrontados} {cuando}",
            }
        )
    return {
        "periodo": periodo,
        "titulo_periodo": "las últimas 12 semanas"
        if periodo == "semana"
        else f"lo que va de {hoy.year}",
        # F57: fechas absolutas para la versión impresa.
        "rango": f"del {desde:%d/%m/%Y} al {hoy:%d/%m/%Y}",
        "fecha": hoy.strftime("%d/%m/%Y"),
        "actualizado": ahora.strftime("%H:%M"),
        "cifras": cifras_por_tipo(usuario),
        "actividad": actividad,
        "confrontaciones": [
            {
                "codigo": fila["expediente"].codigo,
                "tipo": fila["expediente"].get_tipo_display(),
                "usuario": fila["usuario"],
                "fecha": timezone.localtime(fila["fecha"]).strftime("%d/%m/%Y %H:%M"),
                "url": reverse("expediente_detalle", args=[fila["expediente"].pk]),
            }
            for fila in ultimas_confrontaciones()
        ],
        "indicadores": indicadores_calidad(desde, hasta),
    }


# Catálogo de reglas versionado (Anexo A, capas 5 y 6). El núcleo no lee
# archivos: el adaptador lo carga una vez.
CATALOGO_REGLAS = tomllib.loads(
    (Path(__file__).resolve().parents[1] / "nucleo" / "catalogo_reglas.toml").read_text(
        encoding="utf-8"
    )
)
RESULTADO_ERROR = {
    "estado": "ERROR_SEGURO",
    "mensaje": "No se pudo completar la confrontación. Intente nuevamente.",
    "regla": [],
    "ortografia": [],
}
_ESTADOS_CORRIDA = {
    "RESULTADO": Corrida.RESULTADO,
    "ADVERTENCIA_CORRESPONDENCIA": Corrida.ADVERTENCIA,
    "NO_DISPONIBLE": Corrida.NO_DISPONIBLE,
}


class CorridaNoReconstruible(ValueError):
    """Falta un texto de entrada o cambió desde la corrida."""


# F42: «generales de ley» son los datos del compareciente, persona natural o
# jurídica. Lo demás (partidas, montos, anexos, cláusulas) es dato del acto.
_GENERALES_DE_LEY = frozenset(
    {
        "NOMBRE",
        "DNI",
        "SIN_FICHA",
        "NOMBRE_MARCA_AGUA",
        "DOCUMENTO_CRUZADO",
        "DOCUMENTO_SIN_TITULAR",
        "RUC",
        "RAZON_SOCIAL",
        "DOMICILIO_FISCAL",
        "ESTADO_CIVIL_DISCREPANTE",
        "CONYUGE_NO_MENCIONADO",
        "CONYUGE_BIEN_PROPIO",
        "MENOR_DE_EDAD",
        "DOMICILIO_NO_ENCONTRADO",
        "DOMICILIO_HABILITACION",
        "GENERO",
    }
)


def capa_de(campo):
    """Pestaña de la observación: generales de ley (IDENTIDAD) o datos (REGLA)."""
    return "IDENTIDAD" if campo in _GENERALES_DE_LEY else "REGLA"


# F60: en estos avisos «debe decir» no tiene sentido. Solo presentación: la
# corrida guarda el texto de siempre, y también se ven así las ya guardadas.
_CORRIJA = " Corrija la que no corresponda."
# Qué verificar y el rótulo de la línea de la lista («rótulo: hallado»).
_AVISOS = {
    "NUMERO_EN_LETRAS": (
        "La cifra y las letras no valen lo mismo." + _CORRIJA,
        "Cifra y letras no coinciden",
    ),
    "AREA": (
        "La cifra y las letras del área no valen lo mismo." + _CORRIJA,
        "Cifra y letras no coinciden",
    ),
    "COPROPIEDAD": (
        "Las cuotas de copropiedad no suman 100 %." + _CORRIJA,
        "Las cuotas no suman 100 %",
    ),
    "NOMBRE_MARCA_AGUA": (
        "La ficha escaneada muestra una Ñ que puede ser la marca de agua. "
        "Verifique el nombre con el DNI.",
        "Posible Ñ por marca de agua",
    ),
    "DOCUMENTO_SIN_TITULAR": (
        "Ninguna persona de los recaudos tiene este documento. Verifique el número.",
        "Sin titular en los recaudos",
    ),
}
# Frases que el adaptador guarda como «esperado» (parsear_observacion_regla).
_FRASES_AVISO = {
    "No coincide con ninguna fuente": (
        "No coincide con ninguna fuente. Verifique el dato en los documentos.",
        "No coincide con ninguna fuente",
    ),
    "Debe tener 8 dígitos": (
        "Debe tener 8 dígitos. Verifique el número.",
        "Debe tener 8 dígitos",
    ),
}


_RE_SUGIERE = re.compile(
    r"se sugiere(?: corregir (?P<que>las letras|la cifra))? «(?P<texto>[^»]*)»"
)
_RE_DICE = re.compile(r"(?P<quien>la minuta|las letras) dicen? «(?P<texto>[^»]*)»")


def _aviso_con_sugerencia(campo, hallado, esperado, fila):
    """F64: el aviso con lo que dice la minuta y la sugerencia; None si la
    observación no la trae (las guardadas antes de F64 se ven como siempre).
    F65: la nota y la sugerencia también por separado, para la fila de la lista."""
    detalle = fila.get("detalle") or ""
    sugiere = _RE_SUGIERE.search(detalle)
    dice = {m["quien"]: m["texto"] for m in _RE_DICE.finditer(detalle)}
    sin_dato = "la minuta no trae el dato" in detalle
    que = "Se sugiere"
    if campo == "COPROPIEDAD":
        suma = re.search(r"las cuotas suman ([^;]+)", detalle)
        if not suma or not (sugiere or sin_dato):
            return None
        rotulo = "Las cuotas no suman 100 %"
        nota = f"Las cuotas suman {suma[1]}. " + (
            f"La minuta dice {dice['la minuta']}."
            if sugiere
            else "La minuta no trae el reparto: revise cuál corresponde."
        )
    elif "letras mal escritas" in detalle and sugiere:
        rotulo = "Letras mal escritas"
        nota = "Las letras están mal escritas."
    elif sugiere and "la minuta" in dice:
        rotulo = "Cifra y letras no coinciden"
        nota = f"La minuta dice {dice['la minuta']}."
        que = f"Se sugiere corregir {sugiere['que']}"
    elif sin_dato and "las letras" in dice:
        rotulo = "Cifra y letras no coinciden"
        nota = (
            f"La cifra dice {esperado} y las letras dicen {dice['las letras']}. "
            "La minuta no trae este dato: revise cuál corresponde."
        )
    else:
        return None
    aviso = {"borrador": hallado, "verificar": nota, "lista": f"{rotulo}: {hallado}"}
    if sugiere:
        aviso["verificar"] += f" {que}: {sugiere['texto']}."
        aviso["lista"] += f" → {sugiere['texto']}"
        aviso |= {
            "nota": nota,
            "rotulo_sugerencia": que,
            "sugerencia": sugiere["texto"],
        }
    return aviso


def partes_distintas(dice, debe):
    """F65: los dos textos en tramos (texto, ¿distinto?): las palabras comunes
    del principio y del final quedan igual; lo del medio es lo que cambia."""
    a, b = dice.split(" "), debe.split(" ")
    inicio = 0
    while inicio < min(len(a), len(b)) and a[inicio] == b[inicio]:
        inicio += 1
    fin = 0
    while fin < min(len(a), len(b)) - inicio and a[-1 - fin] == b[-1 - fin]:
        fin += 1

    def tramos(palabras):
        medio = palabras[inicio : len(palabras) - fin]
        partes = [
            (" ".join(palabras[:inicio]) + " " * bool(inicio and medio), False),
            (" ".join(medio), True),
            (
                " " * bool(fin and medio) + " ".join(palabras[len(palabras) - fin :]),
                False,
            ),
        ]
        if not medio and inicio and fin:  # solo se agregó o quitó: une los extremos
            partes[2] = (" " + partes[2][0], False)
        return [(texto, distinto) for texto, distinto in partes if texto]

    return tramos(a), tramos(b)


def _cambio(fila):
    """F65: lo hallado y lo correcto con lo distinto resaltado; None si no hay
    con qué comparar (un aviso sin sugerencia o las cuotas de F64)."""
    aviso = fila.get("aviso") or {}
    if aviso:
        if not aviso.get("sugerencia") or fila.get("campo") == "COPROPIEDAD":
            return None
        dice, debe = aviso["borrador"], aviso["sugerencia"]
    else:
        dice, debe = fila.get("hallado") or "", fila.get("esperado") or ""
    if not dice or not debe or dice == "No aparece en el borrador":
        return None
    tramos_dice, tramos_debe = partes_distintas(dice, debe)
    return {"dice": tramos_dice, "debe": tramos_debe}


def aviso_de(fila):
    """F60: qué hay en el borrador, qué verificar y la línea de la lista de un
    aviso que no es una corrección; None si «Dice / Debe decir» tiene sentido."""
    campo = fila.get("campo") or fila.get("tipo")
    hallado, esperado = fila.get("hallado") or "", fila.get("esperado") or ""
    nombre, _, dato = hallado.partition(": ")
    fuente, _, valor = esperado.partition(": ")
    if sugerencia := _aviso_con_sugerencia(campo, hallado, esperado, fila):
        return sugerencia
    fijo = _AVISOS.get(campo) or _FRASES_AVISO.get(esperado)
    if fijo:
        verificar, rotulo = fijo
        lista = f"{rotulo}: {hallado}"
    elif campo == "CONYUGE_BIEN_PROPIO":
        verificar = (
            f"{fuente} indica {valor}. Confirme que el bien es propio; "
            "si no lo es, debe intervenir el cónyuge."
        )
        lista = f"{nombre}: {valor.lower()} según {fuente} · confirme bien propio"
    elif campo == "DOMICILIO_NO_ENCONTRADO":
        hallado = f"{nombre}: su domicilio de {fuente} no aparece en el borrador"
        verificar = (
            f"Domicilio según {fuente}: {valor}. "
            "Verifique el domicilio que el borrador indica para esta persona."
        )
        lista = f"{nombre}: su domicilio de {fuente} no aparece · {valor}"
    elif campo == "MENOR_DE_EDAD":
        hallado = nombre
        verificar = f"Es menor de edad: {dato}. {esperado}. Verifique cómo interviene."
        lista = f"{nombre}: {dato}"
    elif campo == "SIN_FICHA":
        verificar = (
            f"{esperado}. No se pudo verificar: revíselo a mano o cargue la ficha."
        )
        lista = f"{esperado.partition('; ')[0]}: {hallado}"
    elif campo == "ANEXO":
        verificar = (
            f"La minuta incluye «{esperado}». Verifique que el borrador lo incluya."
        )
        lista = f"Falta en el borrador: {esperado}"
    elif campo == "PRECIO":
        lista = "El acta no indica el precio de la transferencia"
        verificar = f"{lista}. Verifique que lo incluya."
    else:
        return None
    return {"borrador": hallado, "verificar": verificar, "lista": lista}


def severidad(campo):
    regla = CATALOGO_REGLAS["reglas"].get(campo)
    return regla["severidad"] if regla else CATALOGO_REGLAS["default_severidad"]


def _con_severidad(resultado):
    """Resultado con la severidad del catálogo en cada observación."""
    return {
        **resultado,
        "personas": [
            {**fila, "severidad": severidad(fila.get("tipo"))}
            for fila in resultado.get("personas", [])
        ],
        "regla": [
            {**fila, "severidad": severidad(fila.get("campo"))}
            for fila in resultado.get("regla", [])
        ],
        "ortografia": [
            {**fila, "severidad": severidad("ORTOGRAFIA")}
            for fila in resultado.get("ortografia", [])
        ],
    }


def hallazgos_canonicos(resultado):
    """JSON canónico de los hallazgos: claves ordenadas, sin espacios."""
    hallazgos = {
        clave: resultado.get(clave, []) for clave in ("personas", "regla", "ortografia")
    }
    hallazgos["estado"] = resultado.get("estado", "")
    hallazgos["mensaje"] = resultado.get("mensaje", "")
    return json.dumps(
        hallazgos, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )


def _sha256_texto(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _entrada_corrida(documento):
    texto = documento.texto_extraido
    return {
        "rol": documento.rol,
        "nombre": documento.nombre_original,
        "hash_archivo": documento.hash_archivo,
        "version_extractor": texto.version_extractor if texto else None,
        "hash_texto": _sha256_texto(texto.texto) if texto else None,
        "estado": documento.estado,
    }


def registrar_corrida(
    expediente,
    borrador,
    usuario,
    resultado,
    origen=Corrida.MANUAL,
    fuentes_documentos=None,
):
    """Crea la corrida inmutable y devuelve el resultado con severidad."""
    resultado = _con_severidad(resultado)
    hallazgos = hallazgos_canonicos(resultado)
    fuentes = (
        fuentes_documentos
        if fuentes_documentos is not None
        else list(
            expediente.documentos.filter(rol__in=Documento.ROLES_FUENTE)
            .select_related("texto_extraido")
            .order_by("pk")
        )
    )
    corrida = Corrida.objects.create(
        expediente=expediente,
        id_borrador=borrador.pk,
        hash_borrador=borrador.hash_archivo,
        entradas=[
            _entrada_corrida(documento)
            for documento in (
                borrador,
                *fuentes,
            )
        ],
        version_catalogo=CATALOGO_REGLAS["version"],
        version_software=settings.ERP_VERSION,
        usuario=usuario,
        # ponytail: sin fecha en el resultado (no llegó a las reglas) se usa la de hoy.
        fecha_referencia=resultado.get("fecha_referencia") or timezone.localdate(),
        estado=_ESTADOS_CORRIDA.get(resultado.get("estado"), Corrida.ERROR),
        hallazgos=hallazgos,
        huella=_sha256_texto(hallazgos),
        origen=origen,
        presentacion={
            "metricas": resultado.get("metricas", {}),
            "calidad_lectura": resultado.get("calidad_lectura", []),
            "extraccion": resultado.get("extraccion", {}),
            "linguistico_aviso": resultado.get("linguistico_aviso", ""),
            "correcciones": resultado.get("correcciones", []),
        },
    )
    return {**resultado, "corrida_id": corrida.pk}


def _con_cambio(fila):
    return {**fila, "cambio": _cambio(fila)}


def resultado_de_corrida(corrida):
    """Resultado para la pantalla de confrontación, sin recalcular (F26)."""
    hallazgos = json.loads(corrida.hallazgos)
    # F42 y F60: la capa y el aviso son presentación; no entran en la huella.
    regla = [
        _con_cambio(
            {**fila, "capa": capa_de(fila.get("campo")), "aviso": aviso_de(fila)}
        )
        for fila in hallazgos.get("regla", [])
    ]
    return {
        **hallazgos,
        "personas": [
            _con_cambio({**fila, "aviso": aviso_de(fila)})
            for fila in hallazgos.get("personas", [])
        ],
        "regla": regla,
        "ortografia": [
            {
                **fila,
                "cambio": _cambio(
                    {"hallado": fila.get("palabra"), "esperado": fila.get("sugerencia")}
                ),
            }
            for fila in hallazgos.get("ortografia", [])
        ],
        "hay_generales": bool(hallazgos.get("personas"))
        or any(fila["capa"] == "IDENTIDAD" for fila in regla),
        "hay_datos": any(fila["capa"] == "REGLA" for fila in regla),
        **corrida.presentacion,
        "corrida_id": corrida.pk,
        "correcciones": corrida.presentacion.get("correcciones", []),
        "calidad_lectura": corrida.presentacion.get(
            "calidad_lectura",
            [
                {
                    "documento": "Resultado histórico",
                    "tipo": "SIN_MEDICION",
                    "paginas": [],
                }
            ],
        ),
    }


_CAMPOS_ENTRADA = ("rol", "nombre", "hash_archivo", "version_extractor", "estado")
# Los mismos datos, leídos de los documentos actuales.
_CAMPOS_DOCUMENTO = (
    "rol",
    "nombre_original",
    "hash_archivo",
    "texto_extraido__version_extractor",
    "estado",
)


def _primera_vigente(corridas, actuales):
    """Primera corrida cuyas entradas registradas son los documentos `actuales`."""
    for corrida in corridas:
        registradas = [[e[c] for c in _CAMPOS_ENTRADA] for e in corrida.entradas]
        if registradas == actuales:
            return corrida
    return None


def corrida_vigente(expediente, borrador):
    """Última corrida del borrador con sus entradas actuales y el catálogo actual.

    Compara metadatos sin cargar textos: el texto queda determinado por el hash
    del archivo y la versión del extractor.
    """
    actuales = [
        list(fila)
        for consulta in (
            Documento.objects.filter(pk=borrador.pk),
            expediente.documentos.filter(rol__in=Documento.ROLES_FUENTE).order_by("pk"),
        )
        for fila in consulta.values_list(*_CAMPOS_DOCUMENTO)
    ]
    corridas = expediente.corridas.filter(
        id_borrador=borrador.pk, version_catalogo=CATALOGO_REGLAS["version"]
    ).order_by("-pk")
    return _primera_vigente(corridas.only("entradas", "estado"), actuales)


def observaciones_vigentes(expedientes):
    """F59: total de observaciones de la corrida vigente del último borrador subido.

    Es el total de la pantalla de resultado (F48), contado igual que el ranking
    (F57). None si no hay corrida vigente o si no llegó a comparar. Tres
    consultas para toda la lista, sin importar cuántos kardex tenga.
    """
    borradores, fuentes = {}, {}
    filas = (
        Documento.objects.filter(expediente__in=expedientes)
        .order_by("pk")
        .values_list("expediente_id", "pk", *_CAMPOS_DOCUMENTO)
    )
    for expediente_id, pk, *fila in filas:
        if fila[0] == Documento.BORRADOR:
            borradores[expediente_id] = pk, fila  # queda el último subido
        else:
            fuentes.setdefault(expediente_id, []).append(fila)
    actuales = {
        pk: [fila, *fuentes.get(expediente_id, [])]
        for expediente_id, (pk, fila) in borradores.items()
    }
    candidatas = {}
    for corrida in (
        Corrida.objects.filter(
            id_borrador__in=list(actuales),
            version_catalogo=CATALOGO_REGLAS["version"],
        )
        .order_by("-pk")
        .only("id_borrador", "entradas", "estado")
    ):
        candidatas.setdefault(corrida.id_borrador, []).append(corrida)
    vigentes = [_primera_vigente(c, actuales[pk]) for pk, c in candidatas.items()]
    totales = {
        corrida.id_borrador: len(_observaciones(corrida))
        for corrida in Corrida.objects.filter(
            pk__in=[corrida.pk for corrida in vigentes if corrida],
            estado=Corrida.RESULTADO,
        ).only("id_borrador", "estado", "hallazgos")
    }
    return {
        expediente_id: totales.get(pk) for expediente_id, (pk, _) in borradores.items()
    }


def estado_borrador(expediente, borrador, fuentes=None):
    from .models import SolicitudConfrontacion

    estado = estado_confrontacion(expediente, borrador, fuentes)
    corrida = corrida_vigente(expediente, borrador) if estado["disponible"] else None
    solicitud = SolicitudConfrontacion.objects.filter(borrador=borrador).first()
    documentos = (
        list(fuentes)
        if fuentes is not None
        else list(expediente.documentos.filter(rol__in=Documento.ROLES_FUENTE))
    )
    roles = {d.rol for d in documentos} | {borrador.rol}
    puede = all(rol in roles for rol, _ in expediente.roles) and not any(
        d.estado == Documento.ERROR
        or (d.estado == Documento.LISTO and _texto_listo(d) is None)
        for d in [borrador, *documentos]
    )
    etapa = (
        "PREPARANDO"
        if any(
            d.estado in (Documento.PENDIENTE, Documento.PROCESANDO)
            for d in [borrador, *documentos]
        )
        else "PREPARADO"
    )
    if solicitud and solicitud.estado in ("CANCELADA", "CAMBIADA", "ERROR"):
        etapa = solicitud.estado
        estado["mensaje"] = {
            "CANCELADA": "Confrontación cancelada. Puede solicitarla de nuevo.",
            "CAMBIADA": "Los documentos cambiaron. Pulse Confrontar para revisar el conjunto actualizado.",
            "ERROR": "No se pudo completar la confrontación. Revise los documentos e intente nuevamente.",
        }[etapa]
    elif solicitud and solicitud.estado == "PROCESANDO":
        etapa = "CONFRONTANDO"
    elif solicitud and solicitud.estado == "PENDIENTE" and etapa == "PREPARADO":
        etapa = "EN_COLA"
    if corrida is not None:
        if corrida.estado != Corrida.ERROR:
            etapa = "LISTO"
            estado["mensaje"] = ""
        elif not solicitud or solicitud.estado not in ("PENDIENTE", "PROCESANDO"):
            etapa = "ERROR"
            estado["mensaje"] = (
                "No se pudo completar la confrontación. Intente nuevamente."
            )
    return {
        **estado,
        "resultado_listo": corrida is not None and corrida.estado != Corrida.ERROR,
        "etapa": etapa,
        "puede_solicitar": puede,
        "solicitada": bool(
            solicitud
            and solicitud.explicita
            and solicitud.estado in ("PENDIENTE", "PROCESANDO")
        ),
    }


def confrontar_automaticamente(limite=None):
    """Adelanta resultados y atiende solicitudes sin repetir entradas vigentes."""
    from .solicitudes import procesar

    creadas = 0
    borradores = Documento.objects.filter(
        Q(estado=Documento.LISTO)
        | Q(solicitud__estado__in=("PENDIENTE", "PROCESANDO")),
        rol=Documento.BORRADOR,
        expediente__archivado_el__isnull=True,
    ).order_by(F("solicitud__explicita").desc(nulls_last=True), "pk")
    for pk in borradores.values_list("pk", flat=True):
        creadas += procesar(pk)
        if limite and creadas >= limite:
            break
    return creadas


def _documento_reconstruido(corrida, entrada):
    texto = None
    if entrada["hash_texto"] is not None:
        texto = TextoExtraido.objects.filter(
            hash_archivo=entrada["hash_archivo"],
            version_extractor=entrada["version_extractor"],
        ).first()
        if texto is None or _sha256_texto(texto.texto) != entrada["hash_texto"]:
            raise CorridaNoReconstruible(
                f"El texto de {entrada['rol']} {entrada['hash_archivo'][:12]} "
                "no está disponible o cambió (¿suprimido?)."
            )
    return Documento(
        expediente=corrida.expediente,
        rol=entrada["rol"],
        nombre_original=entrada["nombre"],
        hash_archivo=entrada["hash_archivo"],
        estado=entrada["estado"],
        texto_extraido=texto,
    )


def reconstruir_corrida(corrida):
    """Repite la confrontación con las entradas registradas (Anexo B, P-08)."""
    avisos = []
    if corrida.version_catalogo != CATALOGO_REGLAS["version"]:
        avisos.append(
            f"Catálogo de reglas registrado {corrida.version_catalogo}, actual "
            f"{CATALOGO_REGLAS['version']}: se aplica el actual."
        )
    borrador, *fuentes = [
        _documento_reconstruido(corrida, entrada) for entrada in corrida.entradas
    ]
    try:
        resultado = confrontar_borrador(
            corrida.expediente, borrador, corrida.fecha_referencia, fuentes
        )
    except Exception:
        resultado = RESULTADO_ERROR
    hallazgos = hallazgos_canonicos(_con_severidad(resultado))
    huella = _sha256_texto(hallazgos)
    return {
        "conforme": huella == corrida.huella,
        "huella": huella,
        "total": len(filas_corrida(hallazgos)),
        "avisos": avisos,
    }


def filas_corrida(hallazgos):
    """Observaciones de una corrida en una sola tabla de solo lectura."""
    datos = json.loads(hallazgos)
    filas = [
        {**fila, "campo": fila.get("tipo"), "motivo": fila.get("motivo", "")}
        for fila in datos["personas"]
    ]
    filas.extend(datos["regla"])
    filas.extend(
        {
            **fila,
            "campo": "ORTOGRAFIA",
            "hallado": fila.get("palabra"),
            "esperado": fila.get("sugerencia"),
        }
        for fila in datos["ortografia"]
    )
    return [{**fila, "aviso": aviso_de(fila)} for fila in filas]


def corridas_con_resumen(expediente):
    """Corridas del expediente, de la más reciente, con hallazgos por severidad."""
    corridas = list(
        expediente.corridas.select_related("usuario").order_by("-creado_el", "-pk")
    )
    for corrida in corridas:
        corrida.severidades = Counter(
            fila.get("severidad") for fila in filas_corrida(corrida.hallazgos)
        )
    return corridas
