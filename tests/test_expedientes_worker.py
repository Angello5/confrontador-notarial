"""Contrato del worker basado en PostgreSQL y estados documentales."""

from datetime import timedelta

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


def test_worker_transiciona_documento_y_borra_temporal(usuario_ficticio, tmp_path):
    from expedientes.models import Documento, Expediente
    from expedientes.services import procesar_documento

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-030", creado_por=usuario_ficticio
    )
    ruta = tmp_path / "worker-ficticio.txt"
    ruta.write_bytes(b"entrada sintetica")
    documento = Documento.objects.create(
        expediente=expediente,
        rol="BORRADOR",
        nombre_original="worker-ficticio.txt",
        hash_archivo="f" * 64,
        tamano_bytes=ruta.stat().st_size,
        ruta_temporal=str(ruta),
        subido_por=usuario_ficticio,
    )

    procesar_documento(documento.pk)
    documento.refresh_from_db()

    assert documento.estado in {"LISTO", "ERROR"}
    assert not ruta.exists()


def test_worker_recupera_procesando_vencido_y_no_toma_dos_veces(
    usuario_ficticio,
):
    from expedientes.models import Documento, Expediente
    from expedientes.services import recuperar_documentos_vencidos, tomar_pendiente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-031", creado_por=usuario_ficticio
    )
    documento = Documento.objects.create(
        expediente=expediente,
        rol="FUENTE",
        nombre_original="pendiente-ficticio.txt",
        hash_archivo="1" * 64,
        tamano_bytes=4,
        estado="PROCESANDO",
        subido_por=usuario_ficticio,
    )
    Documento.objects.filter(pk=documento.pk).update(
        procesando_el=timezone.now() - timedelta(minutes=16)
    )

    assert recuperar_documentos_vencidos() == 1
    assert tomar_pendiente() is not None
    assert tomar_pendiente() is None
