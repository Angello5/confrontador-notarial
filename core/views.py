from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.decorators.http import require_safe


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
    return render(
        request,
        "core/home.html",
        {"es_administrador": es_administrador, "es_usuario": es_usuario},
    )
