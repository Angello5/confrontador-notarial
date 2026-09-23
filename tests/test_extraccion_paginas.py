"""Separación de páginas del adaptador con documentos sintéticos."""

import pymupdf

from adaptadores import extraccion
from adaptadores.extraccion import leer, leer_paginas


def test_pdf_se_entrega_por_paginas_y_leer_usa_salto_de_pagina(tmp_path, monkeypatch):
    ruta = tmp_path / "legajo-ficticio.pdf"
    documento = pymupdf.open()
    documento.new_page().insert_text((72, 72), "PAGINA FICTICIA UNO")
    documento.new_page().insert_text((72, 72), "PAGINA FICTICIA DOS")
    documento.save(ruta)
    documento.close()
    monkeypatch.setattr("adaptadores.extraccion.CACHE", tmp_path / "cache")

    paginas = leer_paginas(ruta)

    assert len(paginas) == 2
    assert "PAGINA FICTICIA UNO" in paginas[0]
    assert "PAGINA FICTICIA DOS" in paginas[1]
    assert leer(ruta) == "\f".join(paginas)


def test_cache_pdf_historica_sigue_siendoun_bloque(tmp_path, monkeypatch):
    ruta = tmp_path / "legajo-ficticio.pdf"
    documento = pymupdf.open()
    documento.new_page().insert_text((72, 72), "TEXTO HISTORICO FICTICIO")
    documento.save(ruta)
    documento.close()
    monkeypatch.setattr(
        extraccion, "_cacheado", lambda *_args: "TEXTO HISTORICO FICTICIO"
    )

    assert leer_paginas(ruta) == ("TEXTO HISTORICO FICTICIO",)


def test_la_llave_de_cache_cambia_con_el_formato_y_con_el_motor(monkeypatch):
    """Una entrada vieja no puede devolverse cuando cambia la forma del dato.

    Ocurrió de verdad: al pasar de guardar una cadena a guardar páginas, las
    entradas anteriores se seguían devolviendo como una sola página y la
    segmentación quedaba inactiva en silencio. Nada fallaba: el sistema
    simplemente dejaba de hacer lo nuevo.
    """
    from adaptadores import extraccion

    llaves = []
    monkeypatch.setattr(
        extraccion,
        "_escribir_cache",
        lambda ruta, valor: llaves.append(ruta.name),
        raising=False,
    )

    def llave_actual():
        import hashlib
        import json

        identidad = json.dumps(
            {
                "modelos": extraccion._OCR_FILES,
                "use_cls": extraccion._OCR_USE_CLS,
                "rapidocr": extraccion.importlib.metadata.version("rapidocr"),
                "formato": extraccion._FORMATO_CACHE,
            },
            sort_keys=True,
        ).encode()
        return hashlib.sha1(b"contenido" + identidad, usedforsecurity=False).hexdigest()

    original = llave_actual()
    monkeypatch.setattr(extraccion, "_FORMATO_CACHE", extraccion._FORMATO_CACHE + 1)
    assert llave_actual() != original, "cambiar el formato debe invalidar la caché"
