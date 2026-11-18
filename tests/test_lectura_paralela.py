"""F76: motor configurable y lectura de páginas en paralelo. Solo datos ficticios."""

import hashlib
import importlib.metadata
import io
import json

import pymupdf
import pytest
from PIL import Image, ImageDraw, ImageFont

from adaptadores import calidad_ocr, extraccion

PAGINAS = ("UNO", "DOS", "TRES")


@pytest.fixture
def motor_limpio():
    """El motor se guarda por proceso: cada prueba parte sin motor ni grupo."""
    extraccion._ocr.cache_clear()
    extraccion.cerrar_grupo()
    yield
    extraccion._ocr.cache_clear()
    extraccion.cerrar_grupo()


def _hoja(marca):
    imagen = Image.new("RGB", (1654, 2339), "white")
    lapiz = ImageDraw.Draw(imagen)
    fuente = ImageFont.load_default(size=40)
    lineas = [
        f"PAGINA {marca} DEL DOCUMENTO FICTICIO",
        "CLAUSULA PRIMERA DEL CONTRATO DE PRUEBA",
        "EL PRECIO PACTADO ES DE 12345 SOLES",
        "PARTIDA FICTICIA NUMERO 00011122",
    ]
    for i, linea in enumerate(lineas):
        lapiz.text((150, 200 + i * 120), linea, fill="black", font=fuente)
    salida = io.BytesIO()
    imagen.save(salida, "PNG")
    return salida.getvalue()


def _pdf(ruta, hojas, con_texto=()):
    """PDF de hojas escaneadas; `con_texto` son los índices con capa digital."""
    with pymupdf.open() as doc:
        for i, marca in enumerate(hojas):
            pagina = doc.new_page(width=595, height=842)
            if i in con_texto:
                for j in range(8):
                    pagina.insert_text(
                        (72, 100 + j * 30),
                        f"PAGINA {marca} CON TEXTO DIGITAL FICTICIO, LINEA {j}",
                    )
            else:
                pagina.insert_image(pagina.rect, stream=_hoja(marca))
        doc.save(ruta)
    return ruta


def _sin_confianza(informes):
    """Lo que debe coincidir entre motores: texto y avisos, no los decimales.

    Las coordenadas de los recuadros varían en fracciones de píxel entre motores;
    de ahí salen la confianza y la inclinación, que se comparan con tolerancia.
    """
    return [
        {
            k: v
            for k, v in informe.items()
            if k not in ("confianza", "inclinacion", "cajas", "descartadas")
        }
        for informe in informes
    ]


# --- configuración (contrato) ---


def test_valores_por_defecto(monkeypatch):
    for nombre in ("OCR_MOTOR", "OCR_PROCESOS", "OCR_HILOS"):
        monkeypatch.delenv(nombre, raising=False)
    # Sin configurar, se lee como antes de F76.
    assert extraccion.motor() == "onnxruntime"
    assert extraccion.procesos() == 1
    assert extraccion.hilos() == 0
    monkeypatch.setenv("OCR_PROCESOS", "3")
    assert extraccion.hilos() == 1


def test_un_proceso_no_fija_hilos(monkeypatch):
    monkeypatch.setenv("OCR_PROCESOS", "1")
    monkeypatch.delenv("OCR_HILOS", raising=False)
    assert extraccion.hilos() == 0
    monkeypatch.setenv("OCR_HILOS", "4")
    assert extraccion.hilos() == 4


@pytest.mark.parametrize(
    ("nombre", "valor"),
    [
        ("OCR_MOTOR", "tesseract"),
        ("OCR_PROCESOS", "0"),
        ("OCR_PROCESOS", "tres"),
        ("OCR_HILOS", "-1"),
    ],
)
def test_valor_invalido_nombra_la_variable(monkeypatch, nombre, valor):
    monkeypatch.setenv(nombre, valor)
    funcion = {
        "OCR_MOTOR": extraccion.motor,
        "OCR_PROCESOS": extraccion.procesos,
        "OCR_HILOS": extraccion.hilos,
    }[nombre]
    with pytest.raises(ValueError, match=nombre):
        funcion()


# --- identidad de la lectura (FR-005) ---


def test_identidad_con_motor_anterior_no_cambia(monkeypatch):
    monkeypatch.setenv("OCR_MOTOR", "onnxruntime")
    anterior = hashlib.sha256(
        json.dumps(
            {
                "modelos": sorted(extraccion._OCR_FILES.items()),
                "use_cls": extraccion._OCR_USE_CLS,
                "rapidocr": importlib.metadata.version("rapidocr"),
                "formato_texto": extraccion._FORMATO_TEXTO,
                "calidad_ocr": calidad_ocr.VERSION,
                "dpi": extraccion.DPI,
                "formato_cache": extraccion._FORMATO_CACHE,
            },
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    assert extraccion.version_extractor() == anterior


def test_identidad_cambia_con_el_motor_y_no_con_los_procesos(monkeypatch):
    monkeypatch.setenv("OCR_MOTOR", "onnxruntime")
    anterior = extraccion.version_extractor()
    monkeypatch.setenv("OCR_MOTOR", "openvino")
    nueva = extraccion.version_extractor()
    assert nueva != anterior
    monkeypatch.setenv("OCR_PROCESOS", "5")
    monkeypatch.setenv("OCR_HILOS", "2")
    assert extraccion.version_extractor() == nueva
    monkeypatch.setattr(
        importlib.metadata,
        "version",
        lambda nombre: "0.0.0-ficticia",
    )
    assert extraccion.version_extractor() != nueva


def test_motor_openvino_recibe_sus_parametros(monkeypatch, tmp_path):
    import rapidocr

    archivos = {}
    for nombre in extraccion._OCR_FILES:
        (tmp_path / nombre).write_bytes(nombre.encode())
        archivos[nombre] = hashlib.sha256(nombre.encode()).hexdigest()
    parametros = {}
    monkeypatch.setattr(extraccion, "OCR_MODELS", tmp_path)
    monkeypatch.setattr(extraccion, "_OCR_FILES", archivos)
    monkeypatch.setattr(rapidocr, "RapidOCR", lambda params: parametros.update(params))
    monkeypatch.setenv("OCR_MOTOR", "openvino")
    monkeypatch.setenv("OCR_PROCESOS", "3")
    monkeypatch.delenv("OCR_HILOS", raising=False)
    extraccion._ocr.cache_clear()
    try:
        extraccion._ocr()
    finally:
        extraccion._ocr.cache_clear()
    assert parametros["Det.engine_type"] == rapidocr.EngineType.OPENVINO
    assert parametros["Rec.engine_type"] == rapidocr.EngineType.OPENVINO
    assert parametros["EngineConfig.openvino.inference_num_threads"] == 1
    assert "EngineConfig.onnxruntime.enable_cpu_mem_arena" not in parametros


# --- lectura en paralelo (FR-001 a FR-003) ---


def test_paralelo_igual_que_en_serie(monkeypatch, tmp_path, motor_limpio):
    ruta = _pdf(tmp_path / "escaneo.pdf", PAGINAS)
    monkeypatch.setenv("OCR_MOTOR", "onnxruntime")
    monkeypatch.setenv("OCR_PROCESOS", "1")
    serie = extraccion._pdf_informe(ruta)
    monkeypatch.setenv("OCR_PROCESOS", "2")
    paralelo = extraccion._pdf_informe(ruta)
    assert paralelo == serie
    for marca, pagina in zip(PAGINAS, serie):
        assert f"PAGINA {marca}" in pagina["texto"]


def test_openvino_da_el_mismo_texto_y_los_mismos_avisos(
    monkeypatch, tmp_path, motor_limpio
):
    ruta = _pdf(tmp_path / "escaneo.pdf", PAGINAS[:2])
    monkeypatch.setenv("OCR_PROCESOS", "1")
    monkeypatch.setenv("OCR_MOTOR", "onnxruntime")
    actual = extraccion._pdf_informe(ruta)
    extraccion._ocr.cache_clear()
    monkeypatch.setenv("OCR_MOTOR", "openvino")
    nuevo = extraccion._pdf_informe(ruta)
    assert _sin_confianza(nuevo) == _sin_confianza(actual)
    for i, (a, n) in enumerate(zip(actual, nuevo), 1):
        assert n["inclinacion"] == pytest.approx(a["inclinacion"], abs=0.5)
        assert n["confianza"] == pytest.approx(a["confianza"], abs=0.005), (
            f"página {i}: la confianza cambia de {a['confianza']} a {n['confianza']}"
        )


def test_paginas_digitales_y_escaneadas_conservan_el_orden(
    monkeypatch, tmp_path, motor_limpio
):
    ruta = _pdf(tmp_path / "mixto.pdf", PAGINAS, con_texto=(1,))
    monkeypatch.setenv("OCR_MOTOR", "onnxruntime")
    monkeypatch.setenv("OCR_PROCESOS", "2")
    informes = extraccion._pdf_informe(ruta)
    assert [i["metodo"] for i in informes] == ["ocr", "texto_pdf", "ocr"]
    for marca, pagina in zip(PAGINAS, informes):
        assert f"PAGINA {marca}" in pagina["texto"]


def _falla(*_):
    raise RuntimeError("fallo ficticio")


def test_fallo_de_una_pagina_se_propaga(monkeypatch, tmp_path, motor_limpio):
    ruta = _pdf(tmp_path / "escaneo.pdf", PAGINAS[:2])
    monkeypatch.setenv("OCR_MOTOR", "onnxruntime")
    monkeypatch.setenv("OCR_PROCESOS", "2")
    monkeypatch.setattr(extraccion, "_leer_pagina_pdf", _falla)
    with pytest.raises(RuntimeError):
        extraccion._pdf_informe(ruta)


def test_imagen_suelta_va_a_un_proceso_de_lectura(monkeypatch, tmp_path, motor_limpio):
    ruta = tmp_path / "hoja.png"
    ruta.write_bytes(_hoja("UNICA"))
    monkeypatch.setattr(extraccion, "CACHE", tmp_path / "cache")
    monkeypatch.setenv("OCR_MOTOR", "onnxruntime")
    monkeypatch.setenv("OCR_PROCESOS", "2")
    assert "PAGINA UNICA" in extraccion.leer(ruta)
    # Este proceso no cargó otra copia del motor.
    assert extraccion._ocr.cache_info().currsize == 0


def test_comprobar_motor_acepta_la_configuracion_instalada(monkeypatch):
    for nombre in ("onnxruntime", "openvino"):
        monkeypatch.setenv("OCR_MOTOR", nombre)
        extraccion.comprobar_motor()


def test_comprobar_motor_avisa_si_no_esta_instalado(monkeypatch):
    import importlib.util

    monkeypatch.setenv("OCR_MOTOR", "openvino")
    monkeypatch.setattr(importlib.util, "find_spec", lambda _: None)
    with pytest.raises(RuntimeError, match="OCR_MOTOR=openvino"):
        extraccion.comprobar_motor()


def test_comprobar_motor_avisa_si_falta_un_modelo(monkeypatch, tmp_path):
    monkeypatch.setattr(extraccion, "OCR_MODELS", tmp_path)
    with pytest.raises(RuntimeError, match="Recurso OCR"):
        extraccion.comprobar_motor()


def test_comprobar_motor_rechaza_valores_invalidos(monkeypatch):
    monkeypatch.setenv("OCR_PROCESOS", "muchos")
    with pytest.raises(ValueError, match="OCR_PROCESOS"):
        extraccion.comprobar_motor()
