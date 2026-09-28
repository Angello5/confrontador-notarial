"""F26: confrontación automática al terminar la carga (datos ficticios)."""

import json
from io import StringIO

import pytest
from django.core.management import call_command

from tests.test_expedientes_confrontacion import (  # noqa: F401 fixtures reutilizados
    crear_documento_listo,
    expediente_confrontacion,
)
from tests.test_manifiesto_auditoria import caso  # noqa: F401 fixture reutilizado

pytestmark = pytest.mark.django_db


def _worker():
    call_command("procesar_documentos", stdout=StringIO())


def _estado(client, usuario, expediente):
    client.force_login(usuario)
    return client.get(f"/expedientes/{expediente.pk}/estado/").json()


def _borrador_estado(client, usuario, expediente, borrador):
    client.force_login(usuario)
    respuesta = client.get(f"/expedientes/{expediente.pk}/")
    (estado,) = [
        e for e in respuesta.context["borradores_estado"] if e["id"] == borrador.pk
    ]
    return estado, respuesta


def test_worker_confronta_al_quedar_todo_listo_y_no_duplica(
    usuario_ficticio,
    administrador_ficticio,
    caso,  # noqa: F811
):
    from expedientes.models import Corrida

    expediente, borrador = caso
    borrador.subido_por = administrador_ficticio
    borrador.save(update_fields=("subido_por",))

    _worker()
    corrida = Corrida.objects.get()
    assert corrida.origen == Corrida.AUTOMATICA
    assert corrida.usuario == administrador_ficticio
    assert corrida.id_borrador == borrador.pk
    assert corrida.estado == Corrida.RESULTADO
    assert corrida.presentacion["extraccion"]["documentos"]

    _worker()
    assert Corrida.objects.count() == 1


def test_worker_no_confronta_mientras_hay_documentos_en_proceso(
    usuario_ficticio,
    caso,
    crear_documento_listo,  # noqa: F811
):
    from expedientes.models import Corrida, Documento

    expediente, _ = caso
    crear_documento_listo(
        expediente,
        Documento.CLIENTE,
        "anexo-ficticio.pdf",
        "texto ficticio",
        estado=Documento.PROCESANDO,
    )

    _worker()
    assert not Corrida.objects.exists()


def test_worker_reconfronta_al_subir_o_eliminar_un_documento(
    usuario_ficticio,
    caso,
    crear_documento_listo,  # noqa: F811
):
    from expedientes.models import Corrida, Documento
    from expedientes.services import eliminar_documento

    expediente, _ = caso
    _worker()
    nuevo = crear_documento_listo(
        expediente, Documento.CLIENTE, "anexo-ficticio.pdf", "ALBA LUMARIA ZAFIRO"
    )
    _worker()
    assert Corrida.objects.count() == 2
    assert len(Corrida.objects.order_by("-pk").first().entradas) == 4

    eliminar_documento(nuevo, confirmado=True)
    _worker()
    assert Corrida.objects.count() == 3
    assert len(Corrida.objects.order_by("-pk").first().entradas) == 3
    _worker()
    assert Corrida.objects.count() == 3


def test_boton_confrontando_hasta_que_existe_la_corrida(
    client,
    usuario_ficticio,
    caso,  # noqa: F811
):
    expediente, borrador = caso

    estado, respuesta = _borrador_estado(client, usuario_ficticio, expediente, borrador)
    assert estado["disponible"] is True
    assert estado["resultado_listo"] is False
    assert estado["mensaje"] == ""
    contenido = respuesta.content.decode()
    assert "Confrontando…" in contenido
    assert respuesta.context["polling"] is True
    assert _estado(client, usuario_ficticio, expediente)["polling"] is True

    _worker()

    estado, respuesta = _borrador_estado(client, usuario_ficticio, expediente, borrador)
    assert estado["resultado_listo"] is True
    assert respuesta.context["polling"] is False
    contenido = respuesta.content.decode()
    assert "Ver resultado" in contenido
    assert f"/documentos/{borrador.pk}/resultado/" in contenido
    assert "Volver a confrontar" in contenido
    assert _estado(client, usuario_ficticio, expediente)["polling"] is False


def test_boton_en_proceso_no_esta_listo(
    client,
    usuario_ficticio,
    caso,
    crear_documento_listo,  # noqa: F811
):
    from expedientes.models import Documento

    expediente, borrador = caso
    _worker()
    crear_documento_listo(
        expediente,
        Documento.MINUTA,
        "minuta-2-ficticia.txt",
        "texto ficticio",
        estado=Documento.PENDIENTE,
    )

    estado, _ = _borrador_estado(client, usuario_ficticio, expediente, borrador)
    assert estado["disponible"] is False
    assert estado["resultado_listo"] is False


def test_sondeo_json_solo_agrega_resultado_listo(
    client,
    usuario_ficticio,
    caso,  # noqa: F811
):
    expediente, borrador = caso
    _worker()

    datos = _estado(client, usuario_ficticio, expediente)
    (item,) = datos["borradores"]
    assert set(item) == {"id", "disponible", "mensaje", "resultado_listo"}
    assert item["resultado_listo"] is True
    contenido = json.dumps(datos)
    for sensible in ("huella", "corrida", "resultado/", "MENOR_DE_EDAD", "90000011"):
        assert sensible not in contenido


def test_ver_resultado_muestra_la_corrida_sin_recalcular(
    client,
    usuario_ficticio,
    caso,
    monkeypatch,  # noqa: F811
):
    from expedientes.models import Corrida

    expediente, borrador = caso
    _worker()
    hallazgos = json.loads(Corrida.objects.get().hallazgos)
    monkeypatch.setattr(
        "expedientes.services.verificar.revisar",
        lambda *_: pytest.fail("no debe recalcular"),
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.catalogo",
        lambda *_: pytest.fail("no debe recalcular"),
    )

    client.force_login(usuario_ficticio)
    respuesta = client.get(
        f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/resultado/"
    )

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert "MENOR_DE_EDAD" in {f["campo"] for f in hallazgos["regla"]}
    assert "17 años" in contenido
    assert "reniec-ficticio.pdf" in contenido
    assert respuesta.context["corrida"].origen == Corrida.AUTOMATICA
    assert Corrida.objects.count() == 1


def test_ver_resultado_sin_corrida_vuelve_al_expediente(
    client,
    usuario_ficticio,
    caso,  # noqa: F811
):
    expediente, borrador = caso
    client.force_login(usuario_ficticio)

    respuesta = client.get(
        f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/resultado/"
    )

    assert respuesta.status_code == 302
    assert respuesta.url == f"/expedientes/{expediente.pk}/"


def test_ver_resultado_exige_rol(client, caso):  # noqa: F811
    from django.contrib.auth import get_user_model

    expediente, borrador = caso
    _worker()
    client.force_login(get_user_model().objects.create_user(username="sin_rol"))

    respuesta = client.get(
        f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/resultado/"
    )
    assert respuesta.status_code == 403


def test_volver_a_confrontar_registra_corrida_manual(
    client,
    usuario_ficticio,
    caso,  # noqa: F811
):
    from expedientes.models import Corrida

    expediente, borrador = caso
    _worker()
    client.force_login(usuario_ficticio)

    respuesta = client.post(
        f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    )

    assert respuesta.status_code == 200
    assert list(Corrida.objects.order_by("pk").values_list("origen", flat=True)) == [
        Corrida.AUTOMATICA,
        Corrida.MANUAL,
    ]


def test_error_automatico_deja_corrida_error_y_permite_reintentar(
    client,
    usuario_ficticio,
    caso,
    monkeypatch,  # noqa: F811
):
    from expedientes.models import Corrida

    expediente, borrador = caso
    with monkeypatch.context() as parche:
        parche.setattr(
            "expedientes.services.verificar.revisar",
            lambda *_: (_ for _ in ()).throw(RuntimeError("detalle privado ficticio")),
        )
        _worker()
        _worker()

    corrida = Corrida.objects.get()
    assert corrida.estado == Corrida.ERROR
    assert corrida.origen == Corrida.AUTOMATICA

    estado, respuesta = _borrador_estado(client, usuario_ficticio, expediente, borrador)
    assert estado["resultado_listo"] is False
    assert estado["disponible"] is True
    assert estado["mensaje"]
    assert respuesta.context["polling"] is False
    assert "Volver a confrontar" in respuesta.content.decode()

    client.post(f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/")
    estado, _ = _borrador_estado(client, usuario_ficticio, expediente, borrador)
    assert estado["resultado_listo"] is True
