#!/usr/bin/env python3
"""Extraccion de texto local, sin nube: .docx .doc .pdf .xlsx .txt e imagenes.

  python3 extraer.py Cliente/                 # todo el folder a stdout
  python3 extraer.py foto.jpg                 # una imagen por OCR

El OCR es RapidOCR/onnxruntime en CPU, con PP-OCRv5 latin aprovisionado localmente.

Los PDF se leen por su capa de texto; si no la traen (escaneo) se rasterizan
pagina a pagina y se pasan por el mismo OCR.
"""

import argparse
import hashlib
import importlib.metadata
import json
import re
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

from nucleo.verificar import IMGS, SEPARADOR_PAGINA

# formatos que abre textutil (macOS) o LibreOffice (Linux)
LEGACY = {".doc", ".rtf", ".odt", ".wordml"}
DOCS = {".docx", ".pdf", ".xlsx", ".txt", ".md", ".csv"} | IMGS | LEGACY

CACHE = Path.home() / ".cache" / "notaria-ocr"
OCR_MODELS = CACHE / "models"
SOFFICE = "soffice"
DPI = 200  # suficiente para DNI y sellos; a 300 tarda el doble sin ganar aciertos

_OCR_FILES = {
    "ch_PP-OCRv5_mobile_det.onnx": "4d97c44a20d30a81aad087d6a396b08f786c4635742afc391f6621f5c6ae78ae",
    "latin_PP-OCRv5_rec_mobile_infer.onnx": "b20bd37c168a570f583afbc8cd7925603890efbcdc000a59e22c269d160b5f5a",
}
_OCR_USE_CLS = False

# 1: texto unido en una cadena. 2: una entrada por pagina.
_FORMATO_CACHE = 2


def version_extractor() -> str:
    """Identidad estable de los recursos y opciones que producen el texto.

    Incluye la version de rapidocr: los modelos pueden ser los mismos y aun asi
    la libreria cambiar el preproceso o el postproceso, y entonces el texto
    cambia. Si no estuviera en la llave, la cache seguiria devolviendo el texto
    del motor anterior tras una actualizacion. No se incluye onnxruntime: no
    altera el texto y su version sube a menudo, lo que invalidaria la cache sin
    motivo.
    """
    identidad = json.dumps(
        {
            "modelos": sorted(_OCR_FILES.items()),
            "use_cls": _OCR_USE_CLS,
            "rapidocr": importlib.metadata.version("rapidocr"),
        },
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(identidad).hexdigest()


@lru_cache(maxsize=1)
def _ocr():
    """Carga recursos locales fijados; el proceso no descarga modelos."""
    from rapidocr import RapidOCR

    paths = {name: OCR_MODELS / name for name in _OCR_FILES}
    for name, path in paths.items():
        if (
            not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != _OCR_FILES[name]
        ):
            raise RuntimeError(f"Recurso OCR ausente o inválido: {name}")
    return RapidOCR(
        params={
            "Global.use_cls": _OCR_USE_CLS,
            "Global.log_level": "error",
            "Det.model_path": str(paths["ch_PP-OCRv5_mobile_det.onnx"]),
            "Rec.model_path": str(paths["latin_PP-OCRv5_rec_mobile_infer.onnx"]),
        }
    )


def _cacheado(clave: bytes, calcular):
    """Cachea OCR costoso usando también la identidad de sus modelos."""
    # Identificador de caché, no firma ni decisión de seguridad.
    identidad = json.dumps(
        {
            "modelos": _OCR_FILES,
            "use_cls": _OCR_USE_CLS,
            "rapidocr": importlib.metadata.version("rapidocr"),
            # Sube cuando cambia la FORMA de lo que se cachea, no solo el motor.
            # Sin esto, una entrada vieja se devuelve tal cual y el cambio queda
            # inactivo en silencio: paso al guardar paginas en vez de una cadena.
            "formato": _FORMATO_CACHE,
        },
        sort_keys=True,
    ).encode()
    f = CACHE / (
        hashlib.sha1(clave + identidad, usedforsecurity=False).hexdigest() + ".json"
    )
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
    return "\n".join(
        "  ".join(t for _, _, t in sorted(f, key=lambda c: c[1])) for f in filas if f
    )


def _pdf_paginas(p: Path) -> tuple[str, ...]:
    import pymupdf

    with pymupdf.open(p) as doc:
        paginas = []
        for i, pg in enumerate(doc, 1):
            txt = pg.get_text()
            if len(txt.strip()) < 50:  # escaneo sin capa de texto
                print(f"    pagina {i}: sin texto, aplicando OCR", file=sys.stderr)
                txt = ocr_lineas(pg.get_pixmap(dpi=DPI).tobytes("png"))
            paginas.append(txt)
    return tuple(paginas)


def _pdf(p: Path) -> str:
    return SEPARADOR_PAGINA.join(_pdf_paginas(p))


def _xlsx(p: Path) -> str:
    import openpyxl

    wb = openpyxl.load_workbook(p, data_only=True, read_only=True)
    return "\n".join(
        "  ".join("" if c is None else str(c) for c in fila).rstrip()
        for h in wb.worksheets
        for fila in h.iter_rows(values_only=True)
    )


def _ruta_legacy(p: Path) -> Path:
    try:
        p = p.resolve(strict=True)
    except OSError:
        raise ValueError(f"{p.name}: formato legacy inválido") from None
    if not p.is_file() or p.suffix.lower() not in LEGACY:
        raise ValueError(f"{p.name}: formato legacy inválido")
    return p


def _soffice(p: Path, formato: str, destino: Path) -> Path:
    """Convierte con LibreOffice headless. Perfil propio en un temporal para no
    chocar con otra instancia abierta; los errores no llevan stderr ni rutas."""
    p = _ruta_legacy(p)
    destino = destino.resolve(strict=True)
    with tempfile.TemporaryDirectory() as perfil:
        try:
            r = subprocess.run(  # noqa: S603 argv sin shell; conversor fijo y ruta como argumento
                [
                    SOFFICE,
                    f"-env:UserInstallation={Path(perfil).as_uri()}",
                    "--headless",
                    "--convert-to",
                    formato,
                    "--outdir",
                    str(destino),
                    str(p),
                ],
                capture_output=True,
                timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise ValueError(
                f"{p.name}: .doc necesita LibreOffice ({SOFFICE}) en PATH"
            ) from None
    salida = destino / f"{p.stem}.{formato.split(':')[0]}"
    if r.returncode or not salida.is_file():
        raise ValueError(f"{p.name}: LibreOffice no pudo convertirlo")
    return salida


def _legacy(p: Path) -> str:
    """Word 97-2003 y compañía, via textutil en macOS o LibreOffice en Linux. Un
    .doc no es un zip sino un contenedor OLE, asi que python-docx no puede con el."""
    if sys.platform == "darwin":
        p = _ruta_legacy(p)
        r = subprocess.run(  # noqa: S603 argv sin shell; conversor fijo y ruta como argumento
            ["/usr/bin/textutil", "-convert", "txt", "-stdout", str(p)],
            capture_output=True,
            text=True,
        )
        if r.returncode:
            raise ValueError(
                f"{p.name}: textutil no pudo leerlo ({r.stderr.strip()[:80]})"
            )
        txt = r.stdout
    else:
        with tempfile.TemporaryDirectory() as tmp:
            txt = _soffice(p, "txt:Text (encoded):UTF8", Path(tmp)).read_text(
                encoding="utf-8-sig"
            )
    # separan las celdas con tabulador; el resto del codigo espera dos espacios
    return txt.replace("\t", "  ")


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
        nombres = sorted(
            (n for n in z.namelist() if PARTES_DOCX.fullmatch(n)),
            key=lambda n: (n != "word/document.xml", n),
        )
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
    return SEPARADOR_PAGINA.join(leer_paginas(p))


def leer_paginas(p: Path) -> tuple[str, ...]:
    """Devuelve una página lógica por elemento y conserva el cache de OCR."""
    s = p.suffix.lower()
    p = p.resolve(strict=True)
    if s == ".docx":
        return (_docx(p),)
    if s in LEGACY:
        return (_legacy(p),)
    if s == ".xlsx":
        return (_xlsx(p),)
    if s == ".pdf":
        paginas = _cacheado(p.read_bytes(), lambda: list(_pdf_paginas(p)))
        return (paginas,) if isinstance(paginas, str) else tuple(paginas)
    if s in IMGS:
        return (_cacheado(p.read_bytes(), lambda: ocr_lineas(p)),)
    if s in {".xls", ".ppt"}:
        raise ValueError(f"{p.name}: formato binario antiguo, guardalo como .{s[1:]}x")
    return (p.read_text(errors="ignore"),)


def archivos(rutas: list[str]) -> list[Path]:
    """Expande carpetas y conserva solo los formatos de documentos admitidos."""
    return [
        archivo
        for ruta in rutas
        for archivo in (
            sorted(x for x in Path(ruta).rglob("*") if x.suffix.lower() in DOCS)
            if Path(ruta).is_dir()
            else [Path(ruta)]
        )
    ]


def recolectar(rutas: list[str]) -> dict[str, str]:
    """Nombre de archivo -> texto, recorriendo carpetas."""
    out = {}
    for archivo in archivos(rutas):
        print(f"  leyendo {archivo.name}", file=sys.stderr)
        out[archivo.name] = leer(archivo)
    return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
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
