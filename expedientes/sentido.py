"""F61 · Capa de sentido en el ERP: corre en el worker, después de la confrontación.

Lee los textos registrados en la corrida, llama al núcleo con los modelos locales
y guarda las anotaciones aparte (AnalisisSentido). No cambia la corrida ni el
documento. Con el interruptor apagado (SENTIDO_ACTIVO) no hace nada.
"""

import hashlib
import json
import logging
from time import perf_counter

from django.conf import settings
from django.db import transaction
from django.db.models import Max

from nucleo import sentido as nucleo

from .bloqueos import exclusivo
from .models import AnalisisSentido, Corrida, Documento, Expediente, TextoExtraido
from .services import CorridaNoReconstruible

logger = logging.getLogger(__name__)
_modelos = None  # se cargan una vez por proceso: el worker continuo los reutiliza

TIPOS = {
    "CONTRADICE": "Contradice la minuta",
    "OMITE": "Omite algo de la minuta",
    "AGREGA": "Agrega algo que la minuta no dice",
    "CAMBIO": "Cambia el sentido",
    "SIN_RESPALDO": "Sin respaldo en la minuta",
    "CONCORDANCIA": "Concordancia",
}
NIVELES = {nucleo.OBSERVACION: "Observación", nucleo.REVISAR: "Para revisar"}
CHIPS = {nucleo.OBSERVACION: "MEDIA", nucleo.REVISAR: "BAJA"}  # color del chip


def huella(anotaciones):
    """SHA-256 de las anotaciones: la misma entrada da la misma huella (P-01)."""
    texto = json.dumps(
        anotaciones, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def activa():
    return settings.SENTIDO_ACTIVO


def modelos_disponibles():
    from adaptadores.modelos_sentido import faltantes

    return not faltantes(settings.SENTIDO_MODELOS_DIR)


def _cargar():
    global _modelos
    if _modelos is None:
        from adaptadores.modelos_sentido import Modelos

        _modelos = Modelos.cargar(settings.SENTIDO_MODELOS_DIR, settings.SENTIDO_HILOS)
    return _modelos


def _documentos(corrida):
    """Documentos de la corrida con sus textos; falla si un texto cambió o se suprimió."""
    from .services import _documento_reconstruido

    return [_documento_reconstruido(corrida, e) for e in corrida.entradas]


def _textos(documentos):
    """(minuta, proyecto) tal como se confrontaron."""
    proyecto = documentos[0].texto_extraido.texto
    minuta = "\f".join(
        d.texto_extraido.texto for d in documentos[1:] if d.rol == Documento.MINUTA
    )
    return minuta, proyecto


def pendientes():
    """Última corrida con resultado de cada borrador de kardex, aún sin analizar."""
    from .services import corrida_vigente

    ultimas = (
        Corrida.objects.filter(
            expediente__archivado_el__isnull=True,
            expediente__tipo=Expediente.NOTARIAL,
        )
        .values("id_borrador")
        .annotate(ultima=Max("pk"))
        .values("ultima")
    )
    corridas = (
        Corrida.objects.filter(
            pk__in=ultimas, estado=Corrida.RESULTADO, analisis_sentido__isnull=True
        )
        .select_related("expediente")
        .order_by("-pk")
    )
    for corrida in corridas:
        borrador = corrida.expediente.documentos.filter(pk=corrida.id_borrador).first()
        if borrador and corrida_vigente(corrida.expediente, borrador) == corrida:
            yield corrida


def analizar(corrida, modelos=None):
    """Analiza una corrida y guarda el resultado. Devuelve 1 si lo guardó."""
    from adaptadores.modelos_sentido import ModelosNoDisponibles, version

    with exclusivo("sentido", corrida.pk) as adquirido:
        if not adquirido or AnalisisSentido.objects.filter(corrida=corrida).exists():
            return 0
        inicio = perf_counter()
        documentos = []
        try:
            modelos = modelos or _cargar()
            documentos = _documentos(corrida)
            minuta, proyecto = _textos(documentos)
            anotaciones = nucleo.anotar(
                minuta,
                proyecto,
                modelos.analizar,
                modelos.parecido,
                modelos.clasificadores,
            )
            estado = AnalisisSentido.LISTO
        except ModelosNoDisponibles as exc:
            # Sin registro: se reintenta cuando los modelos estén aprovisionados.
            logger.error("Capa de sentido sin modelos: %s", exc)
            return 0
        except Exception as exc:
            # Sin texto de los documentos en el registro (Ley 29733).
            logger.error(
                "Falló el análisis de sentido de la corrida %s (%s).",
                corrida.pk,
                type(exc).__name__,
            )
            anotaciones, estado = [], AnalisisSentido.ERROR
        with transaction.atomic():
            if anotaciones:
                # La supresión puede ocurrir mientras trabajan los modelos: con los
                # textos bloqueados se comprueba que siguen siendo los analizados.
                ids = [d.texto_extraido_id for d in documentos if d.texto_extraido_id]
                list(TextoExtraido.objects.select_for_update().filter(pk__in=ids))
                try:
                    _documentos(corrida)
                except CorridaNoReconstruible:
                    anotaciones, estado = [], AnalisisSentido.SUPRIMIDO
            AnalisisSentido.objects.create(
                corrida=corrida,
                estado=estado,
                anotaciones=anotaciones,
                version_modelos=version(),
                segundos=round(perf_counter() - inicio, 2),
                huella=huella(anotaciones),
            )
        return 1


def analizar_pendientes(limite=1, modelos=None):
    """Paso del worker: analiza hasta `limite` corridas si la capa está activa."""
    if not activa():
        return 0
    hechas = 0
    for corrida in pendientes():
        if hechas >= limite:
            break
        hechas += analizar(corrida, modelos)
    return hechas


def suprimir(textos):
    """Borra las oraciones guardadas (derecho de supresión); conserva la huella.

    `textos`: pares (hash_archivo, version_extractor) suprimidos. Alcanza a toda
    corrida que los usó, aunque su documento ya no exista o sea de otro expediente.
    """
    pares = set(textos)
    if not pares:
        return 0
    # F63: SQL Server no filtra dentro del JSON (`__contains`), se filtra aquí.
    # shortcut: recorre en memoria las entradas de todas las corridas analizadas;
    # pasar a una tabla de entradas si superan ~50 000 análisis.
    ids = [
        pk
        for pk, entradas in AnalisisSentido.objects.values_list(
            "pk", "corrida__entradas"
        )
        if any(
            (e.get("hash_archivo"), e.get("version_extractor")) in pares
            for e in entradas
        )
    ]
    return AnalisisSentido.objects.filter(pk__in=ids).update(
        estado=AnalisisSentido.SUPRIMIDO, anotaciones=[]
    )


def para_pantalla(corrida):
    """Estado y anotaciones de la sección «Sentido frente a la minuta», o None."""
    if (
        not activa()
        or corrida.estado != Corrida.RESULTADO
        or corrida.expediente.tipo != Expediente.NOTARIAL
    ):
        return None
    analisis = AnalisisSentido.objects.filter(corrida=corrida).first()
    if analisis is None:
        return {"estado": "PENDIENTE" if modelos_disponibles() else "NO_DISPONIBLE"}
    anotaciones = [
        {
            **a,
            "tipo_texto": TIPOS[a["tipo"]],
            "nivel_texto": NIVELES[a["nivel"]],
            "chip": CHIPS[a["nivel"]],
        }
        for a in analisis.anotaciones
    ]
    observaciones = sum(a["nivel"] == nucleo.OBSERVACION for a in anotaciones)
    revisar = len(anotaciones) - observaciones
    return {
        "estado": analisis.estado,
        "anotaciones": anotaciones,
        "observaciones": observaciones,
        "revisar": revisar,
        "texto_observaciones": f"{observaciones} observaci{'ón' if observaciones == 1 else 'ones'}",
        "texto_revisar": f"{revisar} para revisar",
    }
