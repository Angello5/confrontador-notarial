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
