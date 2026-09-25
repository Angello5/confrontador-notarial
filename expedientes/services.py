import hashlib
import io
import logging
import os
import re
import secrets
import shutil
import unicodedata
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
_RE_DEBE_DECIR = re.compile(
    r"^debe decir\s+«(?P<esperado>[^»]*)»(?P<resto>.*)$", re.IGNORECASE
)
_RE_MOTIVO_CARATULA = re.compile(r"\s+(?P<motivo>\(caratula\))\s*$", re.IGNORECASE)


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
                "El documento pertenece a otra persona según las fuentes."
                if observacion["tipo"] == "DOCUMENTO_CRUZADO"
                else "El documento no pertenece a una persona conocida en las fuentes."
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
    buscado = _normalizar_ubicacion(valor) if valor else ""
    if not buscado:
        return {"linea": None, "fragmento": "No ubicada"}
    for numero, linea in enumerate(texto.splitlines(), start=1):
        if buscado in _normalizar_ubicacion(linea):
            fragmento = linea.strip()
            return {"linea": numero, "fragmento": fragmento[:160]}
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

    coincidencia = _RE_OBSERVACION_CAMPO.match(salida)
    if coincidencia:
        campo = coincidencia.group("campo")
        hallado = coincidencia.group("hallado")
        resto = coincidencia.group("resto")
        debe_decir = _RE_DEBE_DECIR.match(resto)
        if debe_decir:
            motivo = _RE_MOTIVO_CARATULA.search(debe_decir.group("resto"))
            return _observacion_regla(
                campo,
                hallado,
                debe_decir.group("esperado"),
                motivo.group("motivo") if motivo else "",
                texto_borrador,
            )
        if resto.lower().startswith("no coincide con ninguna fuente"):
            return _observacion_regla(
                campo,
                hallado,
                "No coincide con ninguna fuente",
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
            esperado = f"RENIEC: {observacion['esperado']}"
        filas.append(
            {
                "formato": "regla",
                "campo": tipo,
                "hallado": hallado,
                "esperado": esperado,
                "motivo": f"Fuente: {archivo}{pagina}",
                "porcentaje": "",
                "ubicacion": ubicar_valor(texto_borrador, nombre),
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
    faltantes = [etiqueta for rol, etiqueta in Documento.ROLES if rol not in roles]
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


def confrontar_borrador(expediente, borrador):
    """Ejecuta regla y ortografía sobre un borrador listo, sin persistir."""
    if borrador.expediente_id != expediente.pk or borrador.rol != Documento.BORRADOR:
        raise ValueError("El documento no es un borrador de este expediente.")

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
    # El catalogo se construye ANTES del diagnostico: si el aviso salta, el
    # usuario necesita ver que se extrajo para saber si el borrador es de otro
    # expediente o si el OCR no leyo los datos de las fuentes.
    catalogo = verificar.catalogo(fuentes)
    extraccion = _resumen_extraccion(fuentes_documentos, catalogo)
    aviso = verificar.diagnostico(fuentes, texto_borrador)
    if aviso:
        return {
            "estado": "ADVERTENCIA_CORRESPONDENCIA",
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
    reglas = verificar.revisar(catalogo, texto_borrador, _UMBRAL_PARRAFO)
    minutas = [
        documento.texto_extraido.texto
        for documento in fuentes_documentos
        if documento.rol == Documento.MINUTA
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
    observaciones_regla = adaptar_observaciones_regla(reglas, texto_borrador)
    if isinstance(catalogo, verificar.Catalogo):
        observaciones_regla.extend(
            _observaciones_f12_legibles(
                verificar.revisar_persona_ampliada(
                    catalogo, texto_borrador, timezone.localdate()
                ),
                texto_borrador,
            )
        )
    return {
        "estado": "RESULTADO",
        "mensaje": "",
        "personas": _observaciones_personas_legibles(
            observaciones_personas, texto_borrador
        ),
        "extraccion": extraccion,
        "regla": observaciones_regla,
        "ortografia": adaptar_observaciones_ortografia(faltas, texto_borrador),
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
