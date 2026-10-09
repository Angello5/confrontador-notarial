#!/usr/bin/env python3
"""Extraccion de texto local, sin nube: .docx .doc .pdf .xlsx .txt e imagenes.

  python3 extraer.py Cliente/                 # todo el folder a stdout
  python3 extraer.py foto.jpg                 # una imagen por OCR

El OCR es RapidOCR/onnxruntime en CPU, con PP-OCRv5 latin aprovisionado localmente.

Los PDF se leen por su capa de texto; si no la traen (escaneo) se rasterizan
pagina a pagina y se pasan por el mismo OCR.
"""

import argparse
import atexit
import hashlib
import importlib.metadata
import json
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

from nucleo.verificar import IMGS, SEPARADOR_PAGINA
from adaptadores import calidad_ocr
from adaptadores.calidad_ocr import capa_pdf_dudosa

# formatos que abre textutil (macOS) o LibreOffice (Linux)
LEGACY = {".doc", ".rtf", ".odt", ".wordml"}
DOCS = {".docx", ".pdf", ".xlsx", ".txt", ".md", ".csv"} | IMGS | LEGACY

CACHE = Path.home() / ".cache" / "notaria-ocr"
OCR_MODELS = CACHE / "models"
SOFFICE = "soffice"
DPI = 200  # resolución inicial; cambios sujetos a medición
# Marca de agua: con 10 o más cajas inclinadas descartadas se relee la página
# dejando solo la tinta (gris < 130). Medido en consultas RENIEC impresas:
# 21–35 cajas con marca y 0–4 sin ella; a 130 la marca desaparece y el texto
# queda (a 160 vuelve parte de la marca).
MARCA_AGUA_MINIMA = 10
UMBRAL_TINTA = 130
# La relectura se acepta si recupera texto: +15–20 % de letras cuando aparecía
# el nombre tapado; con 1 % o menos solo cambiaban letras sueltas.
TEXTO_RECUPERADO = 1.01
# F33: 0,001 % de píxeles oscuros. Una sola línea con un DNI ocupa ~0,03 % y
# un «1» aislado ~0,0016 %: por debajo solo quedan hojas totalmente blancas.
HOJA_BLANCA = 0.00001

_OCR_FILES = {
    "ch_PP-OCRv5_mobile_det.onnx": "4d97c44a20d30a81aad087d6a396b08f786c4635742afc391f6621f5c6ae78ae",
    "latin_PP-OCRv5_rec_mobile_infer.onnx": "b20bd37c168a570f583afbc8cd7925603890efbcdc000a59e22c269d160b5f5a",
}
_OCR_USE_CLS = False

# 1: texto unido en una cadena. 2: una entrada por pagina.
_FORMATO_CACHE = 3
# Forma del texto extraido que no pasa por la cache de OCR (identidad en la base).
# 2: cada fila de tabla de un .docx es una linea (F27).
# 3: el salto manual <w:br/> de un .docx también separa líneas.
# 4: el «Todo mayúsculas» (w:caps) de un .docx se aplica al texto (F39).
# 5: la capa de texto de un PDF se lee por filas, como el OCR (F43).
_FORMATO_TEXTO = 5


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
            "formato_texto": _FORMATO_TEXTO,
            "calidad_ocr": calidad_ocr.VERSION,
            "dpi": DPI,
            "formato_cache": _FORMATO_CACHE,
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
            # F33: sin reserva, cada lote de líneas de ancho distinto pide y
            # libera memoria; con ella la página real tarda ~18 % menos.
            "EngineConfig.onnxruntime.enable_cpu_mem_arena": True,
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
            "extractor": version_extractor(),
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
    """Texto OCR con agrupación por inclinación y reintentos acotados."""
    return ocr_informe(fuente, tol)["texto"]


def _imagen(fuente):
    """Imagen RGB de la fuente, o None si no se puede abrir."""
    from PIL import Image, ImageOps, UnidentifiedImageError

    if hasattr(fuente, "shape"):  # matriz BGR de una página PDF
        return Image.fromarray(fuente[:, :, ::-1])
    try:
        with Image.open(
            fuente if isinstance(fuente, Path) else io.BytesIO(fuente)
        ) as original:
            return ImageOps.exif_transpose(original).convert("RGB")
    except (UnidentifiedImageError, OSError, TypeError):
        return None


def _oscuros(imagen):
    """Fracción de píxeles con gris menor que 200, el criterio de F31."""
    hist = imagen.convert("L").histogram()
    return sum(hist[:200]) / (imagen.width * imagen.height)


def _matriz(imagen):
    """El motor trabaja en BGR; pasarle la matriz evita codificar un PNG."""
    import numpy as np

    return np.ascontiguousarray(np.asarray(imagen)[:, :, ::-1])


def _valor(informe):
    # Una hoja de lado leída en vertical puntúa igual que la horizontal.
    return calidad_ocr.puntuacion(informe) * (0.5 + calidad_ocr.horizontal(informe))


def _sin_marca_de_agua(imagen, motor, informe, tol):
    """Relee la página sin los grises claros de una marca de agua diagonal.

    El detector junta la marca con el texto que cruza en una sola caja
    inclinada y, al descartarla, se pierde también el texto (un «Nombres:» sin
    valor en las consultas RENIEC impresas).
    """
    limpia = imagen.convert("L").point(lambda v: 0 if v < UMBRAL_TINTA else 255)
    try:
        nuevo = calidad_ocr.resumir(motor(_matriz(limpia.convert("RGB"))), tol)
    except (RuntimeError, ValueError, OSError):
        nuevo = None
    # Letras y no _valor: la puntuación topa en 500 letras y pesa la confianza,
    # y una relectura que recupera el nombre baja a veces una centésima. Sin
    # texto recuperado queda la lectura original: binarizar también puede
    # cambiar una letra de un apellido.
    letras = lambda i: sum(c.isalnum() for c in i["texto"])  # noqa: E731
    if (
        nuevo is not None
        and nuevo["cajas_descartadas"] < MARCA_AGUA_MINIMA
        and letras(nuevo) >= letras(informe) * TEXTO_RECUPERADO
    ):
        nuevo["transformacion"] = {"giro": 0, "escala": 1, "umbral": UMBRAL_TINTA}
        informe = nuevo
    informe["intentos"] = 2
    return informe


def ocr_informe(fuente, tol=9, reintentar=True):
    imagen = _imagen(fuente)
    if imagen is not None and _oscuros(imagen) <= HOJA_BLANCA:
        return _informe_nativo("", "ocr", ["pagina_casi_vacia"])
    motor = _ocr()
    informe = calidad_ocr.resumir(
        motor(str(fuente) if isinstance(fuente, Path) else fuente), tol
    )
    if (
        reintentar
        and imagen is not None
        and informe["cajas_descartadas"] >= MARCA_AGUA_MINIMA
    ):
        informe = _sin_marca_de_agua(imagen, motor, informe, tol)
    if (
        not reintentar
        or imagen is None
        or not informe["requiere_revision"]
        or informe["motivos"] == ["confianza_no_disponible"]
        or (
            not {"sin_texto", "lectura_escasa"}.intersection(informe["motivos"])
            and (informe["confianza"] or 0) >= calidad_ocr.CONFIANZA_MINIMA
        )
    ):
        return informe
    # Una hoja prácticamente vacía no necesita repetir el motor.
    if _oscuros(imagen) < 0.001:
        informe["motivos"] = ["pagina_casi_vacia"]
        return informe
    intentos = informe["intentos"]
    for giro in (180, 90, 270):
        candidata = imagen.rotate(giro, expand=True)
        try:
            nuevo = calidad_ocr.resumir(motor(_matriz(candidata)), tol)
        except (RuntimeError, ValueError, OSError):
            informe["motivos"] = list(
                dict.fromkeys(informe["motivos"] + ["reintento_fallido"])
            )
            informe["requiere_revision"] = True
            break
        intentos += 1
        nuevo["transformacion"] = {"giro": giro, "escala": 1}
        nuevo["dimensiones"] = [candidata.width, candidata.height]
        if _valor(nuevo) > _valor(informe) * 1.1:
            # Si ambas lecturas son extensas, una alternativa no elimina la
            # incertidumbre de los números contradictorios. Una lectura vacía o
            # escasa no contradice nada (F33).
            if not {"sin_texto", "lectura_escasa"}.intersection(
                informe["motivos"]
            ) and re.findall(r"\d+", informe["texto"]) != re.findall(
                r"\d+", nuevo["texto"]
            ):
                nuevo["motivos"].append("lecturas_divergentes")
                nuevo["requiere_revision"] = True
            informe = nuevo
        if not informe["requiere_revision"] and calidad_ocr.horizontal(informe) > 0.8:
            break
    informe["intentos"] = intentos
    return informe


def _pdf_paginas(p: Path) -> tuple[str, ...]:
    return tuple(pagina["texto"] for pagina in _pdf_informe(p))


def _filas_pdf(pg, tol=4):
    """Capa de texto por filas, como el OCR (F43).

    En una boleta SUNARP el rótulo y su valor son bloques sueltos y el orden de
    la capa los separa («Placa» lejos de «: AXC000»). Se juntan las líneas de
    la misma altura de izquierda a derecha. El texto en diagonal (marca de
    agua de la consulta) se descarta, como las cajas inclinadas del OCR.
    """
    lineas = sorted(
        ((y0 + y1) / 2, x0, texto)
        for bloque in pg.get_text("dict")["blocks"]
        for linea in bloque.get("lines", ())
        if abs(linea["dir"][1]) < 0.05
        and (texto := "".join(s["text"] for s in linea["spans"]).strip())
        for x0, y0, _, y1 in (linea["bbox"],)
    )
    filas = []
    for y, x, texto in lineas:
        if filas and y - filas[-1][0] <= tol:
            filas[-1][1].append((x, texto))
        else:
            filas.append((y, [(x, texto)]))
    return "\n".join("  ".join(t for _, t in sorted(celdas)) for _, celdas in filas)


def _pdf_informe(p):
    import pymupdf

    with pymupdf.open(p) as doc:
        paginas = []
        for i, pg in enumerate(doc, 1):
            txt = pg.get_text()
            if capa_pdf_dudosa(txt):
                print(f"    pagina {i}: lectura dudosa, aplicando OCR", file=sys.stderr)
                informe = ocr_informe(_matriz_pagina(pg.get_pixmap(dpi=DPI)))
                legibles = sum(c.isalnum() for c in txt)
                recuperados = sum(c.isalnum() for c in informe["texto"])
                if txt.strip() and (
                    not informe["texto"].strip()
                    or recuperados < legibles * 0.8
                    or (
                        informe.get("requiere_revision", False)
                        # Una lectura dudosa solo sustituye una capa corta si aporta más.
                        and (legibles >= 50 or recuperados <= legibles)
                    )
                ):
                    txt = "".join(
                        "\ufffd" if ord(c) < 32 and c not in "\n\r\t\f" else c
                        for c in txt
                    )
                    informe = _informe_nativo(
                        txt, "texto_pdf", ["capa_dudosa_sin_mejora"]
                    )
            else:
                informe = _informe_nativo(_filas_pdf(pg), "texto_pdf")
            paginas.append(informe)
    return tuple(paginas)


def _matriz_pagina(pix):
    import numpy as np

    rgb = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)
    return np.ascontiguousarray(rgb[:, :, 2::-1])


def _informe_nativo(texto, metodo, motivos=None):
    return {
        "texto": texto,
        "metodo": metodo,
        "confianza": None,
        "requiere_revision": bool(motivos),
        "motivos": motivos or [],
        "intentos": 0,
        "cajas": [],
    }


def _pdf(p: Path) -> str:
    return SEPARADOR_PAGINA.join(_pdf_paginas(p))


def _xlsx(p: Path) -> str:
    import openpyxl

    wb = openpyxl.load_workbook(p, data_only=True, read_only=True)
    try:
        return "\n".join(
            "  ".join("" if c is None else str(c) for c in fila).rstrip()
            for h in wb.worksheets
            for fila in h.iter_rows(values_only=True)
        )
    finally:
        wb.close()


def _ruta_legacy(p: Path, admitidos=LEGACY) -> Path:
    try:
        p = p.resolve(strict=True)
    except OSError:
        raise ValueError(f"{p.name}: formato legacy inválido") from None
    if not p.is_file() or p.suffix.lower() not in admitidos:
        raise ValueError(f"{p.name}: formato legacy inválido")
    return p


_PERFILES_SOFFICE = {}


def _perfil_soffice() -> Path:
    """Un perfil por proceso: prepararlo cuesta tanto como convertir (F33).

    No guarda texto ni nombres de los documentos; vive junto a la caché OCR y
    se borra al terminar el proceso. LibreOffice bloquea su perfil, por eso no
    se comparte entre procesos.
    """
    clave = (os.getpid(), CACHE)
    if clave not in _PERFILES_SOFFICE:
        perfil = CACHE / f"libreoffice-{os.getpid()}"
        atexit.register(shutil.rmtree, perfil, ignore_errors=True)
        _PERFILES_SOFFICE[clave] = perfil
    perfil = _PERFILES_SOFFICE[clave]
    perfil.parent.mkdir(parents=True, exist_ok=True)
    return perfil


def _soffice(
    p: Path, formato: str, destino: Path, admitidos=LEGACY, timeout=120
) -> Path:
    """Convierte con LibreOffice headless con el perfil del proceso; si falla,
    el perfil se descarta. Los errores no llevan stderr ni rutas.
    F32 admite también .docx al dibujar las páginas del borrador."""
    p = _ruta_legacy(p, admitidos)
    destino = destino.resolve(strict=True)
    perfil = _perfil_soffice()
    try:
        r = subprocess.run(  # noqa: S603 argv sin shell; conversor fijo y ruta como argumento
            [
                SOFFICE,
                f"-env:UserInstallation={perfil.as_uri()}",
                "--headless",
                "--convert-to",
                formato,
                "--outdir",
                str(destino),
                str(p),
            ],
            capture_output=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        shutil.rmtree(perfil, ignore_errors=True)
        raise ValueError(
            f"{p.name}: .doc necesita LibreOffice ({SOFFICE}) en PATH"
        ) from None
    salida = destino / f"{p.stem}.{formato.split(':')[0]}"
    if r.returncode or not salida.is_file():
        shutil.rmtree(perfil, ignore_errors=True)
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
RE_WT = re.compile(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", re.S)
# Un salto manual (Mayús+Intro) separa líneas como un párrafo: sin él, el
# inciso siguiente queda pegado a la línea anterior y su correlativo no se lee.
RE_DOCX_MARCA = re.compile(
    r"</w:p>|<w:br(?=[\s/>])[^>]*>|<w:cr(?=[\s/>])[^>]*>"
    r"|<w:tbl(?=[\s>])|</w:tbl>|</w:tc>|</w:tr>"
)
# F39: «Todo mayúsculas» y versalitas. Word imprime «AVENIDA» aunque se tecleara
# «AvENIDA»; el texto debe decir lo que se imprime.
RE_CAPS = re.compile(r'<w:(?:caps|smallCaps)(?:\s+w:val="([^"]*)")?\s*/>')
RE_ETIQUETA = re.compile(r"<(/?)w:(p|pPr|pStyle|r|rStyle|caps|smallCaps|t)\b([^>]*)>")
RE_VAL = re.compile(r'w:val="([^"]*)"')
# formato anterior de un cambio controlado: no es el que se imprime
RE_CAMBIO_FORMATO = re.compile(r"<w:(rPrChange|pPrChange)\b.*?</w:\1>", re.S)


def _caps(val) -> bool:
    return val is None or val.lower() not in {"0", "false", "off"}


def _val(atributos):
    m = RE_VAL.search(atributos)
    return m[1] if m else None


def _heredado(estilo, propios: dict, base: dict):
    """Caps del estilo o del primero de su cadena basedOn que lo defina."""
    for _ in range(20):  # el tope corta un ciclo
        if estilo is None or propios.get(estilo) is not None:
            return propios.get(estilo)
        estilo = base.get(estilo)
    return None


def _estilos_caps(z) -> tuple[dict, bool]:
    """(caps de cada estilo con su herencia, caps por defecto del documento)."""
    try:
        xml = z.read("word/styles.xml").decode("utf-8", "ignore")
    except KeyError:
        return {}, False
    propios, base = {}, {}
    for m in re.finditer(
        r'<w:style\b[^>]*\bw:styleId="([^"]+)"[^>]*>(.*?)</w:style>', xml, re.S
    ):
        rpr = re.search(r"<w:rPr>.*?</w:rPr>", m[2], re.S)
        caps = rpr and RE_CAPS.search(rpr[0])
        propios[m[1]] = _caps(caps[1]) if caps else None
        if padre := re.search(r'<w:basedOn\s+w:val="([^"]+)"', m[2]):
            base[m[1]] = padre[1]
    defecto = re.search(r"<w:rPrDefault>.*?</w:rPrDefault>", xml, re.S)
    caps = defecto and RE_CAPS.search(defecto[0])
    estilos = {e: _heredado(e, propios, base) for e in propios}
    return estilos, bool(caps and _caps(caps[1]))


def _seguir(pila: dict, cierre: str, nombre: str, atributos: str) -> None:
    """Abre o cierra párrafos («p») y runs («r») y anota su estilo y su caps.

    El fondo de cada pila es el documento y no se saca. El rPr dentro de pPr es
    de la marca de párrafo y no toca el texto.
    """
    if nombre == "pPr":
        pila["ppr"] += -1 if cierre else 1
    elif nombre in ("p", "r"):
        abiertos = pila[nombre]
        if cierre:
            del abiertos[max(1, len(abiertos) - 1) :]
        elif not atributos.endswith("/"):
            abiertos.append({})
    elif nombre == "pStyle":
        pila["p"][-1]["estilo"] = _val(atributos)
    elif pila["ppr"]:
        return
    elif nombre == "rStyle":
        pila["r"][-1]["estilo"] = _val(atributos)
    else:  # caps o smallCaps
        pila["r"][-1]["caps"] = _caps(_val(atributos))


def _caps_efectivo(pila: dict, estilos: dict, defecto: bool) -> bool:
    """Formato directo del run, su estilo de carácter, el del párrafo o el defecto."""
    run, parrafo = pila["r"][-1], pila["p"][-1]
    for caps in (
        run.get("caps"),
        estilos.get(run.get("estilo")),
        estilos.get(parrafo.get("estilo")),
    ):
        if caps is not None:
            return caps
    return defecto


def _con_mayusculas(xml: str, estilos: dict, defecto: bool) -> str:
    """Pone en mayúsculas el texto de cada run que Word imprime así.

    Pilas: un cuadro de texto anida párrafos y runs dentro de otro run.
    ponytail: sin el XOR de propiedades alternables entre estilos de Word.
    """
    from html import escape, unescape

    xml = RE_CAMBIO_FORMATO.sub("", xml)
    partes, desde, pila = [], 0, {"p": [{}], "r": [{}], "ppr": 0}
    for m in RE_ETIQUETA.finditer(xml):
        cierre, nombre, atributos = m.groups()
        if nombre != "t":
            _seguir(pila, cierre, nombre, atributos)
        elif not cierre and not atributos.endswith("/"):
            fin = xml.find("</w:t>", m.end())
            texto = xml[m.end() : fin]
            if texto != texto.upper() and _caps_efectivo(pila, estilos, defecto):
                partes += [
                    xml[desde : m.end()],
                    escape(unescape(texto).upper(), quote=False),
                ]
                desde = fin
    return "".join(partes) + xml[desde:]


def _docx(p: Path) -> str:
    """Se lee el XML en crudo y no con python-docx porque `document.paragraphs`
    no entra a los cuadros de texto (w:txbxContent) ni a los encabezados. En este
    caso real ahi vivia una nota al notario con una errata («CONSTACIA») que se
    perdia entera."""
    import zipfile
    from html import unescape

    lineas = []
    with zipfile.ZipFile(p) as z:
        estilos, defecto = _estilos_caps(z)
        nombres = sorted(
            (n for n in z.namelist() if PARTES_DOCX.fullmatch(n)),
            key=lambda n: (n != "word/document.xml", n),
        )
        for n in nombres:
            xml = _con_mayusculas(z.read(n).decode("utf-8", "ignore"), estilos, defecto)
            xml = RE_TAB.sub("<w:t>  </w:t>", RE_FALLBACK.sub("", xml))
            # F27: dentro de una tabla, cada fila es una linea con sus celdas
            # separadas por dos espacios, como ocr_lineas; una tabla anidada se
            # aplana dentro de su celda. Fuera de tablas, un parrafo por linea.
            # El texto antes de otra marca (un cuadro de texto con tabla dentro
            # de un parrafo) sigue en el parrafo hasta su </w:p>.
            nivel, inicio, t, celda, celdas = 0, 0, "", [], []
            for m in RE_DOCX_MARCA.finditer(xml):
                # el grupo opcional exige espacio tras "w:t": sin eso <w:tab .../>
                # entra como si abriera un <w:t> y se arrastra el XML crudo
                t += unescape("".join(RE_WT.findall(xml, inicio, m.start())))
                inicio = m.end()
                marca = m.group()
                if marca == "</w:p>" or marca.startswith(("<w:br", "<w:cr")):
                    if t.strip():
                        (celda if nivel else lineas).append(t)
                    t = ""
                elif marca == "</w:tbl>":
                    nivel -= 1
                elif marca.startswith("<w:tbl"):
                    nivel += 1
                elif nivel == 1 and marca == "</w:tc>":
                    celdas.append(" ".join(celda))
                    celda = []
                elif nivel == 1 and marca == "</w:tr>":
                    if fila := "  ".join(c for c in celdas if c.strip()):
                        lineas.append(fila)
                    celdas = []
    return "\n".join(lineas)


def leer(p: Path) -> str:
    """Texto plano de cualquier formato soportado. Cachea lo que pasa por OCR."""
    return leer_con_calidad(p)["texto"]


def leer_paginas(p: Path) -> tuple[str, ...]:
    """Devuelve una página lógica por elemento y conserva el cache de OCR."""
    return tuple(pagina["texto"] for pagina in _leer_informes(p))


def leer_con_calidad(p: Path) -> dict:
    paginas = _leer_informes(p)
    return {
        "texto": SEPARADOR_PAGINA.join(pagina["texto"] for pagina in paginas),
        "calidad": {
            "version": calidad_ocr.VERSION,
            "paginas": [
                {"pagina": i, **{k: v for k, v in pagina.items() if k != "texto"}}
                for i, pagina in enumerate(paginas, 1)
            ],
        },
    }


def _leer_informes(p):
    s = p.suffix.lower()
    p = p.resolve(strict=True)
    if s == ".docx":
        return (_informe_nativo(_docx(p), "texto_nativo"),)
    if s in LEGACY:
        return (_informe_nativo(_legacy(p), "texto_nativo"),)
    if s == ".xlsx":
        return (_informe_nativo(_xlsx(p), "texto_nativo"),)
    if s == ".pdf":
        paginas = _cacheado(p.read_bytes(), lambda: list(_pdf_informe(p)))
        if isinstance(paginas, str):
            paginas = [paginas]
        return tuple(
            _informe_nativo(pg, "historico", ["calidad_no_disponible"])
            if isinstance(pg, str)
            else pg
            for pg in paginas
        )
    if s in IMGS:
        pagina = _cacheado(p.read_bytes(), lambda: ocr_informe(p))
        if isinstance(pagina, str):
            pagina = _informe_nativo(pagina, "historico", ["calidad_no_disponible"])
        return (pagina,)
    if s in {".xls", ".ppt"}:
        raise ValueError(f"{p.name}: formato binario antiguo, guardalo como .{s[1:]}x")
    texto = p.read_text(encoding="utf-8", errors="replace")
    return (
        _informe_nativo(
            texto, "texto_nativo", ["caracteres_invalidos"] if "\ufffd" in texto else []
        ),
    )


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
