"""Contrato de confrontacion F5 con datos completamente ficticios."""

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


@pytest.fixture
def expediente_confrontacion(usuario_ficticio):
    from expedientes.models import Expediente

    return Expediente.objects.create(
        codigo="EXP-FICTICIO-F5", creado_por=usuario_ficticio
    )


@pytest.fixture
def crear_documento_listo(usuario_ficticio):
    from expedientes.models import Documento, TextoExtraido

    def crear(expediente, rol, nombre, texto, *, estado=Documento.LISTO):
        extraido = TextoExtraido.objects.create(
            hash_archivo=(nombre.replace(".", "")[:64]).ljust(64, "0"),
            version_extractor="extractor-ficticio-v1",
            texto=texto,
            ultimo_uso_el=timezone.now(),
        )
        return Documento.objects.create(
            expediente=expediente,
            rol=rol,
            nombre_original=nombre,
            hash_archivo=extraido.hash_archivo,
            tamano_bytes=max(len(texto), 1),
            estado=estado,
            texto_extraido=extraido,
            subido_por=usuario_ficticio,
        )

    return crear


def test_precondiciones_no_confrontan_texto_vacio_ni_documento_no_listo(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        "",
    )
    llamadas = []
    monkeypatch.setattr(
        "expedientes.services.verificar.diagnostico",
        lambda *args: llamadas.append(args),
    )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert resultado["estado"] == "NO_DISPONIBLE"
    assert llamadas == []


def test_orquestacion_conserva_nombres_extensiones_y_umbral(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion,
        Documento.FUENTE,
        "minuta-ficticia.txt",
        "fuente de texto ficticia",
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.FUENTE,
        "identidad-ficticia.jpg",
        "fuente de identidad ficticia",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        "borrador de texto ficticio",
    )
    llamadas = {"catalogo": [], "diagnostico": [], "revisar": [], "parrafos": []}
    monkeypatch.setattr(
        "expedientes.services.verificar.catalogo",
        lambda fuentes: (
            llamadas["catalogo"].append(fuentes)
            or {"NOMBRE": set(), "DNI": set(), "PARTIDA": set(), "MONTO": set()}
        ),
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.diagnostico",
        lambda fuentes, texto: llamadas["diagnostico"].append((fuentes, texto)) or None,
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.revisar",
        lambda cat, texto, umbral: llamadas["revisar"].append(umbral) or ["regla"],
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.revisar_parrafos",
        lambda minutas, texto, umbral: (
            llamadas["parrafos"].append((minutas, umbral)) or ["parrafo"]
        ),
    )
    monkeypatch.setattr(
        "expedientes.services.diccionario.diccionario", lambda: (None, [])
    )
    monkeypatch.setattr("expedientes.services.diccionario.lista_casa", lambda: set())
    monkeypatch.setattr("expedientes.services.ortografia.revisar", lambda *args: [])
    documentos_antes = Documento.objects.count()

    resultado = confrontar_borrador(expediente_confrontacion, borrador)
    repetido = confrontar_borrador(expediente_confrontacion, borrador)

    assert set(llamadas["catalogo"][0]) == {
        "minuta-ficticia.txt",
        "identidad-ficticia.jpg",
    }
    assert set(llamadas["diagnostico"][0][0]) == set(llamadas["catalogo"][0])
    assert llamadas["parrafos"] == [(["fuente de texto ficticia"], 88)] * 2
    assert llamadas["revisar"] == [88] * 2
    assert resultado["regla"] == ["regla", "parrafo"]
    assert resultado["ortografia"] == []
    assert repetido == resultado
    assert Documento.objects.count() == documentos_antes


def test_orquestacion_pasa_nombres_del_catalogo_a_ortografia(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion,
        Documento.FUENTE,
        "fuente-ficticia.txt",
        "fuente ficticia",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        "borrador ficticio",
    )
    propios = []
    cat = {"NOMBRE": {"LUCAS PEREZ"}, "DNI": set(), "PARTIDA": set(), "MONTO": set()}
    monkeypatch.setattr("expedientes.services.verificar.catalogo", lambda _: cat)
    monkeypatch.setattr("expedientes.services.verificar.diagnostico", lambda *_: None)
    monkeypatch.setattr("expedientes.services.verificar.revisar", lambda *_: [])
    monkeypatch.setattr(
        "expedientes.services.verificar.revisar_parrafos", lambda *_: []
    )
    monkeypatch.setattr(
        "expedientes.services.diccionario.diccionario", lambda: (None, [])
    )
    monkeypatch.setattr("expedientes.services.diccionario.lista_casa", lambda: set())
    monkeypatch.setattr(
        "expedientes.services.ortografia.revisar",
        lambda texto, diccionario, lemas, lista, extra: (
            propios.append(extra) or [("palabraficticia", "motivo ficticio", "?")]
        ),
    )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert propios == [{"LUCAS", "PEREZ"}]
    assert resultado["ortografia"] == [("palabraficticia", "motivo ficticio", "?")]


def test_diagnostico_bloqueante_detiene_toda_ejecucion(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion,
        Documento.FUENTE,
        "fuente-ficticia.txt",
        "fuente ficticia",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        "borrador ficticio",
    )
    llamadas = []
    monkeypatch.setattr(
        "expedientes.services.verificar.diagnostico", lambda *_: "aviso ficticio"
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.catalogo",
        lambda *_: llamadas.append("catalogo"),
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.revisar", lambda *_: llamadas.append("regla")
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.revisar_parrafos",
        lambda *_: llamadas.append("parrafos"),
    )
    monkeypatch.setattr(
        "expedientes.services.ortografia.revisar",
        lambda *_: llamadas.append("ortografia"),
    )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert resultado["estado"] == "ADVERTENCIA_CORRESPONDENCIA"
    assert resultado["mensaje"] == "aviso ficticio"
    assert llamadas == []
