"""F27 ronda 2: filas de tabla del .docx y reextracción (datos ficticios)."""

import zipfile

import pytest
from django.core.management import call_command

from adaptadores import extraccion
from nucleo.verificar import catalogo, montos_exigibles, revisar


def _p(texto):
    return f"<w:p><w:r><w:t>{texto}</w:t></w:r></w:p>"


def _tabla(filas):
    return (
        "<w:tbl><w:tblPr/><w:tblGrid/>"
        + "".join(
            '<w:tr w:rsidR="00F1"><w:trPr/>'
            + "".join(
                f"<w:tc><w:tcPr/>{c if c.startswith('<') else _p(c)}</w:tc>"
                for c in fila
            )
            + "</w:tr>"
            for fila in filas
        )
        + "</w:tbl>"
    )


def _docx(ruta, cuerpo):
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr(
            "word/document.xml", f"<w:document><w:body>{cuerpo}</w:body></w:document>"
        )
    return ruta


def test_fila_de_tabla_es_una_linea_y_fuera_de_tabla_no_cambia(tmp_path):
    celda_dos_parrafos = _p("LOTE") + _p("FICTICIO")
    anidada = _tabla([["A1", "A2"], ["B1"]])
    cuerpo = (
        _p("ANTES DE LA TABLA")
        + _p("")
        + _tabla([["N°", "NOMBRE"], ["1", celda_dos_parrafos, ""], ["2", anidada]])
        + _p("DESPUES DE LA TABLA")
    )

    assert extraccion.leer(_docx(tmp_path / "t.docx", cuerpo)).splitlines() == [
        "ANTES DE LA TABLA",
        "N°  NOMBRE",
        "1  LOTE FICTICIO",
        "2  A1 A2 B1",
        "DESPUES DE LA TABLA",
    ]


def test_salto_manual_separa_lineas_y_en_tabla_no_parte_la_fila(tmp_path):
    con_salto = (
        "<w:p><w:r><w:t>3. INCISO FICTICIO.====</w:t></w:r>"
        "<w:r><w:br/><w:t>4. OTRO INCISO.</w:t><w:cr/><w:t>5. ULTIMO.</w:t></w:r></w:p>"
    )
    celda = "<w:p><w:r><w:t>LOTE</w:t><w:br/><w:t>FICTICIO</w:t></w:r></w:p>"
    cuerpo = con_salto + _tabla([["1", celda]])

    assert extraccion.leer(_docx(tmp_path / "t.docx", cuerpo)).splitlines() == [
        "3. INCISO FICTICIO.====",
        "4. OTRO INCISO.",
        "5. ULTIMO.",
        "1  LOTE FICTICIO",
    ]


def _cronograma(cambiar=None):
    filas = [["N°", "FECHA", "CAPITAL", "INTERES", "CUOTA"]]
    for n in range(1, 13):
        interes = 100 - n
        filas.append(
            [
                str(n),
                f"15/{n:02d}/2027",
                "S/ 1,000.00",
                f"S/ {interes}.00",
                f"S/ 1,{interes:03d}.00",
            ]
        )
    if cambiar:
        destino, origen = cambiar
        filas[destino][4] = filas[origen][4]
    return _p("CRONOGRAMA DE PAGOS FICTICIO") + _tabla(filas)


def _montos(tmp_path, borrador_cuerpo):
    minuta = extraccion.leer(_docx(tmp_path / "minuta.docx", _cronograma()))
    borrador = extraccion.leer(_docx(tmp_path / "borrador.docx", borrador_cuerpo))
    fuentes = {"minuta.docx": minuta}
    return [
        o
        for o in revisar(
            catalogo(fuentes), borrador, 88, None, montos_exigibles([minuta]), fuentes
        )
        if o.startswith("[MONTO]")
    ]


def test_cuota_de_otra_fila_en_cronograma_docx(tmp_path):
    obs = _montos(tmp_path, _cronograma(cambiar=(5, 9)))

    assert len(obs) == 1
    assert obs[0].startswith("[MONTO] «1,091.00» debe decir «1,095.00»")
    assert "concepto: CUOTA 5; fuente: minuta.docx" in obs[0]


def test_cronograma_docx_identico_sin_observaciones(tmp_path):
    assert _montos(tmp_path, _cronograma()) == []


def test_version_extractor_cambia_con_formato_de_texto(monkeypatch):
    primera = extraccion.version_extractor()
    monkeypatch.setattr(extraccion, "_FORMATO_TEXTO", extraccion._FORMATO_TEXTO + 1)

    assert extraccion.version_extractor() != primera


@pytest.fixture
def expediente(usuario_ficticio):
    from expedientes.models import Expediente

    return Expediente.objects.create(
        codigo="EXP-FICTICIO-270", creado_por=usuario_ficticio
    )


def _documento(expediente, rol, ruta=""):
    from expedientes.models import Documento, TextoExtraido

    texto = TextoExtraido.objects.create(
        hash_archivo=rol[0] * 64,
        version_extractor="extractor-ficticio-v1",
        texto="texto antiguo ficticio",
        ultimo_uso_el="2026-01-01T00:00:00Z",
    )
    return Documento.objects.create(
        expediente=expediente,
        rol=rol,
        nombre_original=f"{rol.lower()}-ficticio.docx",
        hash_archivo=rol[0] * 64,
        tamano_bytes=1,
        estado=Documento.LISTO,
        ruta_temporal=str(ruta),
        texto_extraido=texto,
        subido_por=expediente.creado_por,
    )


@pytest.mark.django_db
def test_reextraer_encola_con_archivo_y_no_toca_sin_archivo(
    expediente, tmp_path, settings, capsys
):
    from expedientes.models import Documento

    settings.EXPEDIENTES_TEMP_DIR = tmp_path / "temporales"
    con_archivo = _documento(
        expediente, Documento.BORRADOR, _docx(tmp_path / "b.docx", _p("X"))
    )
    sin_archivo = _documento(expediente, Documento.MINUTA, tmp_path / "no-existe.docx")

    call_command("reextraer_expediente", expediente.codigo)

    con_archivo.refresh_from_db()
    sin_archivo.refresh_from_db()
    assert con_archivo.estado == Documento.PENDIENTE
    assert con_archivo.ruta_temporal.startswith(str(settings.EXPEDIENTES_TEMP_DIR))
    assert con_archivo.ruta_temporal.endswith(".docx")
    assert sin_archivo.estado == Documento.LISTO
    assert sin_archivo.ruta_temporal.endswith("no-existe.docx")
    salida = capsys.readouterr().out
    assert "En cola: 1" in salida
    assert f"Sin archivo: {sin_archivo.nombre_original}" in salida


@pytest.mark.django_db
def test_reextraer_usa_el_borrador_original_conservado(
    expediente, tmp_path, settings, monkeypatch
):
    from expedientes import services
    from expedientes.models import Documento

    settings.EXPEDIENTES_TEMP_DIR = tmp_path / "temporales"
    original = _docx(tmp_path / "original.docx", _p("X"))
    monkeypatch.setattr(services, "ruta_original", lambda _: original, raising=False)
    borrador = _documento(expediente, Documento.BORRADOR)

    call_command("reextraer_expediente", expediente.codigo)

    borrador.refresh_from_db()
    assert borrador.estado == Documento.PENDIENTE
    assert borrador.ruta_temporal != str(original)
    assert original.exists()


@pytest.mark.django_db
def test_reextraer_expediente_inexistente():
    from django.core.management.base import CommandError

    with pytest.raises(CommandError):
        call_command("reextraer_expediente", "EXP-FICTICIO-NO")


def test_todo_mayusculas_de_word_se_lee_como_se_imprime(tmp_path):
    """F39: «AvENIDA» con «Todo mayúsculas» (w:caps) se imprime AVENIDA."""
    caps = "<w:rPr><w:caps/></w:rPr>"
    cuerpo = (
        f"<w:p><w:r>{caps}<w:t>AvENIDA Sol &amp; luna</w:t></w:r></w:p>"
        '<w:p><w:r><w:rPr><w:caps w:val="0"/></w:rPr><w:t>Avenida</w:t></w:r></w:p>'
        '<w:p><w:pPr><w:pStyle w:val="Titulo"/></w:pPr>'
        "<w:r><w:t>clausula primera</w:t></w:r></w:p>"
        # el rPr de la marca de párrafo no toca el texto
        f"<w:p><w:pPr>{caps}</w:pPr><w:r><w:t>Sin estilo</w:t></w:r></w:p>"
        '<w:p><w:r><w:rPr><w:rStyle w:val="Versal"/></w:rPr>'
        "<w:t>versalita</w:t></w:r></w:p>"
    )
    estilos = (
        f'<w:style w:type="paragraph" w:styleId="Base">{caps}</w:style>'
        '<w:style w:type="paragraph" w:styleId="Titulo">'
        '<w:basedOn w:val="Base"/></w:style>'
        '<w:style w:type="character" w:styleId="Versal">'
        "<w:rPr><w:smallCaps/></w:rPr></w:style>"
    )
    ruta = _docx(tmp_path / "c.docx", cuerpo)
    with zipfile.ZipFile(ruta, "a") as z:
        z.writestr("word/styles.xml", f"<w:styles>{estilos}</w:styles>")

    assert extraccion.leer(ruta).splitlines() == [
        "AVENIDA SOL & LUNA",
        "Avenida",
        "CLAUSULA PRIMERA",
        "Sin estilo",
        "VERSALITA",
    ]
