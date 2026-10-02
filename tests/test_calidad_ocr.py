"""Regresiones sintéticas: lectura inclinada, capa corrupta y trazabilidad."""

import math
import io
from types import SimpleNamespace

import pytest

from adaptadores import extraccion
from PIL import Image
import pymupdf


def resultado(angulo=0, diagonal=False, score=0.98):
    rad = math.radians(angulo)
    cos, sin = math.cos(rad), math.sin(rad)
    cajas = []
    for y in (10, 45, 80):
        cajas.append(
            [
                [x * cos - yy * sin, x * sin + yy * cos]
                for x, yy in ((0, y), (200, y), (200, y + 16), (0, y + 16))
            ]
        )
    textos = ["DNI: 90000001", "ALBA ZURBELIA LUMARIA", "IMPORTE: 12345.67"]
    if diagonal:
        cajas.append([[0, 0], [100, 100], [90, 110], [-10, 10]])
        textos.append("MARCA FICTICIA")
    return SimpleNamespace(txts=textos, boxes=cajas, scores=[score] * len(cajas))


@pytest.mark.parametrize("angulo", [-10, 7, 10])
def test_inclinacion_moderada_no_borra_los_campos(monkeypatch, angulo):
    monkeypatch.setattr(extraccion, "_ocr", lambda: lambda _: resultado(angulo, True))
    assert extraccion.ocr_lineas(b"ficticio") == (
        "DNI: 90000001\nALBA ZURBELIA LUMARIA\nIMPORTE: 12345.67"
    )


def test_marca_diagonal_aislada_no_es_texto_del_documento(monkeypatch):
    monkeypatch.setattr(extraccion, "_ocr", lambda: lambda _: resultado(0, True))
    assert "MARCA FICTICIA" not in extraccion.ocr_lineas(b"ficticio")


def test_una_unica_caja_inclinada_no_define_orientacion(monkeypatch):
    r = resultado(30)
    r.txts, r.boxes, r.scores = r.txts[:1], r.boxes[:1], r.scores[:1]
    monkeypatch.setattr(extraccion, "_ocr", lambda: lambda _: r)
    assert extraccion.ocr_lineas(b"ficticio") == ""


def test_capa_corrupta_larga_se_considera_dudosa():
    assert extraccion.capa_pdf_dudosa("\ufffd" * 100)
    assert extraccion.capa_pdf_dudosa("\x00" * 80 + "TEST")
    assert not extraccion.capa_pdf_dudosa(
        "Texto ficticio normal con nombres y cifras. " * 5
    )


def test_algoritmo_y_resolucion_invalidan_identidad_y_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(extraccion, "CACHE", tmp_path)
    anterior = extraccion.version_extractor()
    extraccion._cacheado(b"ficticio", lambda: "anterior")
    monkeypatch.setattr(extraccion, "DPI", extraccion.DPI + 1)
    assert extraccion.version_extractor() != anterior
    assert extraccion._cacheado(b"ficticio", lambda: "nuevo") == "nuevo"


def test_informe_conserva_confianza_y_cajas_sin_modificar_digitos(monkeypatch):
    monkeypatch.setattr(extraccion, "_ocr", lambda: lambda _: resultado(0, score=0.72))
    informe = extraccion.ocr_informe(b"ficticio", reintentar=False)
    assert informe["requiere_revision"]
    assert informe["confianza"] == pytest.approx(0.72)
    assert informe["cajas"][0]["texto"] == "DNI: 90000001"
    assert len(informe["cajas"][0]["puntos"]) == 4


def test_motor_sin_confianza_no_inventa_un_porcentaje(monkeypatch):
    r = resultado()
    del r.scores
    monkeypatch.setattr(extraccion, "_ocr", lambda: lambda _: r)
    informe = extraccion.ocr_informe(b"ficticio", reintentar=False)
    assert informe["confianza"] is None
    assert "confianza_no_disponible" in informe["motivos"]


def test_reintenta_lectura_escasa_y_no_mezcla_alternativas(monkeypatch):
    corto = resultado()
    corto.txts, corto.boxes, corto.scores = ["0000"], corto.boxes[:1], [0.99]
    respuestas = iter([corto, resultado()])
    monkeypatch.setattr(extraccion, "_ocr", lambda: lambda _: next(respuestas))
    imagen = Image.new("RGB", (40, 40), "black")
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    informe = extraccion.ocr_informe(buffer.getvalue())
    assert informe["intentos"] == 2
    assert informe["transformacion"]["giro"] == 180
    assert "DNI: 90000001" in informe["texto"]
    assert not informe["requiere_revision"]


def test_reintentos_acotados_y_pagina_vacia(monkeypatch):
    llamadas = []

    def motor(_):
        llamadas.append(1)
        return SimpleNamespace(txts=None, boxes=None, scores=None)

    monkeypatch.setattr(extraccion, "_ocr", lambda: motor)
    for color, esperado in [("black", 4), ("white", 1)]:
        llamadas.clear()
        buffer = io.BytesIO()
        Image.new("RGB", (40, 40), color).save(buffer, format="PNG")
        informe = extraccion.ocr_informe(buffer.getvalue())
        assert len(llamadas) == esperado
        assert informe["requiere_revision"]


def test_pdf_con_texto_normal_no_usa_ocr_y_capa_corrupta_si(tmp_path, monkeypatch):
    ruta = tmp_path / "ficticio.pdf"
    with pymupdf.open() as doc:
        doc.new_page().insert_text(
            (72, 72),
            "Texto ficticio suficientemente largo para superar cincuenta caracteres.",
        )
        doc.save(ruta)
    llamadas = []

    def motor(_):
        llamadas.append(1)
        return resultado()

    monkeypatch.setattr(extraccion, "_ocr", lambda: motor)
    assert extraccion._pdf_informe(ruta)[0]["metodo"] == "texto_pdf"
    assert not llamadas
    monkeypatch.setattr(pymupdf.Page, "get_text", lambda self: "\ufffd" * 100)
    assert extraccion._pdf_informe(ruta)[0]["metodo"] == "ocr"
    assert len(llamadas) == 1


def test_una_caja_dudosa_no_dispara_giros_de_una_pagina_bien_leida(monkeypatch):
    r = resultado()
    r.scores[0] = 0.64
    llamadas = []

    def motor(_):
        llamadas.append(1)
        return r

    monkeypatch.setattr(extraccion, "_ocr", lambda: motor)
    buffer = io.BytesIO()
    Image.new("RGB", (40, 40), "black").save(buffer, format="PNG")
    informe = extraccion.ocr_informe(buffer.getvalue())
    assert informe["requiere_revision"]
    assert len(llamadas) == 1


def test_capa_pdf_legible_no_se_sustituye_por_ocr_parcial(tmp_path, monkeypatch):
    ruta = tmp_path / "parcial.pdf"
    with pymupdf.open() as doc:
        doc.new_page()
        doc.save(ruta)
    original = "DOCUMENTO FICTICIO DNI 90000001. IMPORTE 12345.67. " * 3 + "\ufffd"
    monkeypatch.setattr(pymupdf.Page, "get_text", lambda self: original)
    monkeypatch.setattr(
        extraccion, "ocr_informe", lambda _: {"texto": "FICTICIO", "confianza": 0.99}
    )
    informe = extraccion._pdf_informe(ruta)[0]
    assert informe["texto"] == original
    assert informe["requiere_revision"]


def test_marcas_descartadas_conservan_posicion(monkeypatch):
    monkeypatch.setattr(extraccion, "_ocr", lambda: lambda _: resultado(0, True))
    informe = extraccion.ocr_informe(b"ficticio", reintentar=False)
    assert len(informe["descartadas"]) == 1
    assert len(informe["descartadas"][0]["puntos"]) == 4


def test_capa_pdf_corta_se_conserva_si_ocr_es_dudoso(tmp_path, monkeypatch):
    ruta = tmp_path / "corto.pdf"
    with pymupdf.open() as doc:
        doc.new_page()
        doc.save(ruta)
    original = "DNI: 90000001"
    monkeypatch.setattr(pymupdf.Page, "get_text", lambda self: original)
    monkeypatch.setattr(
        extraccion,
        "ocr_informe",
        lambda _: {"texto": "DNI: 90000007", "requiere_revision": True},
    )
    informe = extraccion._pdf_informe(ruta)[0]
    assert informe["texto"] == original
    assert informe["requiere_revision"]


def test_capa_residual_corta_cede_ante_ocr_dudoso_mas_completo(tmp_path, monkeypatch):
    ruta = tmp_path / "escaneo.pdf"
    with pymupdf.open() as doc:
        doc.new_page()
        doc.save(ruta)
    monkeypatch.setattr(pymupdf.Page, "get_text", lambda self: "Pagina 1")
    ocr = "DOCUMENTO FICTICIO DNI 90000001 IMPORTE 12345.67"
    monkeypatch.setattr(
        extraccion,
        "ocr_informe",
        lambda _: {"texto": ocr, "requiere_revision": True},
    )
    assert extraccion._pdf_informe(ruta)[0]["texto"] == ocr
