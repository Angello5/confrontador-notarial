"""F32: vista del borrador con observaciones marcadas en la página (ficticio)."""

from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from tests.test_correccion_expedientes import (  # noqa: F401 fixtures
    BORRADOR,
    _propuesta,
    directorios,
    escenario,
)

pytestmark = pytest.mark.django_db


def pdf_ficticio(destino, lineas):
    """PDF de una página con las líneas dadas, en lugar de convertir con LibreOffice."""
    import pymupdf

    doc = pymupdf.open()
    pagina = doc.new_page()
    for i, linea in enumerate(lineas):
        pagina.insert_text((40, 60 + 12 * i), linea, fontsize=6)
    doc.save(destino)
    doc.close()
    return destino


@pytest.fixture
def conversion(monkeypatch):
    """Sustituye la conversión del worker; devuelve las llamadas registradas."""
    from adaptadores import paginas

    llamadas = []

    def convertir(original, destino, lineas=BORRADOR.splitlines()):
        llamadas.append(original)
        return pdf_ficticio(destino, lineas)

    monkeypatch.setattr(paginas, "a_pdf", convertir)
    return llamadas


@pytest.fixture
def corrida(escenario):  # noqa: F811
    from expedientes.models import Corrida

    expediente, borrador, _ = escenario
    _, corrida_id = _propuesta(expediente, borrador)
    return Corrida.objects.get(pk=corrida_id)


def _vista_lista(borrador, corrida):
    from expedientes.services import preparar_vistas, vista_borrador

    assert vista_borrador(borrador, corrida)["estado"] == "PREPARANDO"
    assert preparar_vistas() == 1
    return vista_borrador(borrador, corrida)


def test_la_vista_se_pide_y_el_worker_la_prepara(escenario, corrida, conversion):  # noqa: F811
    from expedientes.services import preparar_vistas, resultado_de_corrida, ruta_vista

    _, borrador, _ = escenario
    vista = _vista_lista(borrador, corrida)
    assert len(conversion) == 1
    assert ruta_vista(borrador).is_file()
    assert preparar_vistas() == 0
    assert vista["estado"] == "LISTA"
    assert vista["paginas"][0]["numero"] == 1
    resultado = resultado_de_corrida(corrida)
    ubicadas = [
        f"{prefijo}{i}"
        for prefijo, clave in (("p", "personas"), ("r", "regla"), ("o", "ortografia"))
        for i, observacion in enumerate(resultado.get(clave) or [], 1)
        if observacion["ubicacion"].get("linea")
    ]
    assert ubicadas
    assert set(ubicadas) <= set(vista["marcas"])
    for rectangulos in vista["marcas"].values():
        for r in rectangulos:
            assert r["pagina"] == 1
            assert 0 <= r["x0"] < r["x1"] <= 1
            assert 0 <= r["y0"] < r["y1"] <= 1
    for no_ubicada in vista["no_ubicadas"]:
        assert no_ubicada["id"] not in vista["marcas"]


def test_la_vista_es_determinista(escenario, corrida, conversion):  # noqa: F811
    from expedientes.services import vista_borrador

    _, borrador, _ = escenario
    assert _vista_lista(borrador, corrida) == vista_borrador(borrador, corrida)


def test_valor_que_no_esta_en_la_pagina(escenario, corrida, monkeypatch):  # noqa: F811
    from adaptadores import paginas

    _, borrador, _ = escenario
    monkeypatch.setattr(
        paginas, "a_pdf", lambda o, d: pdf_ficticio(d, ["TEXTO FICTICIO DISTINTO"])
    )
    vista = _vista_lista(borrador, corrida)
    assert vista["marcas"] == {}
    assert {n["motivo"] for n in vista["no_ubicadas"]} == {"NO_EN_PAGINA"}


def test_observacion_ausente_del_borrador(escenario, conversion):  # noqa: F811
    from expedientes.models import Corrida
    from expedientes.services import registrar_corrida

    expediente, borrador, _ = escenario
    resultado = {
        "estado": "RESULTADO",
        "regla": [
            {
                "campo": "PARRAFO",
                "hallado": "",
                "esperado": "Clausula ficticia ausente.",
                "ubicacion": {"linea": None, "fragmento": "No ubicada"},
            }
        ],
    }
    corrida = Corrida.objects.get(
        pk=registrar_corrida(expediente, borrador, expediente.creado_por, resultado)[
            "corrida_id"
        ]
    )
    vista = _vista_lista(borrador, corrida)
    assert vista["no_ubicadas"] == [{"id": "r1", "motivo": "AUSENTE"}]


def test_error_de_conversion_se_informa_y_se_puede_reintentar(
    escenario,  # noqa: F811
    corrida,
    monkeypatch,
):
    from adaptadores import paginas
    from expedientes.services import preparar_vistas, vista_borrador

    _, borrador, _ = escenario

    def falla(original, destino):
        raise ValueError("conversión ficticia fallida")

    monkeypatch.setattr(paginas, "a_pdf", falla)
    assert vista_borrador(borrador, corrida)["estado"] == "PREPARANDO"
    assert preparar_vistas() == 0
    vista = vista_borrador(borrador, corrida)
    assert (vista["estado"], vista["motivo"]) == ("NO_DISPONIBLE", "CONVERSION")
    assert vista_borrador(borrador, corrida)["estado"] == "PREPARANDO"


def test_sin_original(escenario, corrida, conversion):  # noqa: F811
    from expedientes.services import borrar_originales, vista_borrador

    expediente, borrador, _ = escenario
    borrar_originales(expediente.pk, borrador.pk)
    assert vista_borrador(borrador, corrida)["motivo"] == "SIN_ORIGINAL"


def test_original_alterado(escenario, corrida, conversion):  # noqa: F811
    from expedientes.services import ruta_original, vista_borrador

    _, borrador, _ = escenario
    ruta = ruta_original(borrador)
    ruta.chmod(0o600)
    ruta.write_bytes(ruta.read_bytes() + b"alterado")
    assert vista_borrador(borrador, corrida)["motivo"] == "VERIFICACION"


def test_formato_sin_vista(escenario, corrida):  # noqa: F811
    from expedientes.services import vista_borrador

    _, borrador, _ = escenario
    borrador.nombre_original = "borrador-ficticio.pdf"
    vista = vista_borrador(borrador, corrida)
    assert (vista["estado"], vista["motivo"]) == ("NO_DISPONIBLE", "FORMATO")


def test_supresion_y_eliminacion_borran_la_vista(escenario, corrida, conversion):  # noqa: F811
    from expedientes.services import eliminar_documento, ruta_vista

    expediente, borrador, _ = escenario
    _vista_lista(borrador, corrida)
    ruta = ruta_vista(borrador)
    call_command("suprimir_texto_expediente", expediente.codigo, stdout=StringIO())
    assert not ruta.exists()
    ruta.write_bytes(b"%PDF ficticio")
    eliminar_documento(borrador, confirmado=True)
    assert not ruta.exists()


def test_el_worker_prepara_las_vistas_pedidas(escenario, corrida, conversion):  # noqa: F811
    from expedientes.services import ruta_vista, vista_borrador

    _, borrador, _ = escenario
    vista_borrador(borrador, corrida)
    call_command("procesar_documentos", stdout=StringIO())
    assert ruta_vista(borrador).is_file()


# ── Vistas ──


def _urls(expediente, borrador, corrida, pagina=None):
    args = (expediente.pk, borrador.pk)
    nombre = "documento_vista"
    if pagina is not None:
        args += (pagina,)
        nombre = "documento_vista_pagina"
    return reverse(nombre, args=args) + f"?corrida={corrida.pk}"


@pytest.fixture
def cliente(usuario_ficticio):
    c = Client()
    c.force_login(usuario_ficticio)
    return c


def test_vistas_exigen_sesion_y_rol(escenario, corrida):  # noqa: F811
    expediente, borrador, _ = escenario
    url = _urls(expediente, borrador, corrida)
    assert Client().get(url).status_code == 302
    sin_rol = get_user_model().objects.create_user(username="sin_rol_ficticio")
    c = Client()
    c.force_login(sin_rol)
    assert c.get(url).status_code == 403


def test_vistas_404_fuera_del_expediente(escenario, corrida, cliente):  # noqa: F811
    from expedientes.models import Documento, Expediente

    expediente, borrador, _ = escenario
    otro = Expediente.objects.create(
        codigo="EXP-FICTICIO-OTRO", creado_por=expediente.creado_por
    )
    minuta = expediente.documentos.get(rol=Documento.MINUTA)
    base = reverse("documento_vista", args=(expediente.pk, borrador.pk))
    for url in (
        reverse("documento_vista", args=(otro.pk, borrador.pk))
        + f"?corrida={corrida.pk}",
        reverse("documento_vista", args=(expediente.pk, minuta.pk))
        + f"?corrida={corrida.pk}",
        base,
        base + "?corrida=abc",
        base + f"?corrida={corrida.pk + 1000}",
    ):
        assert cliente.get(url).status_code == 404, url


def test_json_y_png_sin_cache(escenario, corrida, cliente, conversion, settings):  # noqa: F811
    from expedientes.services import preparar_vistas

    expediente, borrador, _ = escenario
    url = _urls(expediente, borrador, corrida)
    respuesta = cliente.get(url)
    assert respuesta.json()["estado"] == "PREPARANDO"
    assert respuesta["Cache-Control"] == "no-store"
    assert cliente.get(_urls(expediente, borrador, corrida, 1)).status_code == 404
    preparar_vistas()
    respuesta = cliente.get(url)
    assert respuesta.json()["estado"] == "LISTA"
    texto = respuesta.content.decode()
    assert str(settings.EXPEDIENTES_TEMP_DIR) not in texto
    assert str(settings.EXPEDIENTES_ORIGINALES_DIR) not in texto
    imagen = cliente.get(_urls(expediente, borrador, corrida, 1))
    assert imagen.status_code == 200
    assert imagen["Content-Type"] == "image/png"
    assert imagen["Cache-Control"] == "no-store"
    assert imagen["X-Content-Type-Options"] == "nosniff"
    assert imagen.content.startswith(b"\x89PNG")
    assert cliente.get(_urls(expediente, borrador, corrida, 2)).status_code == 404


def test_resultado_incluye_el_visor(escenario, corrida, cliente):  # noqa: F811
    expediente, borrador, _ = escenario
    pagina = cliente.get(
        reverse("documento_resultado", args=(expediente.pk, borrador.pk))
    ).content.decode()
    assert reverse("documento_vista", args=(expediente.pk, borrador.pk)) in pagina
    assert "Colores por severidad" in pagina
    assert "Documento original" in pagina
    assert 'class="panel visor-borrador"' in pagina
    assert f'data-corrida="{corrida.pk}"' in pagina


def test_vista_de_borrador_suprimido_durante_la_conversion_no_queda(
    escenario,  # noqa: F811
    corrida,
    monkeypatch,
):
    from adaptadores import paginas
    from expedientes.services import (
        borrar_originales,
        preparar_vistas,
        ruta_vista,
        vista_borrador,
    )

    _, borrador, _ = escenario
    vista_borrador(borrador, corrida)

    def convertir(original, destino):
        # La supresión llega mientras LibreOffice convierte.
        borrar_originales(borrador.expediente_id, borrador.pk)
        return pdf_ficticio(destino, ["TEXTO FICTICIO"])

    monkeypatch.setattr(paginas, "a_pdf", convertir)
    preparar_vistas()
    assert not ruta_vista(borrador).exists()


def test_limpieza_borra_carpetas_de_conversion_huerfanas(settings, tmp_path):
    import os
    import time

    settings.EXPEDIENTES_TEMP_DIR = tmp_path
    hace_25_horas = time.time() - 25 * 3600
    vieja = tmp_path / "tmpficticio"
    vieja.mkdir()
    (vieja / "original.pdf").write_bytes(b"pdf ficticio")
    os.utime(vieja, (hace_25_horas, hace_25_horas))
    reciente = tmp_path / "tmpreciente"
    reciente.mkdir()
    ajena = tmp_path / "otra-carpeta"
    ajena.mkdir()
    os.utime(ajena, (hace_25_horas, hace_25_horas))
    call_command("limpiar_temporales", stdout=StringIO())
    assert not vieja.exists()
    assert reciente.exists()
    assert ajena.exists()
