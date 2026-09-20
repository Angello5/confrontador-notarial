"""Contrato del worker basado en PostgreSQL y estados documentales."""

from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
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


def test_comando_procesa_dos_pendientes_borra_temporales_e_informa(
    usuario_ficticio, monkeypatch, tmp_path
):
    from expedientes.models import Documento, Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-032", creado_por=usuario_ficticio
    )
    documentos = []
    for indice in range(2):
        ruta = tmp_path / f"pendiente-{indice}.tmp"
        ruta.write_bytes(f"contenido ficticio {indice}".encode())
        documentos.append(
            Documento.objects.create(
                expediente=expediente,
                rol="FUENTE" if indice == 0 else "BORRADOR",
                nombre_original=f"documento-{indice}.txt",
                hash_archivo=str(indice + 2) * 64,
                tamano_bytes=ruta.stat().st_size,
                ruta_temporal=str(ruta),
                subido_por=usuario_ficticio,
            )
        )
    monkeypatch.setattr(
        "expedientes.services.extraccion.version_extractor",
        lambda: "ocr-ficticio-v1",
    )
    monkeypatch.setattr(
        "expedientes.services.extraccion.leer",
        lambda ruta: f"texto de {ruta.name}",
    )
    salida = StringIO()

    call_command("procesar_documentos", stdout=salida)

    for documento in documentos:
        documento.refresh_from_db()
        assert documento.estado == "LISTO"
        assert documento.ruta_temporal == ""
    assert not list(tmp_path.glob("*.tmp"))
    assert "Documentos procesados: 2" in salida.getvalue()


def test_comando_informa_cero_si_no_hay_pendientes(usuario_ficticio):
    from expedientes.models import Expediente

    Expediente.objects.create(codigo="EXP-FICTICIO-033", creado_por=usuario_ficticio)
    salida = StringIO()

    call_command("procesar_documentos", stdout=salida)

    assert salida.getvalue().strip() == "Documentos procesados: 0"


def test_comando_recupera_vencido_al_arrancar_y_lo_procesa(
    usuario_ficticio, monkeypatch, tmp_path
):
    from expedientes.models import Documento, Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-034", creado_por=usuario_ficticio
    )
    ruta = tmp_path / "vencido-ficticio.tmp"
    ruta.write_bytes(b"contenido vencido ficticio")
    documento = Documento.objects.create(
        expediente=expediente,
        rol="FUENTE",
        nombre_original="vencido-ficticio.txt",
        hash_archivo="7" * 64,
        tamano_bytes=ruta.stat().st_size,
        estado="PROCESANDO",
        procesando_el=timezone.now() - timedelta(minutes=16),
        ruta_temporal=str(ruta),
        subido_por=usuario_ficticio,
    )
    monkeypatch.setattr(
        "expedientes.services.extraccion.version_extractor",
        lambda: "ocr-ficticio-v1",
    )
    monkeypatch.setattr(
        "expedientes.services.extraccion.leer", lambda _: "texto recuperado ficticio"
    )

    call_command("procesar_documentos")

    documento.refresh_from_db()
    assert documento.estado == "LISTO"
    assert not ruta.exists()
