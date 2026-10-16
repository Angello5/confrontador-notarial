"""F32: del borrador .docx a páginas dibujadas y segmentos con posición (ficticio)."""

import shutil
import zipfile

import pytest

from adaptadores import extraccion, paginas
from nucleo import correccion

pytestmark = pytest.mark.skipif(
    shutil.which(extraccion.SOFFICE) is None, reason="requiere LibreOffice (soffice)"
)

_W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def _run(texto, negrita=False):
    estilo = "<w:rPr><w:b/></w:rPr>" if negrita else ""
    return f'<w:r>{estilo}<w:t xml:space="preserve">{texto}</w:t></w:r>'


def docx_valido(ruta, parrafos):
    """Un .docx mínimo que LibreOffice abre; ``None`` es un salto de página y
    una tupla, tramos ``(texto, negrita)`` de un párrafo justificado."""
    cuerpo = "".join(
        '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
        if p is None
        else '<w:p><w:pPr><w:jc w:val="both"/></w:pPr>'
        + "".join(_run(*tramo) for tramo in p)
        + "</w:p>"
        if isinstance(p, tuple)
        else f"<w:p>{_run(p)}</w:p>"
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
    for texto, x0, y0, x1, y1, _linea, bordes in paginas.segmentos(pdf, 2):
        assert 0 <= x0 < x1 <= 1
        assert 0 <= y0 < y1 <= 1
        assert len(bordes) == len(texto) + 1
        assert list(bordes) == sorted(bordes)
        assert (bordes[0], bordes[-1]) == (x0, x1)


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


def test_el_recuadro_abarca_la_palabra_entera_en_negrita_y_normal(tmp_path):
    """F52: nombre y DNI en negrita seguidos de una coma normal (más estrecha)."""
    import pymupdf

    original = docx_valido(
        tmp_path / "original.docx",
        [
            (
                ("COMPARECE: ", False),
                ("ALBA ZURBELIA LUNARIA", True),
                (", IDENTIFICADA CON DNI ", False),
                ("90000002", True),
                (
                    ", DE ESTADO CIVIL CASADA, QUIEN INTERVIENE POR SER BIEN PROPIO.",
                    False,
                ),
            ),
        ],
    )
    pdf = paginas.a_pdf(original, tmp_path / "vista.pdf")
    segmentos = paginas.segmentos(pdf, 1)
    with pymupdf.open(pdf) as doc:
        pagina = doc[0]
        ancho = pagina.rect.width
        for valor, ultima in (
            ("ALBA ZURBELIA LUNARIA", "LUNARIA"),
            ("90000002", "90000002"),
        ):
            (real,) = pagina.search_for(ultima)
            borde = max(r["x1"] for r in correccion.marcas(segmentos, valor))
            # Medio punto de tolerancia: el ancho de una letra ronda los 7.
            assert borde * ancho == pytest.approx(real.x1, abs=0.5), valor
