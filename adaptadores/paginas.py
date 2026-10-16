"""F32: páginas del borrador tal como se imprimen y posición de sus palabras.

Adaptador: convierte el original a PDF con LibreOffice y lo lee con PyMuPDF.
Entrega al núcleo segmentos ``(texto, x0, y0, x1, y1, linea)`` en fracciones
del tamaño de la página; no decide nada del negocio.
"""

import os
import tempfile
from pathlib import Path

from adaptadores.extraccion import _soffice

CONVERTIBLES = {".docx"}
PPP = 110
# Corre en el worker, no en una petición: el primer arranque de LibreOffice con
# perfil nuevo puede tardar minutos en un servidor lento.
TIEMPO_CONVERSION = 600


def a_pdf(original: Path, destino: Path) -> Path:
    """Convierte el original en ``destino``; el reemplazo es atómico."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destino.parent) as tmp:
        salida = _soffice(
            Path(original),
            "pdf",
            Path(tmp),
            admitidos=CONVERTIBLES,
            timeout=TIEMPO_CONVERSION,
        )
        os.replace(salida, destino)
    return destino


def _pagina(doc, numero):
    if not 1 <= numero <= doc.page_count:
        raise IndexError("Página fuera de rango.")
    return doc[numero - 1]


def paginas(pdf: Path) -> list[dict]:
    import pymupdf

    with pymupdf.open(pdf) as doc:
        return [
            {"numero": i, "proporcion": round(p.rect.height / p.rect.width, 4)}
            for i, p in enumerate(doc, 1)
        ]


def segmentos(pdf: Path, numero: int) -> list[tuple]:
    """Palabras de la página en orden de lectura, agrupadas por línea.

    F52: ``bordes`` trae el borde izquierdo de cada carácter y el derecho del
    último: una coma o una negrita no miden lo mismo que el promedio.
    """
    import pymupdf

    with pymupdf.open(pdf) as doc:
        pagina = _pagina(doc, numero)
        ancho, alto = pagina.rect.width, pagina.rect.height
        textos = pagina.get_textpage(flags=pymupdf.TEXTFLAGS_WORDS)
        palabras = pagina.get_text("words", sort=True, textpage=textos)
        caracteres = {
            (bloque["number"], n): [
                c for tramo in linea["spans"] for c in tramo["chars"]
            ]
            for bloque in textos.extractRAWDICT()["blocks"]
            for n, linea in enumerate(bloque.get("lines", ()))
        }
    lineas = {}
    resultado = []
    for x0, y0, x1, y1, texto, bloque, linea, _n in palabras:
        clave = lineas.setdefault((bloque, linea), len(lineas))
        propios = [
            c
            for c in caracteres.get((bloque, linea), ())
            if not c["c"].isspace() and x0 <= (c["bbox"][0] + c["bbox"][2]) / 2 <= x1
        ]
        if "".join(c["c"] for c in propios) == texto:
            bordes = [c["bbox"][0] for c in propios] + [x1]
        else:  # caracteres solapados: se reparte el ancho por igual
            bordes = [x0 + (x1 - x0) * i / len(texto) for i in range(len(texto) + 1)]
        resultado.append(
            (
                texto,
                max(0.0, x0 / ancho),
                max(0.0, y0 / alto),
                min(1.0, x1 / ancho),
                min(1.0, y1 / alto),
                clave,
                tuple(min(1.0, max(0.0, b / ancho)) for b in bordes),
            )
        )
    return resultado


def png(pdf: Path, numero: int) -> bytes:
    import pymupdf

    with pymupdf.open(pdf) as doc:
        return _pagina(doc, numero).get_pixmap(dpi=PPP).tobytes("png")
