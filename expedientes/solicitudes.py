"""Solicitud persistente y publicación de confrontaciones fuera de HTTP."""

import uuid
from time import perf_counter

from django.db import transaction
from django.utils import timezone

from .bloqueos import exclusivo
from .models import Corrida, Documento, Expediente, SolicitudConfrontacion

ACTIVAS = ("PENDIENTE", "PROCESANDO")


def solicitar(expediente, borrador, usuario):
    from .services import corrida_vigente, _texto_listo

    with transaction.atomic():
        Expediente.objects.select_for_update().get(pk=expediente.pk)
        documentos = list(expediente.documentos.all())
        roles = {d.rol for d in documentos}
        if any(rol not in roles for rol, _ in Documento.ROLES):
            raise ValueError(
                "Adjunte la minuta, el borrador y los documentos del cliente."
            )
        relevantes = [
            d
            for d in documentos
            if d.rol in Documento.ROLES_FUENTE or d.pk == borrador.pk
        ]
        if any(d.estado == Documento.ERROR for d in relevantes):
            raise ValueError(
                "Hay un documento que no se pudo leer. Reemplácelo antes de confrontar."
            )
        if any(
            d.estado == Documento.LISTO and _texto_listo(d) is None for d in relevantes
        ):
            raise ValueError(
                "El texto de un documento ya no está disponible. Vuelva a subirlo."
            )
        corrida = corrida_vigente(expediente, borrador)
        if corrida and corrida.estado != Corrida.ERROR:
            return True
        solicitud, creada = SolicitudConfrontacion.objects.get_or_create(
            borrador=borrador, defaults={"usuario": usuario}
        )
        if not creada and solicitud.estado in ACTIVAS:
            # Una precomputación ya activa también satisface el clic.
            solicitud.explicita = True
            solicitud.usuario = usuario
            solicitud.save(update_fields=["explicita", "usuario", "actualizada_el"])
            return False
        solicitud.token = uuid.uuid4()
        solicitud.estado = "PENDIENTE"
        solicitud.usuario = usuario
        solicitud.explicita = True
        solicitud.solicitada_el = timezone.now()
        solicitud.save()
        return False


def cancelar(expediente, borrador, usuario):
    with transaction.atomic():
        Expediente.objects.select_for_update().get(pk=expediente.pk)
        SolicitudConfrontacion.objects.update_or_create(
            borrador=borrador,
            defaults={"usuario": usuario, "estado": "CANCELADA", "token": uuid.uuid4()},
        )


def _entradas(borrador, fuentes):
    from .services import _entrada_corrida

    return [_entrada_corrida(d) for d in (borrador, *fuentes)]


def procesar(borrador_id):
    from . import services

    with exclusivo("confrontacion", borrador_id) as adquirido:
        if not adquirido:
            return 0
        borrador = (
            Documento.objects.select_related("expediente", "texto_extraido")
            .filter(pk=borrador_id)
            .first()
        )
        if not borrador:
            return 0
        expediente = borrador.expediente
        with transaction.atomic():
            expediente = Expediente.objects.select_for_update().get(pk=expediente.pk)
            if expediente.archivado_el:
                return 0
            borrador = (
                Documento.objects.select_related("texto_extraido")
                .filter(pk=borrador_id)
                .first()
            )
            if not borrador:
                return 0
            solicitud = SolicitudConfrontacion.objects.filter(borrador=borrador).first()
            if solicitud and solicitud.estado in ("CANCELADA", "CAMBIADA", "ERROR"):
                return 0
            vigente = services.corrida_vigente(expediente, borrador)
            reintento = (
                solicitud and solicitud.explicita and solicitud.estado in ACTIVAS
            )
            if vigente and not (vigente.estado == Corrida.ERROR and reintento):
                if solicitud:
                    solicitud.estado = (
                        "ERROR" if vigente.estado == Corrida.ERROR else "LISTO"
                    )
                    solicitud.save(update_fields=["estado", "actualizada_el"])
                return 0
            fuentes = list(
                expediente.documentos.filter(rol__in=Documento.ROLES_FUENTE)
                .select_related("texto_extraido")
                .order_by("pk")
            )
            if not services.estado_confrontacion(expediente, borrador, fuentes)[
                "disponible"
            ]:
                pendientes = any(
                    d.estado in (Documento.PENDIENTE, Documento.PROCESANDO)
                    for d in [borrador, *fuentes]
                )
                if solicitud and not pendientes:
                    solicitud.estado = "ERROR"
                    solicitud.save(update_fields=["estado", "actualizada_el"])
                return 0
            if not solicitud:
                solicitud = SolicitudConfrontacion.objects.create(
                    borrador=borrador, usuario=borrador.subido_por, explicita=False
                )
            solicitud.estado = "PROCESANDO"
            solicitud.save(update_fields=["estado", "actualizada_el"])
            token = solicitud.token
            entradas = _entradas(borrador, fuentes)
            fecha = timezone.localdate()
        inicio = perf_counter()
        metricas = {}
        try:
            resultado = services.confrontar_borrador(
                expediente,
                borrador,
                fecha=fecha,
                fuentes_documentos=fuentes,
                metricas=metricas,
            )
        except Exception:
            resultado = dict(services.RESULTADO_ERROR)
        resultado["metricas"] = metricas
        resultado["metricas"]["analisis_segundos"] = round(perf_counter() - inicio, 4)
        resultado["fecha_referencia"] = fecha
        with transaction.atomic():
            expediente = Expediente.objects.select_for_update().get(pk=expediente.pk)
            actual = SolicitudConfrontacion.objects.filter(
                borrador_id=borrador_id, token=token, estado="PROCESANDO"
            ).first()
            if not actual or expediente.archivado_el:
                return 0
            nuevo = (
                Documento.objects.select_related("texto_extraido")
                .filter(pk=borrador_id)
                .first()
            )
            nuevas_fuentes = list(
                expediente.documentos.filter(rol__in=Documento.ROLES_FUENTE)
                .select_related("texto_extraido")
                .order_by("pk")
            )
            if not nuevo or _entradas(nuevo, nuevas_fuentes) != entradas:
                actual.estado = "CAMBIADA"
                actual.save(update_fields=["estado", "actualizada_el"])
                return 0
            services.registrar_corrida(
                expediente,
                borrador,
                actual.usuario,
                resultado,
                Corrida.MANUAL if actual.explicita else Corrida.AUTOMATICA,
                fuentes_documentos=fuentes,
            )
            actual.estado = (
                "ERROR" if resultado["estado"] == "ERROR_SEGURO" else "LISTO"
            )
            actual.save(update_fields=["estado", "actualizada_el"])
            return 1
