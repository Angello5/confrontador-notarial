"""F34: cargas y solicitudes con documentos exclusivamente ficticios."""

# ruff: noqa: F811
from unittest.mock import Mock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command

from tests.test_expedientes_confrontacion import (  # noqa: F401
    crear_documento_listo,
    expediente_confrontacion,
)
from tests.test_manifiesto_auditoria import caso  # noqa: F401

pytestmark = pytest.mark.django_db


def test_solicitud_rechaza_texto_suprimido(usuario_ficticio, caso):
    from expedientes.solicitudes import solicitar

    expediente, borrador = caso
    borrador.texto_extraido.texto = ""
    borrador.texto_extraido.save()
    with pytest.raises(ValueError, match="texto"):
        solicitar(expediente, borrador, usuario_ficticio)


def test_carga_json_no_extrae_y_conserva_errores_individuales(
    client, usuario_ficticio, expediente_confrontacion, monkeypatch, tmp_path, settings
):
    from expedientes.models import Documento

    settings.EXPEDIENTES_TEMP_DIR = tmp_path
    leer = Mock(side_effect=AssertionError("La subida no debe extraer"))
    monkeypatch.setattr("expedientes.services.extraccion.leer_con_calidad", leer)
    client.force_login(usuario_ficticio)
    response = client.post(
        f"/expedientes/{expediente_confrontacion.pk}/documentos/",
        {
            "rol": "MINUTA",
            "archivos": [
                SimpleUploadedFile("minuta-ficticia.txt", b"documento ficticio"),
                SimpleUploadedFile("invalido.bin", b"invalido"),
            ],
        },
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 200
    assert len(response.json()["recibidos"]) == 1
    assert len(response.json()["errores"]) == 1
    assert Documento.objects.get().estado == Documento.PENDIENTE
    leer.assert_not_called()


def test_confrontar_encola_sin_calcular_y_doble_click_reutiliza(
    client, usuario_ficticio, caso, monkeypatch
):
    from expedientes.models import Corrida, SolicitudConfrontacion

    expediente, borrador = caso
    calcular = Mock(side_effect=AssertionError("No calcular en la petición"))
    monkeypatch.setattr("expedientes.services.confrontar_borrador", calcular)
    client.force_login(usuario_ficticio)
    url = f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    assert client.post(url, HTTP_ACCEPT="application/json").status_code == 202
    token = SolicitudConfrontacion.objects.get().token
    assert client.post(url, HTTP_ACCEPT="application/json").status_code == 202
    assert SolicitudConfrontacion.objects.get().token == token
    assert not Corrida.objects.exists()
    calcular.assert_not_called()


def test_solicitud_admite_lectura_pendiente_y_conserva_usuario(
    usuario_ficticio, administrador_ficticio, caso
):
    from expedientes.models import Corrida, Documento
    from expedientes.solicitudes import solicitar
    from expedientes.services import confrontar_automaticamente

    expediente, borrador = caso
    fuente = expediente.documentos.filter(rol=Documento.MINUTA).get()
    fuente.estado = Documento.PROCESANDO
    fuente.save()
    solicitar(expediente, borrador, administrador_ficticio)
    assert confrontar_automaticamente() == 0
    fuente.estado = Documento.LISTO
    fuente.save()
    assert confrontar_automaticamente() == 1
    assert Corrida.objects.get().usuario == administrador_ficticio
    assert confrontar_automaticamente() == 0


def test_resultado_vigente_se_reutiliza_al_pulsar_confrontar(
    client, usuario_ficticio, caso, monkeypatch
):
    from expedientes.models import Corrida
    from expedientes.services import confrontar_automaticamente

    expediente, borrador = caso
    confrontar_automaticamente()
    monkeypatch.setattr(
        "expedientes.services.confrontar_borrador", Mock(side_effect=AssertionError)
    )
    client.force_login(usuario_ficticio)
    response = client.post(
        f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/",
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 200
    assert response.json()["resultado_listo"] is True
    assert Corrida.objects.count() == 1


def test_cancelar_durante_calculo_no_publica_ni_reinicia(
    caso, usuario_ficticio, monkeypatch
):
    from expedientes import services
    from expedientes.models import Corrida, SolicitudConfrontacion
    from expedientes.solicitudes import cancelar, solicitar

    expediente, borrador = caso
    solicitar(expediente, borrador, usuario_ficticio)
    original = services.confrontar_borrador

    def calcular(*args, **kwargs):
        cancelar(expediente, borrador, usuario_ficticio)
        return original(*args, **kwargs)

    monkeypatch.setattr(services, "confrontar_borrador", calcular)
    assert services.confrontar_automaticamente() == 0
    assert services.confrontar_automaticamente() == 0
    assert not Corrida.objects.exists()
    assert SolicitudConfrontacion.objects.get().estado == "CANCELADA"


def test_cambio_durante_calculo_no_publica_manifiesto_mezclado(
    caso, usuario_ficticio, crear_documento_listo, monkeypatch
):
    from expedientes import services
    from expedientes.models import Corrida, Documento, SolicitudConfrontacion
    from expedientes.solicitudes import solicitar

    expediente, borrador = caso
    solicitar(expediente, borrador, usuario_ficticio)
    original = services.confrontar_borrador

    def calcular(*args, **kwargs):
        resultado = original(*args, **kwargs)
        crear_documento_listo(
            expediente, Documento.CLIENTE, "nuevo-ficticio.txt", "anexo ficticio"
        )
        return resultado

    monkeypatch.setattr(services, "confrontar_borrador", calcular)
    assert services.confrontar_automaticamente() == 0
    assert not Corrida.objects.exists()
    assert SolicitudConfrontacion.objects.get().estado == "CAMBIADA"


def test_worker_confronta_listo_antes_de_otro_documento(caso, monkeypatch):
    from expedientes.models import Corrida

    def siguiente():
        assert Corrida.objects.exists(), "No esperar la cola global"
        return None

    monkeypatch.setattr(
        "expedientes.management.commands.procesar_documentos.tomar_pendiente", siguiente
    )
    call_command("procesar_documentos")


def test_duraciones_separadas_sin_contenido_documental(
    usuario_ficticio, caso, settings, tmp_path
):
    from expedientes.models import Corrida, Documento
    from expedientes.services import (
        confrontar_automaticamente,
        procesar_documento,
        registrar_documento,
    )

    settings.EXPEDIENTES_TEMP_DIR = tmp_path
    expediente, _ = caso
    documento = registrar_documento(
        expediente,
        SimpleUploadedFile("anexo-ficticio.txt", b"anexo ficticio de prueba"),
        Documento.CLIENTE,
        usuario_ficticio,
    )
    procesar_documento(documento.pk)
    documento.refresh_from_db()
    assert documento.estado == Documento.LISTO
    assert set(documento.metricas) == {
        "recepcion_servidor_segundos",
        "cola_segundos",
        "lectura_segundos",
        "reutilizada",
    }
    confrontar_automaticamente()
    metricas = Corrida.objects.get().presentacion["metricas"]
    assert set(metricas) == {
        "analisis_segundos",
        "campos_segundos",
        "comparacion_segundos",
    }
    for valor in (*documento.metricas.values(), *metricas.values()):
        assert isinstance(valor, (bool, int, float))


def test_cancelacion_exige_permiso_y_post(client, usuario_ficticio, caso):
    expediente, borrador = caso
    url = (
        f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/cancelar-confrontacion/"
    )
    assert client.post(url).status_code == 302
    client.force_login(usuario_ficticio)
    assert client.get(url).status_code == 405
    assert client.post(url, HTTP_ACCEPT="application/json").status_code == 200


def test_recalculo_automatico_no_hereda_usuario_ni_origen_manual(
    administrador_ficticio, caso, crear_documento_listo
):
    from expedientes.models import Corrida, Documento
    from expedientes.services import confrontar_automaticamente
    from expedientes.solicitudes import solicitar

    expediente, borrador = caso
    solicitar(expediente, borrador, administrador_ficticio)
    assert confrontar_automaticamente() == 1
    # Otro recaudo llega después: el recálculo no lo pidió quien pulsó antes.
    crear_documento_listo(
        expediente, Documento.CLIENTE, "otro-ficticio.txt", "DOCUMENTO FICTICIO"
    )
    assert confrontar_automaticamente() == 1
    ultima = Corrida.objects.order_by("-pk").first()
    assert ultima.origen == Corrida.AUTOMATICA
    assert ultima.usuario == borrador.subido_por


def test_resultado_de_otro_dia_o_version_sigue_vigente(caso, monkeypatch, settings):
    from datetime import date

    from expedientes.models import Corrida
    from expedientes.services import confrontar_automaticamente, corrida_vigente

    expediente, borrador = caso
    assert confrontar_automaticamente() == 1
    monkeypatch.setattr(
        "expedientes.services.timezone.localdate", lambda: date(2025, 7, 3)
    )
    settings.ERP_VERSION = "9.9.9-ficticia"
    # Mismas entradas: no se recalcula cada día ni con cada despliegue.
    assert corrida_vigente(expediente, borrador) is not None
    assert confrontar_automaticamente() == 0
    assert Corrida.objects.count() == 1
