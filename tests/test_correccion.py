"""F21: capa de corrección y documento corregido con datos ficticios."""

import hashlib
import re
import zipfile
from collections import Counter
from html import unescape

import pytest

SALIDAS = [
    "[DNI] «90000002» debe decir «90000001»   …ALBA, DNI 90000002",
    "[NOMBRE] «ALBA ZURBELIA LUNARIA» debe decir «ALBA ZURBELIA LUMARIA»",
    "[NOMBRE] «CIRO VALDANO» debe decir «CIRO VALDANO»",
    "[NOMBRE] «BRUNO CASTELO RIVAS» debe decir «BRUNO CASTELO»",
    "[DNI] «9000001» no coincide con ninguna fuente   …DNI 9000001",
    "[NOMBRE] FALTA: «DORA QUINTEL» esta en las fuentes y no aparece en el destino",
    "[NUMERO_EN_LETRAS] «MIL QUINIENTOS (1,600.00)» debe decir «1,600.00»",
    "[PARTIDA] «80000009» debe decir «80000077»",
    "[PARRAFO] falta o alterado (70.0%): CLAUSULA FICTICIA",
    "[NOMBRE] «ELIO RAMOS» debe decir «ELIO RAMIS»   (caratula)",
]
FUENTES = {
    "minuta-ficticia.docx": "LA MINUTA DE ALBA ZURBELIA LUMARIA Y ELIO RAMIS.",
    "reniec-ficticio.pdf": "PAGINA SIN DATOS\fDNI N° 90000001\nALBA ZURBELIA LUMARIA",
}


def test_carga_util_solo_con_correcto_distinto_y_fuente():
    from nucleo.correccion import correcciones

    carga = correcciones(SALIDAS, FUENTES)

    assert [(c["campo"], c["erroneo"], c["correcto"]) for c in carga] == [
        ("DNI", "90000002", "90000001"),
        ("NOMBRE", "ALBA ZURBELIA LUNARIA", "ALBA ZURBELIA LUMARIA"),
        ("NOMBRE", "ELIO RAMOS", "ELIO RAMIS"),
    ]
    assert carga[0]["fuente"] == {"archivo": "reniec-ficticio.pdf", "pagina": 2}
    assert carga[1]["fuente"] == {"archivo": "minuta-ficticia.docx", "pagina": 1}
    assert all("ocurrencia" not in c for c in carga)
    assert all(c["correcto"] != c["erroneo"] for c in carga)  # P-03


def test_ids_estables_y_un_par_repetido_es_una_sola_fila():
    from nucleo.correccion import correcciones

    salidas = [
        "[DNI] «90000002» debe decir «90000001»   …uno",
        "[DNI] «90000002» debe decir «90000001»   …dos",
        "[DNI] «90000002» debe decir «90000003»   …otro valor",
    ]
    carga = correcciones(salidas, {"f.pdf": "DNI 90000001 Y DNI 90000003"})
    assert [(c["erroneo"], c["correcto"]) for c in carga] == [
        ("90000002", "90000001"),
        ("90000002", "90000003"),
    ]
    assert len({c["id"] for c in carga}) == 2
    assert carga == correcciones(salidas, {"f.pdf": "DNI 90000001 Y DNI 90000003"})
    assert all(re.fullmatch(r"[0-9a-f]{12}", c["id"]) for c in carga)


def test_prefijo_y_tildes_se_descartan():
    from nucleo.correccion import correcciones

    salidas = [
        "[NOMBRE] «ALBA ZURBELIA LUMARIAS» debe decir «ALBA ZURBELIA LUMARIA»",
        "[NOMBRE] «ALBA ZURBELIA LUMARÍA» debe decir «ALBA ZURBELIA LUMARIA»",
    ]
    assert correcciones(salidas, FUENTES) == []


def test_coincidencias_con_limites_de_palabra_sin_tildes_ni_mayusculas():
    from nucleo.correccion import coincidencias

    texto = "Sr. José  Péres y JOSEPERES; 190000002 y 90000002."
    assert [texto[i:j] for i, j in coincidencias(texto, "JOSE PERES")] == [
        "José  Péres"
    ]
    assert [texto[i:j] for i, j in coincidencias(texto, "90000002")] == ["90000002"]
    assert coincidencias(texto, "") == []


# --- adaptador .docx -------------------------------------------------------

_W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def crear_docx(ruta, cuerpo):
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/'
            'package/2006/content-types"/>',
        )
        z.writestr(
            "word/document.xml",
            f'<?xml version="1.0"?><w:document {_W}><w:body>{cuerpo}</w:body></w:document>',
        )
        z.writestr("word/styles.xml", "<estilos-ficticios/>")
    return ruta


def _xml(ruta):
    with zipfile.ZipFile(ruta) as z:
        return z.read("word/document.xml").decode()


def _palabras(ruta):
    xml = _xml(ruta)
    return Counter(
        palabra
        for parrafo in xml.split("</w:p>")
        for palabra in re.findall(
            r"\w+",
            unescape("".join(re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", parrafo))),
        )
    )


CUERPO = (
    "<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>ALBA ZURBELIA LU</w:t></w:r>"
    "<w:r><w:t>NARIA</w:t></w:r>"
    '<w:r><w:t xml:space="preserve">, DE NACIONALIDAD PERUANA, DNI 90000002.</w:t></w:r></w:p>'
    "<w:p><w:r><w:t>TESTIGO CON DNI 90000002 Y A &amp; B</w:t></w:r></w:p>"
)


def _correccion(id_, erroneo, correcto):
    return {
        "id": id_,
        "campo": "X",
        "erroneo": erroneo,
        "correcto": correcto,
        "fuente": {"archivo": "minuta-ficticia.docx", "pagina": 1},
    }


def test_aplicar_todas_las_apariciones_y_nada_mas(tmp_path):
    from adaptadores.docx_corregido import aplicar

    original = crear_docx(tmp_path / "borrador.docx", CUERPO)
    antes = original.read_bytes()
    destino = tmp_path / "borrador-corregido.docx"
    carga = [
        _correccion("nombre", "ALBA ZURBELIA LUNARIA", "ALBA ZURBELIA LUMARIA"),
        _correccion("dni", "90000002", "90000001"),
        _correccion("inexistente", "90000009", "90000001"),
    ]

    aplicadas, no_aplicadas = aplicar(original, destino, carga)

    assert aplicadas == {"nombre": 1, "dni": 2}
    assert no_aplicadas == ["inexistente"]
    assert original.read_bytes() == antes
    esperado = (
        CUERPO.replace(
            "<w:t>ALBA ZURBELIA LU</w:t>",
            '<w:t xml:space="preserve">ALBA ZURBELIA LUMARIA</w:t>',
        )
        .replace("<w:t>NARIA</w:t>", '<w:t xml:space="preserve"></w:t>')
        .replace(
            '<w:t xml:space="preserve">, DE NACIONALIDAD PERUANA, DNI 90000002.</w:t>',
            '<w:t xml:space="preserve">, DE NACIONALIDAD PERUANA, DNI 90000001.</w:t>',
        )
        .replace(
            "<w:t>TESTIGO CON DNI 90000002 Y A &amp; B</w:t>",
            '<w:t xml:space="preserve">TESTIGO CON DNI 90000001 Y A &amp; B</w:t>',
        )
    )
    assert _xml(destino) == _xml(original).replace(CUERPO, esperado)
    with zipfile.ZipFile(original) as a, zipfile.ZipFile(destino) as b:
        assert a.namelist() == b.namelist()
        assert a.read("word/styles.xml") == b.read("word/styles.xml")


def test_p04_solo_cambian_las_palabras_corregidas(tmp_path):
    from adaptadores.docx_corregido import aplicar

    original = crear_docx(tmp_path / "borrador.docx", CUERPO)
    destino = tmp_path / "corregido.docx"
    aplicar(
        original,
        destino,
        [
            _correccion("nombre", "ALBA ZURBELIA LUNARIA", "ALBA ZURBELIA LUMARIA"),
            _correccion("dni", "90000002", "90000001"),
        ],
    )
    antes, despues = _palabras(original), _palabras(destino)
    assert antes - despues == Counter({"LUNARIA": 1, "90000002": 2})
    assert despues - antes == Counter({"LUMARIA": 1, "90000001": 2})
    assert sum(antes.values()) == sum(despues.values())


def test_correcciones_en_competencia_no_se_aplican_en_ese_tramo(tmp_path):
    from adaptadores.docx_corregido import aplicar

    original = crear_docx(tmp_path / "borrador.docx", CUERPO)
    aplicadas, no_aplicadas = aplicar(
        original,
        tmp_path / "c.docx",
        [
            _correccion("uno", "ALBA ZURBELIA LUNARIA", "ALBA ZURBELIA LUMARIA"),
            _correccion("dos", "ZURBELIA LUNARIA", "ZURBELIA LUMARIA"),
            _correccion("dni", "90000002", "90000001"),
        ],
    )
    assert (aplicadas, no_aplicadas) == ({"dni": 2}, ["uno", "dos"])
    assert "ALBA ZURBELIA LU" in _xml(tmp_path / "c.docx")


def test_correccion_aplicada_en_un_tramo_y_en_competencia_en_otro(tmp_path):
    from adaptadores.docx_corregido import aplicar

    cuerpo = (
        "<w:p><w:r><w:t>DNI 90000002 DE ELIO RAMOS</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>ELIO RAMOS FIRMA</w:t></w:r></w:p>"
    )
    original = crear_docx(tmp_path / "b.docx", cuerpo)
    aplicadas, no_aplicadas = aplicar(
        original,
        tmp_path / "c.docx",
        [
            _correccion("nombre", "ELIO RAMOS", "ELIO RAMIS"),
            _correccion("dni", "90000002 DE ELIO", "90000001 DE ELIO"),
        ],
    )
    assert (aplicadas, no_aplicadas) == ({"nombre": 1}, ["nombre", "dni"])
    assert "DNI 90000002 DE ELIO RAMOS" in _xml(tmp_path / "c.docx")
    assert "ELIO RAMIS FIRMA" in _xml(tmp_path / "c.docx")


def test_sin_correcciones_el_corregido_es_copia_del_texto(tmp_path):
    from adaptadores.docx_corregido import aplicar

    original = crear_docx(tmp_path / "borrador.docx", CUERPO)
    destino = tmp_path / "c.docx"
    assert aplicar(original, destino, []) == ({}, [])
    assert _xml(destino) == _xml(original)
    assert hashlib.sha256(original.read_bytes()).hexdigest()


@pytest.mark.parametrize("cuerpo", ["<w:p><w:r><w:t>SIN DATOS</w:t></w:r></w:p>"])
def test_erroneo_ausente_queda_no_aplicado(tmp_path, cuerpo):
    from adaptadores.docx_corregido import aplicar

    original = crear_docx(tmp_path / "b.docx", cuerpo)
    assert aplicar(
        original, tmp_path / "c.docx", [_correccion("x", "90000002", "90000001")]
    ) == ({}, ["x"])


def test_enie_descompuesta_y_destino_distinto(tmp_path):
    from adaptadores.docx_corregido import aplicar
    from nucleo.correccion import coincidencias

    assert coincidencias("SR. MUÑOZ", "MUÑOZ") == [(4, 10)]
    original = crear_docx(tmp_path / "b.docx", CUERPO)
    with pytest.raises(ValueError):
        aplicar(original, original, [])


def test_erroneo_repetido_tres_veces_se_corrige_las_tres(tmp_path):
    from adaptadores.docx_corregido import aplicar, apariciones

    cuerpo = (
        "<w:p><w:r><w:t>COMPARECE NILO FERRANTE ORBEGAL, CON DNI 90000021.</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>EL SENOR NILO </w:t></w:r><w:r><w:t>FERRANTE ORBEGAL VENDE.</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>FIRMA NILO FERRANTE ORBEGAL; TESTIGO NILO FERRANTE.</w:t></w:r></w:p>"
    )
    original = crear_docx(tmp_path / "b.docx", cuerpo)
    destino = tmp_path / "c.docx"
    carga = [_correccion("nombre", "NILO FERRANTE ORBEGAL", "NILO FERRANTE ORBEGAR")]

    assert apariciones(original, carga) == {"nombre": 3}
    assert aplicar(original, destino, carga) == ({"nombre": 3}, [])
    antes, despues = _palabras(original), _palabras(destino)
    assert antes - despues == Counter({"ORBEGAL": 3})
    assert despues - antes == Counter({"ORBEGAR": 3})
    assert sum(antes.values()) == sum(despues.values())


def test_prefijo_numerico_solo_con_limite_de_palabra(tmp_path):
    from adaptadores.docx_corregido import aplicar

    cuerpo = (
        "<w:p><w:r><w:t>DNI 9000011 Y DNI 90000111; RUC 20000000011.</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>REPITE 9000011, NO 90000111.</w:t></w:r></w:p>"
    )
    original = crear_docx(tmp_path / "b.docx", cuerpo)
    destino = tmp_path / "c.docx"
    carga = [_correccion("dni", "9000011", "90000112")]

    assert aplicar(original, destino, carga) == ({"dni": 2}, [])
    antes, despues = _palabras(original), _palabras(destino)
    assert antes - despues == Counter({"9000011": 2})
    assert despues - antes == Counter({"90000112": 2})
    assert despues["90000111"] == 2
    assert despues["20000000011"] == 1
