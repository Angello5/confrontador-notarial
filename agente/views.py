import json
import time

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from expedientes.views import _navegacion_contexto, _requiere_rol

from .models import ConsultaAgente
from .services import AgenteError, consultar, leer_adjunto

MAX_PREGUNTA = 20_000  # también se pega aquí texto del cliente
MAX_TURNOS = 6  # el historial viaja desde el navegador; el servidor no guarda contenido
MAX_ADJUNTOS = 8


def _habilitado(request):
    if not settings.AGENTE_ACTIVO:
        raise Http404
    _requiere_rol(request)


def _historial(crudo):
    return [
        (t["rol"], t["texto"][:20_000])
        for t in (crudo if isinstance(crudo, list) else [])[-MAX_TURNOS:]
        if isinstance(t, dict)
        and t.get("rol") in ("usuario", "agente")
        and isinstance(t.get("texto"), str)
    ]


def _documentos(crudo):
    return [
        {
            "nombre": str(d.get("nombre", "documento"))[:120],
            "texto": d["texto"],
            "aviso": str(d.get("aviso", ""))[:300],
        }
        for d in (crudo if isinstance(crudo, list) else [])[:MAX_ADJUNTOS]
        if isinstance(d, dict) and isinstance(d.get("texto"), str)
    ]


@login_required
@require_GET
def consulta(request):
    _habilitado(request)
    contexto = {
        **_navegacion_contexto(request),
        "max_contexto": settings.AGENTE_MAX_CONTEXTO,
    }
    return render(request, "agente/consulta.html", contexto)


@login_required
@require_POST
def adjuntar(request):
    """Lee un archivo y devuelve su texto al navegador; el servidor no lo guarda."""
    _habilitado(request)
    archivo = request.FILES.get("archivo")
    if not archivo:
        return JsonResponse({"error": "Elija un archivo."}, status=400)
    try:
        leido = leer_adjunto(archivo)
    except AgenteError as e:
        return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"nombre": archivo.name[:120], **leido})


@login_required
@require_POST
def preguntar(request):
    _habilitado(request)
    try:
        datos = json.loads(request.body)
        pregunta = str(datos.get("pregunta", "")).strip()[:MAX_PREGUNTA]
    except (ValueError, AttributeError):
        return JsonResponse({"error": "Consulta no válida."}, status=400)
    if not pregunta:
        return JsonResponse({"error": "Escriba una pregunta."}, status=400)
    documentos = _documentos(datos.get("documentos"))
    inicio = time.monotonic()
    try:
        respuesta, recortados = consultar(
            pregunta, documentos, _historial(datos.get("historial"))
        )
        error = None
    except AgenteError as e:
        respuesta, recortados, error = None, [], str(e)
    ConsultaAgente.objects.create(
        usuario=request.user,
        adjuntos=len(documentos),
        proveedor=settings.AGENTE_PROVEEDOR,
        ok=error is None,
        segundos=int(time.monotonic() - inicio),
    )
    if error:
        return JsonResponse({"error": error}, status=503)
    aviso = (
        f"Se recortó el texto de: {', '.join(recortados)} (límite {settings.AGENTE_MAX_CONTEXTO:,} "
        "caracteres). El estudio es parcial: adjunte por partes o solo lo más relevante."
        if recortados
        else ""
    )
    return JsonResponse({"respuesta": respuesta, "aviso": aviso})
