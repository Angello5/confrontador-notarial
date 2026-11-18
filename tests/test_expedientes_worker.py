"""Contrato del worker basado en la cola de la base de datos y estados documentales."""

from datetime import timedelta
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.utils import timezone

pytestmark = pytest.mark.django_db

FORMATOS = Path(__file__).parent / "fixtures" / "formatos"


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


@pytest.mark.parametrize(
    ("nombre", "esperado"),
    [
        ("tabla.docx", "90000004"),
        ("texto.pdf", "DOCUMENTO FICTICIO PARA PRUEBAS DE EXTRACCION"),
        ("datos.xlsx", "90000004"),
    ],
)
def test_worker_extrae_formatos_binarios_desde_temporal_real(
    usuario_ficticio, tmp_path, nombre, esperado
):
    from expedientes.models import Documento, Expediente
    from expedientes.services import calcular_hash, crear_temporal, procesar_documento

    origen = FORMATOS / nombre
    temporal = crear_temporal(origen, origen.name, tmp_path)
    expediente = Expediente.objects.create(
        codigo=f"EXP-FICTICIO-FORMATO-{origen.suffix[1:].upper()}",
        creado_por=usuario_ficticio,
    )
    documento = Documento.objects.create(
        expediente=expediente,
        rol="FUENTE",
        nombre_original=origen.name,
        hash_archivo=calcular_hash(temporal),
        tamano_bytes=origen.stat().st_size,
        ruta_temporal=str(temporal),
        subido_por=usuario_ficticio,
    )

    procesar_documento(documento.pk)
    documento.refresh_from_db()

    assert temporal.suffix == origen.suffix
    assert documento.estado == Documento.LISTO
    texto = documento.texto_extraido.texto
    assert esperado in texto
    assert "\x00" not in texto, (
        "El texto extraído contiene bytes 0x00: el extractor no reconoció el formato."
    )
    assert not temporal.exists()


def test_extraccion_binaria_no_devuelve_bytes_nulos(tmp_path):
    from adaptadores import extraccion
    from expedientes.services import crear_temporal

    origen = FORMATOS / "tabla.docx"
    temporal = crear_temporal(origen, origen.name, tmp_path)

    texto = extraccion.leer(temporal)

    assert "\x00" not in texto, (
        "El texto extraído contiene bytes 0x00: el extractor no reconoció el formato."
    )


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
        rol="CLIENTE",
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
                rol="CLIENTE" if indice == 0 else "BORRADOR",
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
        "expedientes.services.extraccion.leer_con_calidad",
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
        rol="CLIENTE",
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
        "expedientes.services.extraccion.leer_con_calidad",
        lambda _: "texto recuperado ficticio",
    )

    call_command("procesar_documentos")

    documento.refresh_from_db()
    assert documento.estado == "LISTO"
    assert not ruta.exists()


# --- F76 ---


def _pendiente(expediente, usuario, rol, indice):
    from expedientes.models import Documento

    return Documento.objects.create(
        expediente=expediente,
        rol=rol,
        nombre_original=f"f76-{indice}.txt",
        hash_archivo=f"{indice:x}" * 64,
        tamano_bytes=1,
        ruta_temporal="",
        subido_por=usuario,
    )


def test_la_cola_toma_primero_borrador_y_minuta(usuario_ficticio):
    from expedientes.models import Expediente
    from expedientes.services import tomar_pendiente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-F76-COLA", creado_por=usuario_ficticio
    )
    recaudo_1 = _pendiente(expediente, usuario_ficticio, "CLIENTE", 1)
    recaudo_2 = _pendiente(expediente, usuario_ficticio, "CLIENTE", 2)
    minuta = _pendiente(expediente, usuario_ficticio, "MINUTA", 3)
    borrador = _pendiente(expediente, usuario_ficticio, "BORRADOR", 4)

    tomados = [tomar_pendiente().pk for _ in range(4)]

    assert tomados == [minuta.pk, borrador.pk, recaudo_1.pk, recaudo_2.pk]
    assert tomar_pendiente() is None


def test_las_metricas_guardan_con_que_se_leyo(usuario_ficticio, monkeypatch, tmp_path):
    from expedientes.models import Documento, Expediente
    from expedientes.services import procesar_documento

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-F76-METRICAS", creado_por=usuario_ficticio
    )
    ruta = tmp_path / "metricas-ficticio.tmp"
    ruta.write_bytes(b"contenido ficticio")
    documento = Documento.objects.create(
        expediente=expediente,
        rol="CLIENTE",
        nombre_original="metricas-ficticio.pdf",
        hash_archivo="a" * 64,
        tamano_bytes=ruta.stat().st_size,
        ruta_temporal=str(ruta),
        subido_por=usuario_ficticio,
    )
    monkeypatch.setattr(
        "expedientes.services.extraccion.version_extractor", lambda: "ocr-ficticio-f76"
    )
    monkeypatch.setattr(
        "expedientes.services.extraccion.leer_con_calidad",
        lambda _: {
            "texto": "texto ficticio",
            "calidad": {"version": 4, "paginas": [{"pagina": 1}, {"pagina": 2}]},
        },
    )

    procesar_documento(documento.pk)
    documento.refresh_from_db()

    assert documento.estado == "LISTO"
    assert documento.metricas["openvino"] is False
    assert documento.metricas["procesos"] == 1
    assert documento.metricas["paginas"] == 2


def test_fallo_de_lectura_deja_error_sin_texto_y_sin_temporal(
    usuario_ficticio, monkeypatch, tmp_path
):
    from expedientes.models import Documento, Expediente
    from expedientes.services import procesar_documento

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-F76-FALLO", creado_por=usuario_ficticio
    )
    ruta = tmp_path / "fallo-ficticio.tmp"
    ruta.write_bytes(b"contenido ficticio")
    documento = Documento.objects.create(
        expediente=expediente,
        rol="CLIENTE",
        nombre_original="fallo-ficticio.pdf",
        hash_archivo="b" * 64,
        tamano_bytes=ruta.stat().st_size,
        ruta_temporal=str(ruta),
        subido_por=usuario_ficticio,
    )

    def falla(_):
        from concurrent.futures.process import BrokenProcessPool

        raise BrokenProcessPool("proceso de lectura ficticio terminado")

    monkeypatch.setattr(
        "expedientes.services.extraccion.version_extractor", lambda: "ocr-ficticio-f76"
    )
    monkeypatch.setattr("expedientes.services.extraccion.leer_con_calidad", falla)

    procesar_documento(documento.pk)
    documento.refresh_from_db()

    assert documento.estado == "ERROR"
    assert documento.error == "No se pudo procesar el archivo."
    assert documento.texto_extraido is None
    assert not ruta.exists()


def test_el_worker_no_arranca_con_configuracion_invalida(usuario_ficticio, monkeypatch):
    from django.core.management.base import CommandError

    from expedientes.models import Expediente
    from expedientes.services import tomar_pendiente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-F76-ARRANQUE", creado_por=usuario_ficticio
    )
    _pendiente(expediente, usuario_ficticio, "CLIENTE", 5)
    monkeypatch.setenv("OCR_MOTOR", "motor-ficticio")

    with pytest.raises(CommandError, match="OCR_MOTOR"):
        call_command("procesar_documentos")

    assert tomar_pendiente() is not None
