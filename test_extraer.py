"""Pruebas de extracción sobre documentos enteramente sintéticos."""

from pathlib import Path
from zipfile import ZipFile

import pymupdf
import pytest

import extraer

BASE = Path(__file__).parent / "tests" / "fixtures"
DNI = BASE / "cliente" / "dni.png"


def test_imagen_y_pdf_escaneado(tmp_path, monkeypatch):
    monkeypatch.setattr(extraer, "CACHE", tmp_path / "cache")
    img = extraer.leer(DNI)
    assert "90000004-1" in img, img[:300]
    assert "NUBELIA" in img, img[:300]
    assert extraer.leer(DNI) == img
    pdf = BASE / "formatos" / "escaneado.pdf"
    with pymupdf.open(pdf) as doc:
        assert not doc[0].get_text().strip()
    assert "90000004-1" in extraer.leer(pdf)


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
            assert "DONACION" not in str(e) and str(tmp_path) not in str(e)
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
    assert "<w:txbxContent>" in xml and "<mc:Fallback>" in xml
    assert xml.count(nota) == 2  # Choice moderno y Fallback VML.
    cuerpo = extraer.leer(ruta)
    assert "<w:" not in cuerpo
    assert cuerpo.count(nota) == 1


def test_pdf_texto_y_tabla_docx():
    texto = extraer.leer(BASE / "formatos" / "texto.pdf")
    assert "DOCUMENTO FICTICIO" in texto and "90000004" in texto
    tabla = extraer.leer(BASE / "formatos" / "tabla.docx")
    assert tabla.splitlines()[:4] == ["DNI", "90000004", "Partida", "80000001"]
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


@pytest.mark.parametrize(
    "nombre,es_directorio", [("ficticio.txt", False), ("ficticio.rtf", True)]
)
def test_legacy_valida_archivo_y_sufijo(tmp_path, monkeypatch, nombre, es_directorio):
    ruta = tmp_path / nombre
    ruta.mkdir() if es_directorio else ruta.write_text("DOCUMENTO FICTICIO")
    monkeypatch.setattr(
        extraer.subprocess, "run", lambda *_args, **_kwargs: pytest.fail("subprocess")
    )
    with pytest.raises(ValueError, match="formato legacy inválido"):
        extraer._legacy(ruta)
