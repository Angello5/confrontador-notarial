#!/usr/bin/env python3
"""Extraccion de texto local, sin nube: .docx .doc .pdf .xlsx .txt e imagenes.

  python3 extraer.py Cliente/                 # todo el folder a stdout
  python3 extraer.py foto.jpg                 # una imagen por OCR

El OCR es RapidOCR (modelos PP-OCRv4 sobre onnxruntime, solo CPU: los mismos
pesos que PaddleOCR sin arrastrar Paddle). ~4 s por pagina en este equipo.

Los PDF se leen por su capa de texto; si no la traen (escaneo) se rasterizan
pagina a pagina y se pasan por el mismo OCR.
"""
import argparse, hashlib, json, re, subprocess, sys
from functools import lru_cache
from pathlib import Path

IMGS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
# formatos que abre textutil, que viene con macOS: no hace falta instalar nada
LEGACY = {".doc", ".rtf", ".odt", ".wordml"}
DOCS = {".docx", ".pdf", ".xlsx", ".txt", ".md", ".csv"} | IMGS | LEGACY

CACHE = Path.home() / ".cache" / "notaria-ocr"
DPI = 200  # suficiente para DNI y sellos; a 300 tarda el doble sin ganar aciertos


@lru_cache(maxsize=1)
def _ocr():
    from rapidocr import RapidOCR
    return RapidOCR()


def _cacheado(clave: bytes, calcular):
    """OCR cuesta segundos por pagina y estos archivos no cambian entre corridas."""
    f = CACHE / (hashlib.sha1(clave).hexdigest() + ".json")
    if f.exists():
        return json.loads(f.read_text())
    txt = calcular()
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(txt))
    return txt


def ocr_lineas(fuente, tol: int = 9) -> str:
    """OCR reconstruyendo filas. Descarta cajas inclinadas: los sellos de agua van
    en diagonal y el texto real es horizontal, asi que la inclinacion los separa.

    `fuente` es una ruta o los bytes de la imagen. Las columnas quedan separadas
    por dos espacios, que es lo que usan los lectores de rotulo del RENIEC.
    """
    r = _ocr()(str(fuente) if isinstance(fuente, Path) else fuente)
    if not r.txts:
        return ""
    cajas = []
    for txt, box in zip(r.txts, r.boxes):
        (x0, y0), (x1, y1) = box[0], box[1]
        if abs(y1 - y0) <= max(4, abs(x1 - x0) * 0.08):  # borde superior horizontal
            cajas.append((sum(pt[1] for pt in box) / 4, x0, txt))
    cajas.sort()
    filas, actual = [], []
    for y, x, txt in cajas:
        if actual and y - actual[0][0] > tol:
            filas.append(actual)
            actual = []
        actual.append((y, x, txt))
    filas.append(actual)
    return "\n".join("  ".join(t for _, _, t in sorted(f, key=lambda c: c[1])) for f in filas if f)


def _pdf(p: Path) -> str:
    import pymupdf
    with pymupdf.open(p) as doc:
        paginas = []
        for i, pg in enumerate(doc, 1):
            txt = pg.get_text()
            if len(txt.strip()) < 50:  # escaneo sin capa de texto
                print(f"    pagina {i}: sin texto, aplicando OCR", file=sys.stderr)
                txt = ocr_lineas(pg.get_pixmap(dpi=DPI).tobytes("png"))
            paginas.append(txt)
    return "\n".join(paginas)


def _xlsx(p: Path) -> str:
    import openpyxl
    wb = openpyxl.load_workbook(p, data_only=True, read_only=True)
    return "\n".join(
        "  ".join("" if c is None else str(c) for c in fila).rstrip()
        for h in wb.worksheets for fila in h.iter_rows(values_only=True)
    )


def _legacy(p: Path) -> str:
    """Word 97-2003 y compañía, via textutil (parte de macOS). Un .doc no es un zip
    sino un contenedor OLE, asi que python-docx no puede con el."""
    if sys.platform != "darwin":
        raise ValueError(f"{p.name}: .doc necesita textutil (macOS) o LibreOffice")
    r = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(p)],
                       capture_output=True, text=True)
    if r.returncode:
        raise ValueError(f"{p.name}: textutil no pudo leerlo ({r.stderr.strip()[:80]})")
    # textutil separa las celdas con tabulador; el resto del codigo espera dos espacios
    return r.stdout.replace("\t", "  ")


# document.xml primero; el resto son encabezados, pies y notas al pie
PARTES_DOCX = re.compile(r"word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml")
RE_TAB = re.compile(r"<w:tab(?:\s[^>]*)?/>")
# mc:AlternateContent guarda el mismo cuadro de texto dos veces (wps moderno y VML
# antiguo). Sin descartar el Fallback, cada nota se lee duplicada.
RE_FALLBACK = re.compile(r"<mc:Fallback>.*?</mc:Fallback>", re.S)


def _docx(p: Path) -> str:
    """Se lee el XML en crudo y no con python-docx porque `document.paragraphs`
    no entra a los cuadros de texto (w:txbxContent) ni a los encabezados. En este
    caso real ahi vivia una nota al notario con una errata («CONSTACIA») que se
    perdia entera."""
    import zipfile
    from html import unescape

    lineas = []
    with zipfile.ZipFile(p) as z:
        nombres = sorted((n for n in z.namelist() if PARTES_DOCX.fullmatch(n)),
                         key=lambda n: (n != "word/document.xml", n))
        for n in nombres:
            xml = z.read(n).decode("utf-8", "ignore")
            xml = RE_TAB.sub("<w:t>  </w:t>", RE_FALLBACK.sub("", xml))
            for parrafo in xml.split("</w:p>"):
                # el grupo opcional exige espacio tras "w:t": sin eso <w:tab .../>
                # entra como si abriera un <w:t> y se arrastra el XML crudo
                t = "".join(re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", parrafo, re.S))
                if t.strip():
                    lineas.append(unescape(t))
    return "\n".join(lineas)


def leer(p: Path) -> str:
    """Texto plano de cualquier formato soportado. Cachea lo que pasa por OCR."""
    s = p.suffix.lower()
    if s == ".docx":
        return _docx(p)
    if s in LEGACY:
        return _legacy(p)
    if s == ".xlsx":
        return _xlsx(p)
    if s == ".pdf":
        return _cacheado(p.read_bytes(), lambda: _pdf(p))
    if s in IMGS:
        return _cacheado(p.read_bytes(), lambda: ocr_lineas(p))
    if s in {".xls", ".ppt"}:
        raise ValueError(f"{p.name}: formato binario antiguo, guardalo como .{s[1:]}x")
    return p.read_text(errors="ignore")


def recolectar(rutas: list[str]) -> dict[str, str]:
    """Nombre de archivo -> texto, recorriendo carpetas."""
    out = {}
    for r in rutas:
        p = Path(r)
        archivos = sorted(x for x in p.rglob("*") if x.suffix.lower() in DOCS) if p.is_dir() else [p]
        for a in archivos:
            print(f"  leyendo {a.name}", file=sys.stderr)
            out[a.name] = leer(a)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rutas", nargs="+", help="archivos o carpetas")
    ap.add_argument("--json", action="store_true", help="salida {archivo: texto}")
    a = ap.parse_args()

    textos = recolectar(a.rutas)
    if a.json:
        print(json.dumps(textos, ensure_ascii=False, indent=2))
    else:
        for nombre, txt in textos.items():
            print(f"\n===== {nombre} =====\n{txt}")
    return 0 if textos else 1


if __name__ == "__main__":
    sys.exit(main())
