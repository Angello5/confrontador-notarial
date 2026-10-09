from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import (
    CODIGO_OCUPADO,
    DocumentoUploadForm,
    ExpedienteForm,
    formatos_admitidos,
)
from .models import DecisionCorreccion, Documento, Expediente
from .solicitudes import cancelar, solicitar
from .services import (
    CorreccionNoAplicable,
    DocumentoDuplicado,
    aplicar_correcciones,
    confrontar_borrador,
    corrida_vigente,
    corridas_con_resumen,
    eliminar_documento,
    estado_borrador,
    estado_confrontacion,
    expedientes_con_resumen,
    filas_corrida,
    png_de_vista,
    registrar_corrida,
    registrar_documento,
    resultado_de_corrida,
    ruta_original,
    resumen_documento,
    resumen_expediente,
    ruta_corregido,
    usuario_puede_ver_expediente,
    vista_borrador,
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
    expediente = get_object_or_404(Expediente, pk=pk, archivado_el__isnull=True)
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


def _sondear(resumen, borradores):
    """Sondeo mientras se extrae o falta la confrontación automática (F26)."""
    return bool(
        resumen["pendientes"]
        or resumen["procesando"]
        or any(
            (b.get("etapa") == "PREPARADO" and b["disponible"])
            or b.get("etapa") in ("EN_COLA", "CONFRONTANDO")
            for b in borradores
        )
    )


def _render_detalle(request, expediente, upload_form=None, status=200):
    documentos = list(expediente.documentos.order_by("subido_el", "pk"))
    fuentes = [
        documento for documento in documentos if documento.rol in Documento.ROLES_FUENTE
    ]
    borradores = [
        documento for documento in documentos if documento.rol == Documento.BORRADOR
    ]
    for documento in documentos:
        if documento.rol == Documento.BORRADOR:
            documento.confrontacion_estado = estado_borrador(
                expediente, documento, fuentes
            )
    estado_general = estado_confrontacion(expediente, None, fuentes)
    roles = expediente.roles
    formularios = {
        rol: DocumentoUploadForm(expected_role=rol, roles=roles) for rol, _ in roles
    }
    if upload_form is not None:
        rol = upload_form.expected_role or upload_form.data.get("rol")
        formularios[rol if rol in formularios else Documento.CLIENTE] = upload_form
    etiquetas = dict(roles)
    descripciones = {
        Documento.CLIENTE: "DNI, partidas registrales y demás recaudos.",
        Documento.MINUTA: "Documento del encargo, normalmente Word.",
        Documento.BORRADOR: "Documento elaborado que se confrontará con los recaudos.",
    }
    vehicular = expediente.tipo == Expediente.VEHICULAR
    if vehicular:
        # F43: la transferencia vehicular se confronta con la información, sin minuta.
        etiquetas[Documento.CLIENTE] = "Información"
        descripciones[Documento.CLIENTE] = "Boleta informativa, DNI y cheques."
        descripciones[Documento.BORRADOR] = (
            "Acta elaborada que se confrontará con la información."
        )
    por_rol = {Documento.BORRADOR: borradores}
    zonas = [
        {
            "rol": rol,
            "titulo": etiquetas[rol],
            "descripcion": descripciones[rol],
            "documentos": por_rol.get(rol, [d for d in documentos if d.rol == rol]),
            "form": formularios[rol],
        }
        for rol, _ in roles
    ]
    borradores_estado = [
        {"id": borrador.pk, **borrador.confrontacion_estado} for borrador in borradores
    ]
    resumen = resumen_expediente(expediente)
    contexto = {
        "expediente": expediente,
        "documentos": documentos,
        "borradores": borradores,
        "borradores_estado": borradores_estado,
        "polling": _sondear(resumen, borradores_estado),
        "estado_general": estado_general,
        "zonas": zonas,
        "zonas_fuente": zonas[:-1],
        "zona_borrador": zonas[-1],
        "vehicular": vehicular,
        "documentos_estado": [
            {**resumen_documento(d), "nombre": d.nombre_original} for d in documentos
        ],
        "resumen": resumen,
        "formatos_admitidos": formatos_admitidos(),
        "max_file_size_mb": settings.EXPEDIENTES_MAX_FILE_SIZE / (1024 * 1024),
    }
    contexto.update(_navegacion_contexto(request))
    contexto["carga_config"] = {
        "documentos": contexto["documentos_estado"],
        "borradores": borradores_estado,
        "base": reverse("expediente_detalle", args=[expediente.pk]),
        "maximo": settings.EXPEDIENTES_MAX_FILE_SIZE,
        "extensiones": [e.strip().lower() for e in formatos_admitidos().split(",")],
        "roles": [[rol, etiquetas[rol]] for rol, _ in roles],
    }
    return render(
        request,
        "expedientes/detalle.html",
        contexto,
        status=status,
    )


@login_required
def expediente_lista(request, tipo=Expediente.NOTARIAL):
    _requiere_rol(request)
    if request.method == "POST":
        form = ExpedienteForm(request.POST, instance=Expediente(tipo=tipo))
        if form.is_valid():
            try:
                with transaction.atomic():
                    expediente = form.save(commit=False)
                    expediente.creado_por = request.user
                    expediente.save()
            except IntegrityError:
                form.add_error("codigo", CODIGO_OCUPADO)
            else:
                messages.success(
                    request, "Kardex creado. Ahora puede cargar sus documentos."
                )
                return redirect("expediente_detalle", pk=expediente.pk)
    else:
        form = ExpedienteForm()
    contexto = _navegacion_contexto(request)
    archivados = contexto["es_administrador"] and request.GET.get("archivados") == "1"
    contexto.update(
        form=form,
        archivados=archivados,
        expedientes=expedientes_con_resumen(request.user, archivados, tipo),
        vehicular=tipo == Expediente.VEHICULAR,
    )
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
@require_http_methods(["GET", "POST"])
def expediente_editar(request, pk):
    _requiere_rol(request)
    expediente = _expediente_visible(request, pk)
    status = 200
    if request.method == "POST":
        form = ExpedienteForm(request.POST, instance=expediente)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except IntegrityError:
                form.add_error("codigo", CODIGO_OCUPADO)
            else:
                messages.success(request, "Kardex actualizado.")
                return redirect("expediente_detalle", pk=expediente.pk)
        status = 400
        # El formulario inválido ya cambió la instancia; la cabecera usa la guardada.
        expediente.refresh_from_db()
    else:
        form = ExpedienteForm(instance=expediente)
    contexto = {"expediente": expediente, "form": form}
    contexto.update(_navegacion_contexto(request))
    return render(request, "expedientes/editar.html", contexto, status=status)


@login_required
@require_http_methods(["GET", "POST"])
def expediente_eliminar(request, pk):
    _requiere_rol(request)
    expediente = _expediente_visible(request, pk)
    if request.method == "POST":
        expediente.archivado_el = timezone.now()
        expediente.archivado_por = request.user
        expediente.save(update_fields=["archivado_el", "archivado_por"])
        messages.success(request, f"Kardex {expediente.codigo} eliminado.")
        return redirect("expediente_lista")
    contexto = {"expediente": expediente}
    contexto.update(_navegacion_contexto(request))
    return render(request, "expedientes/eliminar.html", contexto)


@login_required
@require_POST
def expediente_restaurar(request, pk):
    if not _navegacion_contexto(request)["es_administrador"]:
        raise PermissionDenied
    expediente = get_object_or_404(Expediente, pk=pk, archivado_el__isnull=False)
    expediente.archivado_el = None
    expediente.archivado_por = None
    try:
        with transaction.atomic():
            expediente.save(update_fields=["archivado_el", "archivado_por"])
    except IntegrityError:
        messages.error(
            request,
            "No se puede restaurar: ya existe un kardex activo con el número "
            f"{expediente.codigo}. Cambie o elimine ese kardex primero.",
        )
        return redirect(f"{reverse('expediente_lista')}?archivados=1")
    messages.success(request, f"Kardex {expediente.codigo} restaurado.")
    return redirect("expediente_detalle", pk=expediente.pk)


@login_required
@require_POST
def documento_subir(request, pk):
    _requiere_rol(request)
    expediente = _expediente_visible(request, pk)
    form = DocumentoUploadForm(
        request.POST,
        request.FILES,
        expected_role=request.POST.get("rol"),
        roles=expediente.roles,
    )
    if not form.is_valid():
        if _quiere_json(request):
            return JsonResponse(
                {
                    "recibidos": [],
                    "errores": [
                        {"mensaje": str(error)}
                        for errores in form.errors.values()
                        for error in errores
                    ],
                },
                status=400,
            )
        return _render_detalle(request, expediente, form, status=400)

    registrados = 0
    recibidos = []
    errores = [
        {"nombre": nombre, "mensaje": motivo}
        for nombre, motivo in form.errores_archivos
    ]
    for nombre, motivo in form.errores_archivos:
        if not _quiere_json(request):
            messages.error(request, f"No se cargó {nombre}: {motivo}")
    for archivo in form.cleaned_data["archivos"]:
        try:
            documento = registrar_documento(
                expediente,
                archivo,
                form.cleaned_data["rol"],
                request.user,
            )
        except DocumentoDuplicado:
            if _quiere_json(request):
                # Una respuesta perdida se puede reintentar sin duplicar la entrada.
                errores.append(
                    {
                        "nombre": Path(archivo.name).name,
                        "mensaje": "Ya está registrado con este rol. Revise la lista de documentos.",
                    }
                )
            else:
                messages.error(
                    request,
                    f"No se cargó {Path(archivo.name).name}: ya está registrado con este rol.",
                )
        else:
            registrados += 1
            recibidos.append(
                {**resumen_documento(documento), "nombre": documento.nombre_original}
            )
    if _quiere_json(request):
        return JsonResponse(
            {"recibidos": recibidos, "errores": errores},
            status=200 if registrados else 400,
        )
    if not registrados:
        return _render_detalle(request, expediente, form, status=400)
    if registrados == 1:
        mensaje = "Documento recibido. Quedó en cola para extraer su texto."
    else:
        mensaje = f"{registrados} documentos recibidos. Quedaron en cola para extraer su texto."
    messages.success(request, mensaje)
    return redirect("expediente_detalle", pk=expediente.pk)


@login_required
@require_GET
def expediente_estado(request, pk):
    _requiere_rol(request)
    expediente = _expediente_visible(request, pk)
    resumen = resumen_expediente(expediente)
    documentos = list(expediente.documentos.all())
    fuentes = [
        documento for documento in documentos if documento.rol in Documento.ROLES_FUENTE
    ]
    borradores = [
        {
            "id": documento.pk,
            **estado_borrador(expediente, documento, fuentes),
        }
        for documento in documentos
        if documento.rol == Documento.BORRADOR
    ]
    return JsonResponse(
        {
            "expediente_id": expediente.pk,
            "estado": resumen["estado"],
            "resumen": resumen,
            "documentos": [
                {**resumen_documento(d), "nombre": d.nombre_original}
                for d in documentos
            ],
            "borradores": borradores,
            "polling": _sondear(resumen, borradores),
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
    if _quiere_json(request):
        return JsonResponse({"eliminado": True})
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
    try:
        listo = solicitar(expediente, borrador, request.user)
    except ValueError as exc:
        # Spec 014 FR-003: cada confrontación pedida queda en el manifiesto.
        registrar_corrida(
            expediente,
            borrador,
            request.user,
            confrontar_borrador(expediente, borrador),
        )
        if _quiere_json(request):
            return JsonResponse({"mensaje": str(exc)}, status=400)
        messages.error(request, str(exc))
        return redirect("expediente_detalle", pk=pk)
    if _quiere_json(request):
        return JsonResponse(
            estado_borrador(expediente, borrador), status=200 if listo else 202
        )
    if listo:
        return redirect("documento_resultado", pk=pk, doc_id=doc_id)
    messages.info(
        request, "Confrontación solicitada. Puede seguir trabajando y volver después."
    )
    return redirect("expediente_detalle", pk=pk)


def _quiere_json(request):
    return "application/json" in request.headers.get("Accept", "")


@login_required
@require_POST
def documento_cancelar_confrontacion(request, pk, doc_id):
    _requiere_rol(request)
    expediente = _expediente_visible(request, pk)
    borrador = get_object_or_404(
        expediente.documentos, pk=doc_id, rol=Documento.BORRADOR
    )
    cancelar(expediente, borrador, request.user)
    if _quiere_json(request):
        return JsonResponse(estado_borrador(expediente, borrador))
    messages.info(request, "Confrontación cancelada.")
    return redirect("expediente_detalle", pk=pk)


@login_required
@require_POST
def correcciones_aplicar(request, pk, doc_id):
    _requiere_rol(request)
    expediente = _expediente_visible(request, pk)
    borrador = get_object_or_404(
        expediente.documentos, pk=doc_id, rol=Documento.BORRADOR
    )
    contexto = {"expediente": expediente, "borrador": borrador}
    contexto.update(_navegacion_contexto(request))
    if request.POST.get("confirmado") != "1":
        contexto["error"] = "Confirme la aplicación de las correcciones para continuar."
        return _respuesta_aplicacion(request, contexto, status=400)
    try:
        contexto["aplicacion"] = aplicar_correcciones(
            expediente,
            borrador,
            request.POST.get("corrida", ""),
            request.POST.getlist("aplicar"),
            request.user,
        )
    except CorreccionNoAplicable as exc:
        contexto["error"] = str(exc)
        return _respuesta_aplicacion(request, contexto, status=400)
    return _respuesta_aplicacion(request, contexto)


def _nombre_corregido(decision):
    return f"{Path(decision.corrida.entradas[0]['nombre']).stem}-corregido.docx"


def _respuesta_aplicacion(request, contexto, status=200):
    """F40: el popup pide JSON para descargar directo; sin JavaScript, la página."""
    if not _quiere_json(request):
        return render(
            request, "expedientes/correccion_aplicada.html", contexto, status=status
        )
    if "error" in contexto:
        return JsonResponse({"error": contexto["error"]}, status=status)
    aplicacion = contexto["aplicacion"]
    return JsonResponse(
        {
            "archivo": _nombre_corregido(aplicacion),
            "descarga": reverse(
                "correccion_descargar", args=(contexto["expediente"].pk, aplicacion.pk)
            ),
            "aplicadas": len(aplicacion.apariciones),
            "excluidas": len(aplicacion.correcciones_excluidas),
            "no_aplicadas": len(aplicacion.correcciones_no_aplicadas),
        }
    )


@login_required
@require_GET
def correccion_descargar(request, pk, decision_id):
    _requiere_rol(request)
    expediente = _expediente_visible(request, pk)
    decision = get_object_or_404(
        DecisionCorreccion.objects.select_related("corrida"),
        pk=decision_id,
        corrida__expediente=expediente,
    )
    ruta = ruta_corregido(decision)
    if not decision.hash_corregido or not ruta.is_file():
        raise Http404
    return FileResponse(
        ruta.open("rb"), as_attachment=True, filename=_nombre_corregido(decision)
    )


@login_required
@require_GET
def expediente_historial(request, pk):
    _requiere_rol(request)
    expediente = _expediente_visible(request, pk)
    contexto = {
        "expediente": expediente,
        "corridas": corridas_con_resumen(expediente),
    }
    contexto.update(_navegacion_contexto(request))
    return render(request, "expedientes/historial.html", contexto)


@login_required
@require_GET
def corrida_detalle(request, pk, corrida_id):
    _requiere_rol(request)
    expediente = _expediente_visible(request, pk)
    corrida = get_object_or_404(
        expediente.corridas.select_related("usuario"), pk=corrida_id
    )
    contexto = {
        "expediente": expediente,
        "corrida": corrida,
        "filas": filas_corrida(corrida.hallazgos),
        "decisiones": corrida.decisiones.select_related("usuario").order_by("pk"),
    }
    contexto.update(_navegacion_contexto(request))
    return render(request, "expedientes/corrida.html", contexto)


@login_required
@require_GET
def documento_resultado(request, pk, doc_id):
    """Resultado guardado de la corrida vigente, sin recalcular (F26)."""
    _requiere_rol(request)
    expediente = _expediente_visible(request, pk)
    borrador = get_object_or_404(
        expediente.documentos, pk=doc_id, rol=Documento.BORRADOR
    )
    corrida = corrida_vigente(expediente, borrador)
    if corrida is None:
        messages.info(request, "El resultado aún no está listo.")
        return redirect("expediente_detalle", pk=expediente.pk)
    contexto = {
        "expediente": expediente,
        "borrador": borrador,
        # F21 (vista consolidada de correcciones) usa la corrida al fusionarse.
        "corrida": corrida,
        "resultado": {
            **resultado_de_corrida(corrida),
            "corregible": ruta_original(borrador).is_file(),
        },
    }
    contexto.update(_navegacion_contexto(request))
    return render(request, "expedientes/confrontacion.html", contexto)


def _borrador_y_corrida(request, pk, doc_id):
    """F32: el borrador del expediente y la corrida que el usuario está viendo."""
    _requiere_rol(request)
    expediente = _expediente_visible(request, pk)
    borrador = get_object_or_404(
        expediente.documentos, pk=doc_id, rol=Documento.BORRADOR
    )
    corrida_id = request.GET.get("corrida", "")
    if not corrida_id.isdigit():
        raise Http404
    corrida = get_object_or_404(
        expediente.corridas, pk=int(corrida_id), id_borrador=borrador.pk
    )
    return borrador, corrida


def _sin_cache(respuesta):
    # Páginas con datos personales: nada queda en la caché de un PC compartido.
    respuesta["Cache-Control"] = "no-store"
    respuesta["X-Content-Type-Options"] = "nosniff"
    return respuesta


@login_required
@require_GET
def documento_vista(request, pk, doc_id):
    borrador, corrida = _borrador_y_corrida(request, pk, doc_id)
    return _sin_cache(JsonResponse(vista_borrador(borrador, corrida)))


@login_required
@require_GET
def documento_vista_pagina(request, pk, doc_id, numero):
    borrador, _corrida = _borrador_y_corrida(request, pk, doc_id)
    contenido = png_de_vista(borrador, numero)
    if contenido is None:
        raise Http404
    return _sin_cache(HttpResponse(contenido, content_type="image/png"))
