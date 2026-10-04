"""F20: catálogo de reglas, severidad y manifiesto de auditoría (datos ficticios)."""

import hashlib

from tests.flujo_confrontacion import confrontar_y_ver
import json
from datetime import date
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import CommandError, call_command

from tests.test_expedientes_confrontacion import (  # noqa: F401 fixtures reutilizados
    crear_documento_listo,
    expediente_confrontacion,
)

pytestmark = pytest.mark.django_db

RENIEC = (
    "CUI: 90000011 - 5\nAPELLIDO PATERNO  LUMARIA\n"
    "APELLIDO MATERNO  ZAFIRO\nNOMBRES  ALBA\n"
    "ESTADO CIVIL  CASADA\nFECHA DE NACIMIENTO  03/07/2007\n"
    "DIRECCION  Av. Luna 12"
)
BORRADOR = "ALBA LUMARIA ZAFIRO, soltera, domiciliada en Calle Sol 8. DNI 90000011"


def _sha(texto):
    return hashlib.sha256(texto.encode()).hexdigest()


@pytest.fixture
def caso(expediente_confrontacion, crear_documento_listo, monkeypatch):  # noqa: F811
    from expedientes.models import Documento

    crear_documento_listo(
        expediente_confrontacion, Documento.CLIENTE, "reniec-ficticio.pdf", RENIEC
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-ficticia.txt",
        "ALBA LUMARIA ZAFIRO",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        BORRADOR,
    )
    monkeypatch.setattr(
        "expedientes.services.timezone.localdate", lambda: date(2025, 7, 2)
    )
    return expediente_confrontacion, borrador


def _confrontar(client, usuario, expediente, borrador):
    client.force_login(usuario)
    return confrontar_y_ver(
        client, f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    )


def test_catalogo_de_reglas_es_legible_versionado_y_con_severidad():
    from expedientes.services import CATALOGO_REGLAS, severidad

    assert CATALOGO_REGLAS["version"]
    campos = (
        "NOMBRE DNI PARTIDA MONTO PARRAFO NUMERO_EN_LETRAS DOCUMENTO_CRUZADO "
        "DOCUMENTO_SIN_TITULAR ESTADO_CIVIL_DISCREPANTE CONYUGE_NO_MENCIONADO "
        "MENOR_DE_EDAD DOMICILIO_NO_ENCONTRADO ORTOGRAFIA RUC DIRECCION"
    ).split()
    for campo in campos:
        regla = CATALOGO_REGLAS["reglas"][campo]
        assert regla["descripcion"]
        assert regla["severidad"] in {"ALTA", "MEDIA", "BAJA"}
    assert severidad("DNI") == "ALTA"
    assert severidad("MENOR_DE_EDAD") == "MEDIA"
    assert severidad("PARRAFO") == "MEDIA"
    assert severidad("ORTOGRAFIA") == "BAJA"
    assert severidad("CAMPO_FICTICIO_DESCONOCIDO") == "MEDIA"


def test_confrontar_registra_corrida_con_manifiesto_completo(
    client, usuario_ficticio, caso, settings
):
    from expedientes.models import Corrida
    from expedientes.services import CATALOGO_REGLAS

    expediente, borrador = caso
    respuesta = _confrontar(client, usuario_ficticio, expediente, borrador)

    assert respuesta.status_code == 200
    corrida = Corrida.objects.get()
    assert corrida.expediente == expediente
    assert corrida.usuario == usuario_ficticio
    assert corrida.estado == Corrida.RESULTADO
    assert corrida.id_borrador == borrador.pk
    assert corrida.hash_borrador == borrador.hash_archivo
    assert corrida.version_catalogo == CATALOGO_REGLAS["version"]
    assert corrida.version_software == settings.ERP_VERSION
    assert corrida.fecha_referencia == date(2025, 7, 2)
    assert corrida.creado_el is not None
    assert [e["rol"] for e in corrida.entradas] == ["BORRADOR", "CLIENTE", "MINUTA"]
    assert corrida.entradas[0]["hash_texto"] == _sha(BORRADOR)
    assert corrida.entradas[1]["hash_texto"] == _sha(RENIEC)
    assert all(
        e["version_extractor"] == "extractor-ficticio-v1" for e in corrida.entradas
    )
    assert corrida.huella == _sha(corrida.hallazgos)
    hallazgos = json.loads(corrida.hallazgos)
    assert corrida.hallazgos == json.dumps(
        hallazgos, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    assert "extraccion" not in hallazgos
    severidades = {fila["campo"]: fila["severidad"] for fila in hallazgos["regla"]}
    assert severidades["MENOR_DE_EDAD"] == "MEDIA"
    contenido = respuesta.content.decode()
    assert "Severidad" in contenido
    assert "MEDIA" in contenido


def test_tres_corridas_identicas_tienen_la_misma_huella(usuario_ficticio, caso):
    from expedientes.models import Corrida
    from expedientes.services import confrontar_borrador, registrar_corrida

    expediente, borrador = caso
    for _ in range(3):
        registrar_corrida(
            expediente,
            borrador,
            usuario_ficticio,
            confrontar_borrador(expediente, borrador),
        )

    assert Corrida.objects.count() == 3
    assert len(set(Corrida.objects.values_list("huella", flat=True))) == 1


def test_corrida_y_decision_son_inmutables(client, usuario_ficticio, caso):
    from django.contrib import admin
    from django.db.models import ProtectedError

    from expedientes.models import Corrida, DecisionCorreccion, RegistroInmutable

    expediente, borrador = caso
    _confrontar(client, usuario_ficticio, expediente, borrador)
    corrida = Corrida.objects.get()
    decision = DecisionCorreccion.objects.create(
        corrida=corrida, usuario=usuario_ficticio, correcciones_excluidas=[2]
    )

    for registro in (corrida, decision):
        with pytest.raises(RegistroInmutable):
            registro.save()
        with pytest.raises(RegistroInmutable):
            registro.delete()
        with pytest.raises(RegistroInmutable):
            type(registro).objects.update(creado_el=None)
        with pytest.raises(RegistroInmutable):
            type(registro).objects.all().delete()
        assert type(registro) not in admin.site._registry
    with pytest.raises(ProtectedError):
        expediente.delete()
    assert list(corrida.decisiones.all()) == [decision]


def test_reconstruir_corrida_conforme_aunque_cambie_la_fecha(
    client, usuario_ficticio, caso, monkeypatch
):
    from expedientes.models import Corrida

    expediente, borrador = caso
    _confrontar(client, usuario_ficticio, expediente, borrador)
    corrida = Corrida.objects.get()
    borrador.delete()
    monkeypatch.setattr(
        "expedientes.services.timezone.localdate", lambda: date(2030, 1, 1)
    )
    salida = StringIO()

    call_command("reconstruir_corrida", str(corrida.pk), stdout=salida)

    assert "CONFORME" in salida.getvalue()
    assert corrida.huella in salida.getvalue()


def test_reconstruir_informa_catalogo_distinto_y_diferencias(
    client, usuario_ficticio, caso, monkeypatch
):
    from expedientes.models import Corrida
    from expedientes.services import CATALOGO_REGLAS

    expediente, borrador = caso
    _confrontar(client, usuario_ficticio, expediente, borrador)
    corrida = Corrida.objects.get()
    monkeypatch.setitem(CATALOGO_REGLAS, "version", "catalogo-ficticio-futuro")
    salida = StringIO()
    call_command("reconstruir_corrida", str(corrida.pk), stdout=salida)
    assert "catalogo-ficticio-futuro" in salida.getvalue()
    assert corrida.version_catalogo in salida.getvalue()

    monkeypatch.setattr(
        "expedientes.services.verificar.revisar",
        lambda *_: ["[DNI] «90000099» no coincide con ninguna fuente"],
    )
    with pytest.raises(CommandError, match="DIFERENTE"):
        call_command("reconstruir_corrida", str(corrida.pk), stdout=StringIO())
    with pytest.raises(CommandError, match="no existe"):
        call_command("reconstruir_corrida", "999999", stdout=StringIO())


def test_reconstruir_detecta_texto_suprimido(client, usuario_ficticio, caso):
    from expedientes.models import Corrida

    expediente, borrador = caso
    _confrontar(client, usuario_ficticio, expediente, borrador)
    corrida = Corrida.objects.get()
    call_command("suprimir_texto_expediente", expediente.codigo, stdout=StringIO())

    with pytest.raises(CommandError, match="no está disponible"):
        call_command("reconstruir_corrida", str(corrida.pk), stdout=StringIO())


def test_fallo_a_medias_deja_corrida_error_sin_hallazgos(
    client, usuario_ficticio, caso, monkeypatch
):
    from expedientes.models import Corrida, Documento

    expediente, borrador = caso
    antes = list(Documento.objects.order_by("pk").values())
    monkeypatch.setattr(
        "expedientes.services.verificar.revisar",
        lambda *_: (_ for _ in ()).throw(RuntimeError("detalle privado ficticio")),
    )

    respuesta = _confrontar(client, usuario_ficticio, expediente, borrador)

    assert "No se pudo completar la confrontación" in respuesta.content.decode()
    corrida = Corrida.objects.get()
    assert corrida.estado == Corrida.ERROR
    hallazgos = json.loads(corrida.hallazgos)
    assert hallazgos["regla"] == hallazgos["personas"] == []
    assert "detalle privado ficticio" not in corrida.hallazgos
    assert corrida.version_catalogo
    assert len(corrida.entradas) == 3
    assert list(Documento.objects.order_by("pk").values()) == antes
    salida = StringIO()
    call_command("reconstruir_corrida", str(corrida.pk), stdout=salida)
    assert "CONFORME" in salida.getvalue()


def test_corrida_no_disponible_registra_version_y_hashes(
    client,
    usuario_ficticio,
    expediente_confrontacion,  # noqa: F811
    crear_documento_listo,  # noqa: F811
):
    from expedientes.models import Corrida, Documento

    borrador = crear_documento_listo(
        expediente_confrontacion, Documento.BORRADOR, "borrador-ficticio.txt", "x"
    )
    _confrontar(client, usuario_ficticio, expediente_confrontacion, borrador)
    corrida = Corrida.objects.get()
    assert corrida.estado == Corrida.NO_DISPONIBLE
    assert corrida.version_catalogo
    assert corrida.entradas[0]["hash_archivo"] == borrador.hash_archivo

    salida = StringIO()
    call_command("reconstruir_corrida", str(corrida.pk), stdout=salida)
    assert "CONFORME" in salida.getvalue()


def test_historial_y_detalle_con_permisos_del_expediente(
    client, usuario_ficticio, administrador_ficticio, caso
):
    from expedientes.models import Corrida

    expediente, borrador = caso
    _confrontar(client, usuario_ficticio, expediente, borrador)
    corrida = Corrida.objects.get()
    hallazgos = json.loads(corrida.hallazgos)
    medias = sum(f["severidad"] == "MEDIA" for f in hallazgos["regla"])

    detalle = client.get(f"/expedientes/{expediente.pk}/").content.decode()
    assert f"/expedientes/{expediente.pk}/confrontaciones/" in detalle

    historial = client.get(f"/expedientes/{expediente.pk}/confrontaciones/")
    contenido = historial.content.decode()
    assert historial.status_code == 200
    assert corrida.version_catalogo in contenido
    assert "usuario_ficticio" in contenido
    assert f">{medias}<" in contenido

    ficha = client.get(f"/expedientes/{expediente.pk}/confrontaciones/{corrida.pk}/")
    contenido = ficha.content.decode()
    assert ficha.status_code == 200
    assert corrida.huella in contenido
    assert "Menor de edad" in contenido
    assert "<form" not in contenido.split("<main", 1)[-1]

    otro = get_user_model().objects.create_user(username="otro_ficticio")
    otro.groups.add(Group.objects.get(name="Usuario"))
    client.force_login(otro)
    assert (
        client.get(f"/expedientes/{expediente.pk}/confrontaciones/").status_code == 403
    )
    assert (
        client.get(
            f"/expedientes/{expediente.pk}/confrontaciones/{corrida.pk}/"
        ).status_code
        == 403
    )
    client.force_login(administrador_ficticio)
    assert (
        client.get(f"/expedientes/{expediente.pk}/confrontaciones/").status_code == 200
    )
    assert (
        client.post(f"/expedientes/{expediente.pk}/confrontaciones/").status_code == 405
    )


def test_corrida_de_otro_expediente_no_se_muestra(client, usuario_ficticio, caso):
    from expedientes.models import Corrida, Expediente

    expediente, borrador = caso
    _confrontar(client, usuario_ficticio, expediente, borrador)
    corrida = Corrida.objects.get()
    otro = Expediente.objects.create(
        codigo="EXP-FICTICIO-OTRO", creado_por=usuario_ficticio
    )

    respuesta = client.get(f"/expedientes/{otro.pk}/confrontaciones/{corrida.pk}/")
    assert respuesta.status_code == 404


def test_sondeo_json_no_expone_corridas(client, usuario_ficticio, caso):
    expediente, borrador = caso
    _confrontar(client, usuario_ficticio, expediente, borrador)

    contenido = client.get(f"/expedientes/{expediente.pk}/estado/").content.decode()

    assert "huella" not in contenido
    assert "corrida" not in contenido.lower()
    assert "MENOR_DE_EDAD" not in contenido
