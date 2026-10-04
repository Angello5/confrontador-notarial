"""F32: del borrador .docx a páginas dibujadas y segmentos con posición (ficticio)."""

import shutil
import zipfile

import pytest

from adaptadores import extraccion, paginas

pytestmark = pytest.mark.skipif(
    shutil.which(extraccion.SOFFICE) is None, reason="requiere LibreOffice (soffice)"
)

_W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def docx_valido(ruta, parrafos):
    """Un .docx mínimo que LibreOffice abre; ``None`` es un salto de página."""
    cuerpo = "".join(
        '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
        if p is None
        else f'<w:p><w:r><w:t xml:space="preserve">{p}</w:t></w:r></w:p>'
        for p in parrafos
    )
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/'
            'vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>",
        )
        z.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/'
            '2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>",
        )
        z.writestr(
            "word/document.xml",
            f'<?xml version="1.0" encoding="UTF-8"?><w:document {_W}><w:body>'
            f"{cuerpo}</w:body></w:document>",
        )
    return ruta


@pytest.fixture(scope="module")
def pdf(tmp_path_factory):
    carpeta = tmp_path_factory.mktemp("vista")
    original = docx_valido(
        carpeta / "original.docx",
        [
            "OPERACION FICTICIA DE PRUEBA.",
            None,
            "ALBA ZURBELIA LUNARIA, IDENTIFICADA CON DNI 90000002.",
        ],
    )
    return paginas.a_pdf(original, carpeta / "vista.pdf")


def test_a_pdf_produce_dos_paginas(pdf):
    assert pdf.is_file()
    assert [p["numero"] for p in paginas.paginas(pdf)] == [1, 2]
    assert all(p["proporcion"] > 1 for p in paginas.paginas(pdf))


def test_segmentos_traen_el_texto_en_su_pagina(pdf):
    textos = [s[0] for s in paginas.segmentos(pdf, 2)]
    assert "90000002." in textos
    assert "90000002." not in [s[0] for s in paginas.segmentos(pdf, 1)]
    for _texto, x0, y0, x1, y1, _linea in paginas.segmentos(pdf, 2):
        assert 0 <= x0 < x1 <= 1
        assert 0 <= y0 < y1 <= 1


def test_png_de_la_pagina(pdf):
    assert paginas.png(pdf, 1).startswith(b"\x89PNG\r\n\x1a\n")


def test_pagina_fuera_de_rango(pdf):
    with pytest.raises(IndexError):
        paginas.png(pdf, 3)
    with pytest.raises(IndexError):
        paginas.segmentos(pdf, 0)


def test_a_pdf_sin_rutas_en_el_error(tmp_path):
    with pytest.raises(ValueError) as error:
        paginas.a_pdf(tmp_path / "ausente.docx", tmp_path / "salida.pdf")
    assert str(tmp_path) not in str(error.value)
