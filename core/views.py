from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_safe

from expedientes.services import (
    avisos_documentos_ilegibles,
    datos_inicio_administrador,
    expedientes_con_resumen,
)


def _es_administrador(usuario):
    return usuario.is_staff and usuario.groups.filter(name="Administrador").exists()


@login_required
@require_safe
def home(request):
    grupos = request.user.groups
    if not grupos.filter(name__in=("Administrador", "Usuario")).exists():
        raise PermissionDenied
    es_administrador = _es_administrador(request.user)
    es_usuario = grupos.filter(name="Usuario").exists()
    contexto = {
        "es_administrador": es_administrador,
        "es_usuario": es_usuario,
        "avisos": avisos_documentos_ilegibles(request.user),
    }
    if es_administrador:
        # F53: el administrador ve toda la notaría; solo consultas agregadas.
        datos = datos_inicio_administrador(request.user)
        contexto.update(datos_inicio=datos, cifras=datos["cifras"])
    else:
        # ponytail: un resumen por expediente visible; agregar en SQL si crecen a miles.
        filas = expedientes_con_resumen(request.user)
        estados = [resumen["estado"] for _, resumen in filas]
        contexto["metricas"] = {
            "total": len(filas),
            "procesando": estados.count("PROCESANDO"),
            "listos": estados.count("LISTO"),
            "errores": estados.count("ERROR"),
        }
        contexto["ultimos"] = filas[:5]
    return render(request, "core/home.html", contexto)


@login_required
@require_GET
def home_datos(request):
    """F53: los mismos datos del Inicio del administrador, para refrescarlo solo."""
    if not _es_administrador(request.user):
        raise PermissionDenied
    return JsonResponse(
        datos_inicio_administrador(request.user, request.GET.get("periodo", "semana"))
    )
