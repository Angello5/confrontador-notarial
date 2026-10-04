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
    """Palabras de la página en orden de lectura, agrupadas por línea."""
    import pymupdf

    with pymupdf.open(pdf) as doc:
        pagina = _pagina(doc, numero)
        ancho, alto = pagina.rect.width, pagina.rect.height
        palabras = pagina.get_text("words", sort=True)
    lineas = {}
    resultado = []
    for x0, y0, x1, y1, texto, bloque, linea, _n in palabras:
        clave = lineas.setdefault((bloque, linea), len(lineas))
        resultado.append(
            (
                texto,
                max(0.0, x0 / ancho),
                max(0.0, y0 / alto),
                min(1.0, x1 / ancho),
                min(1.0, y1 / alto),
                clave,
            )
        )
    return resultado


def png(pdf: Path, numero: int) -> bytes:
    import pymupdf

    with pymupdf.open(pdf) as doc:
        return _pagina(doc, numero).get_pixmap(dpi=PPP).tobytes("png")
