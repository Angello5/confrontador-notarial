from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import DocumentoUploadForm, ExpedienteForm, formatos_admitidos
from .models import Documento, Expediente
from .services import (
    DocumentoDuplicado,
    eliminar_documento,
    expedientes_visibles,
    registrar_documento,
    resumen_documento,
    resumen_expediente,
    estado_confrontacion,
    confrontar_borrador,
    usuario_puede_ver_expediente,
)


def _requiere_rol(request):
    if (
        not request.user.is_authenticated
        or not request.user.groups.filter(
            name__in=("Administrador", "Usuario")
        ).exists()
    ):
        raise PermissionDenied


def _expediente_visible(request, pk):
    expediente = get_object_or_404(Expediente, pk=pk)
    if not usuario_puede_ver_expediente(request.user, expediente):
        raise PermissionDenied
    return expediente


def _navegacion_contexto(request):
    grupos = request.user.groups
    return {
        "es_administrador": request.user.is_staff
        and grupos.filter(name="Administrador").exists(),
        "es_usuario": grupos.filter(name="Usuario").exists(),
    }


def _render_detalle(request, expediente, upload_form=None, status=200):
    documentos = expediente.documentos.order_by("subido_el", "pk")
    for documento in documentos:
        if documento.rol == Documento.BORRADOR:
            documento.confrontacion_estado = estado_confrontacion(expediente, documento)
    contexto = {
        "expediente": expediente,
        "documentos": documentos,
        "documentos_estado": [resumen_documento(documento) for documento in documentos],
        "resumen": resumen_expediente(expediente),
        "upload_form": upload_form or DocumentoUploadForm(),
        "formatos_admitidos": formatos_admitidos(),
        "max_file_size_mb": settings.EXPEDIENTES_MAX_FILE_SIZE / (1024 * 1024),
    }
    contexto.update(_navegacion_contexto(request))
    return render(
        request,
        "expedientes/detalle.html",
        contexto,
        status=status,
    )


@login_required
def expediente_lista(request):
    _requiere_rol(request)
    if request.method == "POST":
        form = ExpedienteForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    expediente = form.save(commit=False)
                    expediente.creado_por = request.user
                    expediente.save()
            except IntegrityError:
                form.add_error(
                    "codigo", "Ese código ya está registrado. Ingrese otro código."
                )
            else:
                messages.success(
                    request, "Expediente creado. Ahora puede cargar sus documentos."
                )
                return redirect("expediente_detalle", pk=expediente.pk)
    else:
        form = ExpedienteForm()
    expedientes = expedientes_visibles(request.user).order_by("-actualizado_el", "-pk")
    filas = [(expediente, resumen_expediente(expediente)) for expediente in expedientes]
    contexto = {"form": form, "expedientes": filas}
    contexto.update(_navegacion_contexto(request))
    return render(
        request,
        "expedientes/lista.html",
        contexto,
    )


@login_required
@require_GET
def expediente_detalle(request, pk):
    _requiere_rol(request)
    return _render_detalle(request, _expediente_visible(request, pk))


@login_required
@require_POST
def documento_subir(request, pk):
    _requiere_rol(request)
    expediente = _expediente_visible(request, pk)
    form = DocumentoUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return _render_detalle(request, expediente, form, status=400)

    try:
        registrar_documento(
            expediente,
            form.cleaned_data["archivo"],
            form.cleaned_data["rol"],
            request.user,
        )
    except DocumentoDuplicado:
        form.add_error(
            "archivo", "Ese archivo ya está registrado con este rol en el expediente."
        )
        return _render_detalle(request, expediente, form, status=400)
    messages.success(
        request, "Documento recibido. Quedó en cola para extraer su texto."
    )
    return redirect("expediente_detalle", pk=expediente.pk)


@login_required
@require_GET
def expediente_estado(request, pk):
    _requiere_rol(request)
    expediente = _expediente_visible(request, pk)
    resumen = resumen_expediente(expediente)
    documentos = [
        resumen_documento(documento) for documento in expediente.documentos.all()
    ]
    return JsonResponse(
        {
            "expediente_id": expediente.pk,
            "estado": resumen["estado"],
            "resumen": resumen,
            "documentos": documentos,
            "polling": bool(resumen["pendientes"] or resumen["procesando"]),
        }
    )


@login_required
@require_POST
def documento_eliminar(request, pk, doc_id):
    _requiere_rol(request)
    expediente = _expediente_visible(request, pk)
    documento = get_object_or_404(expediente.documentos, pk=doc_id)
    confirmado = any(
        request.POST.get(nombre, "").lower() in {"1", "true", "on", "si", "sí"}
        for nombre in ("confirmado", "confirmar", "confirmacion")
    )
    if not confirmado:
        messages.error(request, "Confirme la eliminación del documento para continuar.")
        return _render_detalle(request, expediente, status=400)
    eliminar_documento(documento, confirmado=True)
    messages.success(request, "Documento eliminado.")
    return redirect("expediente_detalle", pk=expediente.pk)


@login_required
@require_POST
def documento_confrontar(request, pk, doc_id):
    _requiere_rol(request)
    expediente = _expediente_visible(request, pk)
    borrador = get_object_or_404(
        expediente.documentos, pk=doc_id, rol=Documento.BORRADOR
    )
    resultado = confrontar_borrador(expediente, borrador)
    contexto = {
        "expediente": expediente,
        "borrador": borrador,
        "resultado": resultado,
    }
    contexto.update(_navegacion_contexto(request))
    return render(request, "expedientes/confrontacion.html", contexto)
