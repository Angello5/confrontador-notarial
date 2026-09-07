"""Check minimo de extraer.py: las rutas nuevas (PDF escaneado y xlsx) y el cache.

  python3 test_extraer.py
"""
import subprocess
import tempfile
from pathlib import Path

import openpyxl
import pymupdf

import extraer

BASE = Path(__file__).parent
DNI = BASE / "Cliente" / "1785794685531_1.jpg"

if __name__ == "__main__":
    # imagen: el dato clave del RENIEC sobrevive al filtro de sellos de agua
    img = extraer.leer(DNI)
    assert "40324003-1" in img, img[:300]
    assert "AVELLANEDA" in img, img[:300]
    assert extraer.leer(DNI) == img          # segunda pasada sale del cache

    with tempfile.TemporaryDirectory() as tmp:
        # PDF sin capa de texto: la misma imagen incrustada, que es el caso de escaneo
        pdf = Path(tmp) / "escaneado.pdf"
        doc = pymupdf.open()
        pagina = doc.new_page(width=595, height=842)
        pagina.insert_image(pagina.rect, filename=str(DNI))
        doc.save(pdf)
        doc.close()
        assert not pymupdf.open(pdf)[0].get_text().strip()   # de verdad no trae texto
        assert "40324003-1" in extraer.leer(pdf), "el OCR de PDF escaneado no encontro el CUI"

        # .doc (Word 97-2003): contenedor OLE, no zip. Se hace uno de verdad
        # convirtiendo con textutil, que es lo mismo que usa leer() al revés.
        doc = Path(tmp) / "minuta.doc"
        rtf = Path(tmp) / "minuta.rtf"
        rtf.write_text(r"{\rtf1\ansi DONACION DE ACCIONES Y DERECHOS\par KARDEX 71168\par}")
        subprocess.run(["textutil", "-convert", "doc", "-output", str(doc), str(rtf)],
                       check=True, capture_output=True)
        assert doc.read_bytes()[:4] == b"\xd0\xcf\x11\xe0", "no quedo un OLE de verdad"
        texto_doc = extraer.leer(doc)
        assert "DONACION DE ACCIONES Y DERECHOS" in texto_doc, texto_doc
        assert "71168" in texto_doc, texto_doc
        assert extraer.leer(rtf).strip().startswith("DONACION"), extraer.leer(rtf)

        xlsx = Path(tmp) / "datos.xlsx"
        wb = openpyxl.Workbook()
        wb.active.append(["DNI", "40324003"])
        wb.active.append(["Partida", 70703688])
        wb.save(xlsx)
        assert extraer.leer(xlsx).splitlines() == ["DNI  40324003", "Partida  70703688"], \
            extraer.leer(xlsx)

    # el cuerpo del .docx no basta: esta nota vive en un cuadro de texto y
    # mc:Fallback la guarda una segunda vez, asi que hay que leerla exactamente 1 vez
    cuerpo = extraer.leer(BASE / "Proyecto(borrador)" / "1785794688639_71168_malo2.docx")
    assert "<w:" not in cuerpo, "se filtro XML crudo al texto"
    nota = "CONSULTAR NUMERO DE CONSTACIA DE ALCABALA (3)"
    assert cuerpo.count(nota) == 1, f"la nota del cuadro de texto sale {cuerpo.count(nota)} veces"

    print("OK — imagen, PDF escaneado, .doc, .rtf, xlsx, cuadros de texto y cache")
