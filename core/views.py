from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.decorators.http import require_safe

from expedientes.services import expedientes_con_resumen


@login_required
@require_safe
def home(request):
    grupos = request.user.groups
    if not grupos.filter(name__in=("Administrador", "Usuario")).exists():
        raise PermissionDenied
    es_administrador = (
        request.user.is_staff and grupos.filter(name="Administrador").exists()
    )
    es_usuario = grupos.filter(name="Usuario").exists()
    # ponytail: un resumen por expediente visible; agregar en SQL si crecen a miles.
    filas = expedientes_con_resumen(request.user)
    estados = [resumen["estado"] for _, resumen in filas]
    metricas = {
        "total": len(filas),
        "procesando": estados.count("PROCESANDO"),
        "listos": estados.count("LISTO"),
        "errores": estados.count("ERROR"),
    }
    return render(
        request,
        "core/home.html",
        {
            "es_administrador": es_administrador,
            "es_usuario": es_usuario,
            "metricas": metricas,
            "ultimos": filas[:5],
        },
    )
