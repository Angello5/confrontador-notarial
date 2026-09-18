from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render


@login_required
def home(request):
    grupos = request.user.groups
    if not grupos.filter(name__in=("Administrador", "Usuario")).exists():
        raise PermissionDenied
    es_administrador = grupos.filter(name="Administrador").exists()
    return render(request, "core/home.html", {"es_administrador": es_administrador})
