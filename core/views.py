from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.decorators.http import require_safe

from expedientes.services import (
    actividad_semanal,
    avisos_documentos_ilegibles,
    cifras_por_tipo,
    expedientes_con_resumen,
    ultimas_confrontaciones,
)


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
    contexto = {
        "es_administrador": es_administrador,
        "es_usuario": es_usuario,
        "avisos": avisos_documentos_ilegibles(request.user),
    }
    if es_administrador:
        # F53: el administrador ve toda la notaría; solo consultas agregadas.
        actividad = actividad_semanal()
        maximo = max(semana["kardex"] for semana in actividad)
        for semana in actividad:
            semana["alto"] = round(100 * semana["kardex"] / maximo) if maximo else 0
        contexto.update(
            cifras=cifras_por_tipo(request.user),
            actividad=actividad,
            confrontaciones=ultimas_confrontaciones(),
        )
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
