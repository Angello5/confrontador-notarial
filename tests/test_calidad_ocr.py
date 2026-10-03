"""Regresiones sintéticas: lectura inclinada, capa corrupta y trazabilidad."""

import math
import io
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from adaptadores import calidad_ocr, extraccion
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
    # F33: una hoja totalmente blanca ya no pasa por el motor.
    for color, esperado in [("black", 4), ("white", 0)]:
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


# ── F33 · Rendimiento del OCR ────────────────────────────────────────────────


def _caja(x, y, ancho, alto):
    return [[x, y], [x + ancho, y], [x + ancho, y + alto], [x, y + alto]]


def vertical(score=0.98):
    """Texto de una hoja de lado: RapidOCR reconoce las líneas en cajas altas."""
    r = resultado(score=score)
    r.boxes = [_caja(x, 10, 16, 200) for x in (10, 45, 80)]
    return r


def secuencia(*respuestas):
    """Motor falso que registra cada entrada y responde en orden."""
    entradas = []

    def motor(entrada):
        entradas.append(entrada)
        return respuestas[min(len(entradas), len(respuestas)) - 1]

    return motor, entradas


VACIO = SimpleNamespace(txts=None, boxes=None, scores=None)


def hoja(oscuros=None, alto=2339, ancho=1654):
    """Página A4 a 200 dpi como matriz BGR: negra, o blanca con `oscuros` píxeles negros."""
    if oscuros is None:
        return np.zeros((alto, ancho, 3), np.uint8)
    matriz = np.full((alto, ancho, 3), 255, np.uint8)
    matriz.reshape(-1, 3)[:oscuros] = 0
    return matriz


def test_f33_sube_la_version_de_la_lectura():
    assert calidad_ocr.VERSION == 3


def test_motor_usa_reserva_de_memoria(monkeypatch, tmp_path):
    import hashlib

    import rapidocr

    archivos = {}
    for nombre in extraccion._OCR_FILES:
        (tmp_path / nombre).write_bytes(nombre.encode())
        archivos[nombre] = hashlib.sha256(nombre.encode()).hexdigest()
    parametros = {}
    monkeypatch.setattr(extraccion, "OCR_MODELS", tmp_path)
    monkeypatch.setattr(extraccion, "_OCR_FILES", archivos)
    monkeypatch.setattr(rapidocr, "RapidOCR", lambda params: parametros.update(params))
    extraccion._ocr.cache_clear()
    try:
        extraccion._ocr()
    finally:
        extraccion._ocr.cache_clear()
    assert parametros["EngineConfig.onnxruntime.enable_cpu_mem_arena"] is True


def test_pdf_escaneado_llega_al_motor_como_matriz_bgr(tmp_path, monkeypatch):
    ruta = tmp_path / "escaneo.pdf"
    with pymupdf.open() as doc:
        pagina = doc.new_page()
        pagina.draw_rect(pagina.rect, color=(1, 0, 0), fill=(1, 0, 0))
        doc.save(ruta)
    motor, entradas = secuencia(resultado())
    monkeypatch.setattr(extraccion, "_ocr", lambda: motor)
    extraccion._pdf_informe(ruta)
    assert isinstance(entradas[0], np.ndarray)
    assert entradas[0].ndim == 3 and entradas[0].shape[2] == 3
    assert entradas[0][50, 50].tolist() == [0, 0, 255]  # rojo en orden BGR


def test_giros_tambien_llegan_como_matriz(monkeypatch):
    motor, entradas = secuencia(VACIO, resultado())
    monkeypatch.setattr(extraccion, "_ocr", lambda: motor)
    extraccion.ocr_informe(hoja())
    assert len(entradas) == 2
    assert all(isinstance(e, np.ndarray) for e in entradas)


def test_horizontal_cuenta_cajas_mas_anchas_que_altas():
    assert calidad_ocr.horizontal(calidad_ocr.resumir(resultado())) == 1
    assert calidad_ocr.horizontal(calidad_ocr.resumir(vertical())) == 0
    assert calidad_ocr.horizontal(calidad_ocr.resumir(VACIO)) == 0


def test_lectura_vacia_no_vuelve_divergente_al_primer_giro_legible(monkeypatch):
    motor, entradas = secuencia(VACIO, resultado())
    monkeypatch.setattr(extraccion, "_ocr", lambda: motor)
    informe = extraccion.ocr_informe(hoja())
    assert len(entradas) == 2
    assert informe["intentos"] == 2
    assert informe["transformacion"]["giro"] == 180
    assert "lecturas_divergentes" not in informe["motivos"]
    assert not informe["requiere_revision"]


def test_ante_empate_gana_el_giro_con_lineas_horizontales(monkeypatch):
    motor, _ = secuencia(VACIO, vertical(), VACIO, resultado())
    monkeypatch.setattr(extraccion, "_ocr", lambda: motor)
    informe = extraccion.ocr_informe(hoja())
    assert informe["transformacion"]["giro"] == 270
    assert informe["texto"].splitlines() == [
        "DNI: 90000001",
        "ALBA ZURBELIA LUMARIA",
        "IMPORTE: 12345.67",
    ]


def test_lecturas_extensas_con_numeros_distintos_siguen_divergentes(monkeypatch):
    otra = resultado()
    otra.txts = ["DNI: 90000007", "ALBA ZURBELIA LUMARIA", "IMPORTE: 12345.69"]
    motor, _ = secuencia(resultado(score=0.5), otra)
    monkeypatch.setattr(extraccion, "_ocr", lambda: motor)
    informe = extraccion.ocr_informe(hoja())
    assert "lecturas_divergentes" in informe["motivos"]
    assert informe["requiere_revision"]


@pytest.mark.parametrize("oscuros", [0, 38])
def test_hoja_totalmente_blanca_no_pasa_por_el_motor(monkeypatch, oscuros):
    motor, entradas = secuencia(resultado())
    monkeypatch.setattr(extraccion, "_ocr", lambda: motor)
    informe = extraccion.ocr_informe(hoja(oscuros))
    assert not entradas
    assert informe["texto"] == ""
    assert informe["intentos"] == 0
    assert informe["motivos"] == ["pagina_casi_vacia"]
    assert informe["requiere_revision"]


def test_hoja_con_una_marca_minima_se_sigue_leyendo(monkeypatch):
    # Un «1» aislado en A4 a 200 dpi ocupa unos 60 píxeles oscuros.
    motor, entradas = secuencia(resultado())
    monkeypatch.setattr(extraccion, "_ocr", lambda: motor)
    extraccion.ocr_informe(hoja(60))
    assert len(entradas) == 1


def _soffice_falso(llamadas, perfiles, codigo=0):
    """LibreOffice simulado: escribe en el perfil recibido y en el destino."""

    def ejecutar(argv, **_kwargs):
        llamadas.append(argv)
        perfil = next(p for p in perfiles if p.as_uri() in argv[1])
        perfil.mkdir(parents=True, exist_ok=True)
        (perfil / "registrymodifications.xcu").write_text("ficticio")
        destino = Path(argv[argv.index("--outdir") + 1])
        (destino / (Path(argv[-1]).stem + ".txt")).write_text("DOCUMENTO FICTICIO")
        return SimpleNamespace(returncode=codigo)

    return ejecutar


def _preparar_soffice(tmp_path, monkeypatch, codigo=0):
    import os

    monkeypatch.setattr(extraccion, "CACHE", tmp_path / "cache")
    monkeypatch.setattr(extraccion, "_PERFILES_SOFFICE", {})
    perfil = extraccion.CACHE / f"libreoffice-{os.getpid()}"
    llamadas = []
    monkeypatch.setattr(
        extraccion.subprocess, "run", _soffice_falso(llamadas, [perfil], codigo)
    )
    rtf = tmp_path / "ficticio.rtf"
    rtf.write_text("{\\rtf1 DOCUMENTO FICTICIO}")
    salida = tmp_path / "salida"
    salida.mkdir()
    return perfil, llamadas, rtf, salida


def test_libreoffice_reutiliza_un_perfil_por_proceso(tmp_path, monkeypatch):
    temporales = tmp_path / "tmp"
    temporales.mkdir()
    monkeypatch.setattr(extraccion.tempfile, "tempdir", str(temporales))
    registrados = []
    monkeypatch.setattr(
        extraccion.atexit, "register", lambda *a, **_k: registrados.append(a)
    )
    perfil, llamadas, rtf, salida = _preparar_soffice(tmp_path, monkeypatch)
    for _ in range(2):
        extraccion._soffice(rtf, "txt", salida)
    assert len(llamadas) == 2
    assert {argv[1] for argv in llamadas} == {
        f"-env:UserInstallation={perfil.as_uri()}"
    }
    assert len(registrados) == 1
    assert not list(temporales.iterdir())


def test_libreoffice_descarta_el_perfil_si_la_conversion_falla(tmp_path, monkeypatch):
    monkeypatch.setattr(extraccion.atexit, "register", lambda *_a, **_k: None)
    perfil, _, rtf, salida = _preparar_soffice(tmp_path, monkeypatch, codigo=1)
    with pytest.raises(ValueError, match="LibreOffice no pudo convertirlo"):
        extraccion._soffice(rtf, "txt", salida)
    assert not perfil.exists()
