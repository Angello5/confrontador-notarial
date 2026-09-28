"""Pruebas de extracción sobre documentos enteramente sintéticos."""

from pathlib import Path
from difflib import SequenceMatcher
from zipfile import ZipFile

import pymupdf
import pytest
from PIL import Image, ImageDraw, ImageFont

from adaptadores import extraccion as extraer

BASE = Path(__file__).parent / "tests" / "fixtures"
DNI = BASE / "cliente" / "dni.png"


def test_imagen_y_pdf_escaneado(tmp_path, monkeypatch):
    from adaptadores import extraccion

    monkeypatch.setattr(extraccion, "CACHE", tmp_path / "cache")
    img = extraer.leer(DNI)
    assert "90000004-1" in img, img[:300]
    assert "NUBELIA" in img, img[:300]
    assert extraer.leer(DNI) == img
    pdf = BASE / "formatos" / "escaneado.pdf"
    with pymupdf.open(pdf) as doc:
        assert not doc[0].get_text().strip()
    assert "90000004-1" in extraer.leer(pdf)


def test_ocr_lineas_conserva_orden_acentos_y_eñe(monkeypatch):
    from types import SimpleNamespace

    cajas = [
        ([[30, 10], [70, 10], [70, 20], [30, 20]], "ÑANDÚ"),
        ([[0, 10], [25, 10], [25, 20], [0, 20]], "LÍNEA"),
        ([[0, 35], [45, 35], [45, 45], [0, 45]], "ACCIÓN"),
    ]
    ocr = SimpleNamespace(
        txts=[texto for _, texto in cajas], boxes=[caja for caja, _ in cajas]
    )
    monkeypatch.setattr(extraer, "_ocr", lambda: lambda _fuente: ocr)

    assert extraer.ocr_lineas(b"imagen sintetica") == "LÍNEA  ÑANDÚ\nACCIÓN"


def test_ocr_requiere_recursos_fijados_sin_descarga(monkeypatch, tmp_path):
    from adaptadores import extraccion

    extraccion._ocr.cache_clear()
    monkeypatch.setattr(extraccion, "OCR_MODELS", tmp_path)
    for name in extraccion._OCR_FILES:
        (tmp_path / name).write_bytes(b"modelo ficticio invalido")
    with pytest.raises(RuntimeError, match="ch_PP-OCRv5_mobile_det.onnx"):
        extraccion._ocr()


def test_cache_ocr_se_invalida_si_cambia_modelo(monkeypatch, tmp_path):
    from adaptadores import extraccion

    monkeypatch.setattr(extraccion, "CACHE", tmp_path)
    monkeypatch.setattr(extraccion, "_OCR_FILES", {"det": "sha-v4"})
    assert extraccion._cacheado(b"documento ficticio", lambda: "OCR v4") == "OCR v4"
    monkeypatch.setattr(extraccion, "_OCR_FILES", {"det": "sha-v5"})
    assert extraccion._cacheado(b"documento ficticio", lambda: "OCR v5") == "OCR v5"


def test_ocr_predeterminado_alcanza_piso_sintetico_v5():
    lineas = [
        "En Lima, los otorgantes declaran válida la unión y la cesión del inmueble.",
        "La señora Ángela Núñez y el señor José Muñoz acuerdan la transmisión.",
        "El cónyuge manifiesta que recibió información íntegra, clara y verídica.",
        "Partida registral ficticia número 80000001, asiento cinco, sección Ñ.",
        "Documento nacional ficticio DNI 90000004, emitido el día miércoles.",
        "El precio pactado asciende a S/. 150,000.75 (ciento cincuenta mil soles).",
        "Quedó leído, ratificado y firmado; también consta la cláusula de garantía.",
        "ÚLTIMA DISPOSICIÓN: habrá revisión, aprobación y anotación en el registro.",
    ]
    font_path = Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf")
    if not font_path.is_file():
        pytest.skip("requiere fonts-liberation (instalado en CI)")
    font = ImageFont.truetype(str(font_path), 50)
    image = Image.new("RGB", (2480, 3508), "white")
    draw = ImageDraw.Draw(image)
    for index, line in enumerate(lineas):
        draw.text((150, (220 + index * 210) * 1.5), line, fill="black", font=font)
    output = extraer._ocr()(image)
    raw = " ".join(output.txts or [])
    texto = " ".join(lineas)
    expected_words, actual_words = texto.casefold().split(), raw.casefold().split()
    words = sum(
        size
        for _, _, size in SequenceMatcher(
            a=expected_words, b=actual_words, autojunk=False
        ).get_matching_blocks()
    )
    special = set("áéíóúüñÁÉÍÓÚÜÑ")
    matcher = SequenceMatcher(a=texto, b=raw, autojunk=False)
    diacritics = sum(
        1
        for a, _, size in matcher.get_matching_blocks()
        for c in texto[a : a + size]
        if c in special
    )
    ys = sorted(sum(point[1] for point in box) / len(box) for box in output.boxes)
    lines = []
    for y in ys:
        if not lines or y - lines[-1][-1] > 97.5:
            lines.append([y])
        else:
            lines[-1].append(y)
    assert len(lines) == 8
    assert words >= 82 and diacritics >= 31


def test_legacy(tmp_path, monkeypatch):
    monkeypatch.setattr(extraer.sys, "platform", "linux")
    monkeypatch.setattr(extraer.tempfile, "tempdir", str(tmp_path))
    rtf = BASE / "formatos" / "minuta.rtf"
    doc = extraer._soffice(rtf, "doc", tmp_path).rename(tmp_path / "minuta.doc")
    assert doc.read_bytes()[:4] == b"\xd0\xcf\x11\xe0"
    texto_doc = extraer.leer(doc)
    assert "DONACION DE ACCIONES Y DERECHOS" in texto_doc, texto_doc
    assert "70001" in texto_doc, texto_doc
    assert extraer.leer(rtf).strip().startswith("DONACION"), extraer.leer(rtf)
    assert sorted(x.name for x in tmp_path.iterdir()) == [
        "minuta.doc"
    ]  # sin temporales


def test_legacy_sin_libreoffice(tmp_path, monkeypatch):
    monkeypatch.setattr(extraer.sys, "platform", "linux")
    monkeypatch.setattr(extraer.tempfile, "tempdir", str(tmp_path))
    rtf = BASE / "formatos" / "minuta.rtf"
    for exe in ["no-existe-soffice", "false"]:  # ausente y fallo del ejecutable
        monkeypatch.setattr(extraer, "SOFFICE", exe)
        try:
            extraer.leer(rtf)
        except ValueError as e:
            assert "DONACION" not in str(e)
            assert str(tmp_path) not in str(e)
        else:
            raise AssertionError(exe)
    assert not list(tmp_path.iterdir())


def test_xlsx():
    assert extraer.leer(BASE / "formatos" / "datos.xlsx").splitlines() == [
        "DNI  90000004",
        "Partida  80000001",
    ]


def test_cuadro_texto_docx():
    ruta = BASE / "borrador" / "observado.docx"
    nota = "NOTA DE PRUEBA: CONSTACIA DEL DOCUMENTO (3)"
    with ZipFile(ruta) as z:
        xml = z.read("word/document.xml").decode()
    assert "<w:txbxContent>" in xml
    assert "<mc:Fallback>" in xml
    assert xml.count(nota) == 2  # Choice moderno y Fallback VML.
    cuerpo = extraer.leer(ruta)
    assert "<w:" not in cuerpo
    assert cuerpo.count(nota) == 1


def test_pdf_texto_y_tabla_docx(monkeypatch, tmp_path):
    monkeypatch.setattr(extraer, "CACHE", tmp_path / "cache")
    texto = extraer.leer(BASE / "formatos" / "texto.pdf")
    assert "DOCUMENTO FICTICIO" in texto
    assert "90000004" in texto
    tabla = extraer.leer(BASE / "formatos" / "tabla.docx")
    # F27: cada fila de tabla es una linea con sus celdas separadas por dos espacios
    assert tabla.splitlines()[:2] == ["DNI  90000004", "Partida  80000001"]
    assert "CAMPO  VALOR" in tabla


def test_legacy_macos_ejecutable_y_ruta_absolutos(tmp_path, monkeypatch):
    from types import SimpleNamespace

    ruta = tmp_path / "-ficticio.rtf"
    ruta.write_text("{\\rtf1 DOCUMENTO FICTICIO}")
    monkeypatch.chdir(tmp_path)

    def ejecutar(argv, **kwargs):
        assert argv == [
            "/usr/bin/textutil",
            "-convert",
            "txt",
            "-stdout",
            str(ruta.resolve()),
        ]
        assert kwargs == {"capture_output": True, "text": True}
        return SimpleNamespace(returncode=0, stdout="CAMPO\tVALOR")

    monkeypatch.setattr(extraer.sys, "platform", "darwin")
    monkeypatch.setattr(extraer.subprocess, "run", ejecutar)
    assert extraer.leer(Path(ruta.name)) == "CAMPO  VALOR"


def test_leer_conserva_sufijo_del_enlace(tmp_path, monkeypatch):
    destino = tmp_path / "documento-ficticio.bin"
    destino.write_text("DOCUMENTO FICTICIO")
    enlace = tmp_path / "documento-ficticio.rtf"
    enlace.symlink_to(destino)
    monkeypatch.setattr(extraer, "_legacy", lambda ruta: f"legacy:{ruta.name}")
    assert extraer.leer(enlace) == f"legacy:{destino.name}"


@pytest.mark.parametrize(
    "nombre,es_directorio",
    [("ficticio.txt", False), ("ficticio.rtf", True), ("inexistente.rtf", None)],
)
def test_legacy_valida_archivo_y_sufijo(tmp_path, monkeypatch, nombre, es_directorio):
    ruta = tmp_path / nombre
    if es_directorio is not None:
        ruta.mkdir() if es_directorio else ruta.write_text("DOCUMENTO FICTICIO")
    monkeypatch.setattr(
        extraer.subprocess, "run", lambda *_args, **_kwargs: pytest.fail("subprocess")
    )
    with pytest.raises(ValueError, match="formato legacy inválido"):
        extraer._legacy(ruta)
