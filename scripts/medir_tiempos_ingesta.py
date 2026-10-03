"""Mide tiempos de ingesta por tipo de documento y variantes de OCR.

Uso:
    .venv/Scripts/python.exe scripts/medir_tiempos_ingesta.py

Genera documentos ficticios en .venv/ocr-tiempos/ (TXT, DOCX, RTF, PDF con
texto, PDF escaneado, foto JPEG, página girada, inclinada, en blanco y capa
corrupta), mide la extracción completa sin caché y compara variantes del OCR
en tiempo y exactitud. Escribe solo métricas en docs/ocr-tiempos.json.
No contacta la red. Los tiempos dependen del equipo; no es un ensayo aislado.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import platform
import random
import statistics
import sys
import tempfile
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageFilter
from rapidfuzz.distance import Levenshtein

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from adaptadores import calidad_ocr, extraccion  # noqa: E402

OUT = ROOT / ".venv" / "ocr-tiempos"
RESULTADO = ROOT / "docs" / "ocr-tiempos.json"
SILABAS = ["AL", "BA", "ZUR", "BE", "LIA", "LU", "MA", "RIA", "TO", "NE", "QUI", "SO"]


# ── Documentos ficticios ─────────────────────────────────────────────────────


def _nombre(rng):
    return " ".join(
        "".join(rng.choice(SILABAS) for _ in range(rng.randint(2, 3))) for _ in range(3)
    )


def pagina_ficticia(semilla, lineas=42):
    """Texto de una página A4 con datos verificables (todos ficticios)."""
    rng = random.Random(semilla)  # noqa: S311 datos ficticios reproducibles, no criptografía
    texto, campos = [], []
    for i in range(lineas):
        if i % 6 == 0:
            dni = f"9{rng.randint(0, 9999999):07d}"
            linea = f"COMPARECE {_nombre(rng)}, IDENTIFICADO CON DNI N. {dni},"
            campos.append(dni)
        elif i % 6 == 3:
            monto = f"{rng.randint(1000, 999999):,}.{rng.randint(0, 99):02d}"
            linea = f"POR EL PRECIO DE S/ {monto} QUE DECLARA HABER RECIBIDO,"
            campos.append(monto)
        else:
            linea = " ".join(
                rng.choice(
                    "EL LA DE QUE EN Y CON POR PARA SU INMUEBLE PARTIDA "
                    "REGISTRAL VENDEDOR COMPRADOR CLAUSULA OTORGA ESCRITURA "
                    "NOTARIAL MINUTA SENOR SENORA PRESENTE".split()
                )
                for _ in range(rng.randint(7, 10))
            )
        texto.append(linea)
    return texto, campos


def pdf_nativo(paginas, destino):
    doc = pymupdf.open()
    for lineas in paginas:
        pg = doc.new_page(width=595, height=842)
        for i, linea in enumerate(lineas):
            pg.insert_text((50, 60 + i * 17.5), linea, fontsize=9.5, fontname="tiro")
    doc.save(destino)
    doc.close()


def escaneo(lineas, giro=0.0, contraste=1.0, dpi=300, semilla=0):
    """Rasteriza el texto como haría un escáner, con ruido y compresión."""
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "p.pdf"
        pdf_nativo([lineas], ruta)
        with pymupdf.open(ruta) as d:
            pix = d[0].get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
            img = Image.frombytes("L", (pix.width, pix.height), pix.samples)
    rng = np.random.default_rng(semilla)
    arr = np.asarray(img, dtype=np.float32)
    arr = 255 - (255 - arr) * contraste
    arr = np.clip(arr + rng.normal(0, 9, arr.shape), 0, 255).astype(np.uint8)
    img = Image.fromarray(arr).filter(ImageFilter.GaussianBlur(0.6))
    if giro:
        img = img.rotate(giro, expand=giro % 90 == 0, fillcolor=255)
    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, format="JPEG", quality=70)
    return buffer.getvalue()


def pdf_escaneado(imagenes, destino):
    doc = pymupdf.open()
    for jpg in imagenes:
        with Image.open(io.BytesIO(jpg)) as img:
            ancho, alto = img.size
        horizontal = ancho > alto
        pg = doc.new_page(
            width=842 if horizontal else 595, height=595 if horizontal else 842
        )
        pg.insert_image(pg.rect, stream=jpg)
    doc.save(destino)
    doc.close()


def pdf_capa_corrupta(lineas, destino):
    """Imagen legible con capa de texto basura (caracteres de control)."""
    pdf_escaneado([escaneo(lineas)], destino)
    with pymupdf.open(destino) as doc:
        doc[0].insert_text((50, 30), "\x01\x02 �" * 30, fontsize=4, render_mode=3)
        doc.saveIncr()


def docx(lineas, destino):
    cuerpo = "".join(
        f"<w:p><w:r><w:t>{linea.replace('&', '&amp;')}</w:t></w:r></w:p>"
        for linea in lineas
    )
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    with zipfile.ZipFile(destino, "w") as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/'
            'package/2006/content-types"><Default Extension="rels" ContentType='
            '"application/vnd.openxmlformats-package.relationships+xml"/><Default '
            'Extension="xml" ContentType="application/xml"/><Override PartName='
            '"/word/document.xml" ContentType="application/vnd.openxmlformats-'
            'officedocument.wordprocessingml.document.main+xml"/></Types>',
        )
        z.writestr(
            "_rels/.rels",
            '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats'
            '.org/package/2006/relationships"><Relationship Id="r1" Type="http://'
            "schemas.openxmlformats.org/officeDocument/2006/relationships/"
            'officeDocument" Target="word/document.xml"/></Relationships>',
        )
        z.writestr(
            "word/document.xml",
            f'<?xml version="1.0"?><w:document xmlns:w="{w}"><w:body>{cuerpo}'
            "</w:body></w:document>",
        )


def rtf(lineas, destino):
    destino.write_text(
        "{\\rtf1\\ansi " + "\\par ".join(lineas) + "}",
        encoding="ascii",
        errors="replace",
    )


# ── Medición de punta a punta ────────────────────────────────────────────────


def _exactitud(texto, lineas, campos):
    plano = " ".join(texto.split()).upper()
    referencia = " ".join(" ".join(lineas).split()).upper()
    return {
        "similitud": round(Levenshtein.normalized_similarity(plano, referencia), 4),
        "campos_exactos": sum(c in plano for c in campos),
        "campos_posibles": len(campos),
    }


def generar(carpeta):
    paginas = [pagina_ficticia(s) for s in range(12)]
    lineas, campos = paginas[0]
    casos = []

    def caso(nombre, archivo, refs, descripcion):
        casos.append(
            {
                "caso": nombre,
                "archivo": archivo,
                "refs": refs,
                "descripcion": descripcion,
            }
        )

    (carpeta / "texto.txt").write_text("\n".join(lineas), encoding="utf-8")
    caso("txt", "texto.txt", [paginas[0]], "Texto plano")
    docx(lineas, carpeta / "minuta.docx")
    caso("docx", "minuta.docx", [paginas[0]], "Word moderno")
    rtf(lineas, carpeta / "antiguo.rtf")
    caso(
        "rtf_libreoffice",
        "antiguo.rtf",
        [paginas[0]],
        "Formato antiguo vía LibreOffice",
    )
    pdf_nativo([paginas[0][0]], carpeta / "nativo-1.pdf")
    caso("pdf_texto_1p", "nativo-1.pdf", paginas[:1], "PDF con capa de texto, 1 página")
    pdf_nativo([p[0] for p in paginas[:10]], carpeta / "nativo-10.pdf")
    caso(
        "pdf_texto_10p",
        "nativo-10.pdf",
        paginas[:10],
        "PDF con capa de texto, 10 páginas",
    )
    pdf_escaneado([escaneo(lineas)], carpeta / "escaneo-1.pdf")
    caso(
        "pdf_escaneado_1p",
        "escaneo-1.pdf",
        paginas[:1],
        "PDF escaneado limpio, 1 página",
    )
    pdf_escaneado(
        [escaneo(p[0], semilla=i) for i, p in enumerate(paginas[:10])],
        carpeta / "escaneo-10.pdf",
    )
    caso(
        "pdf_escaneado_10p",
        "escaneo-10.pdf",
        paginas[:10],
        "PDF escaneado limpio, 10 páginas",
    )
    foto = escaneo(lineas, dpi=420)
    (carpeta / "foto.jpg").write_bytes(foto)
    caso("foto_jpg", "foto.jpg", paginas[:1], "Foto JPEG de 12 MP")
    pdf_escaneado([escaneo(lineas, giro=4)], carpeta / "inclinada.pdf")
    caso("pdf_inclinado_4", "inclinada.pdf", paginas[:1], "Escaneo inclinado 4°")
    pdf_escaneado([escaneo(lineas, contraste=0.35)], carpeta / "tenue.pdf")
    caso("pdf_bajo_contraste", "tenue.pdf", paginas[:1], "Escaneo de bajo contraste")
    pdf_escaneado([escaneo(lineas, giro=180)], carpeta / "girada-180.pdf")
    caso("pdf_girado_180", "girada-180.pdf", paginas[:1], "Página escaneada al revés")
    pdf_escaneado([escaneo(lineas, giro=90)], carpeta / "girada-90.pdf")
    caso("pdf_girado_90", "girada-90.pdf", paginas[:1], "Página escaneada de lado")
    pdf_escaneado([escaneo([" "])], carpeta / "blanco.pdf")
    caso("pdf_pagina_blanca", "blanco.pdf", [([], [])], "Página en blanco")
    pdf_capa_corrupta(lineas, carpeta / "capa-corrupta.pdf")
    caso(
        "pdf_capa_corrupta", "capa-corrupta.pdf", paginas[:1], "Capa de texto corrupta"
    )
    return casos, paginas


def medir_casos(carpeta, casos, repeticiones):
    filas = []
    for c in casos:
        ruta = carpeta / c["archivo"]
        tiempos = []
        for _ in range(repeticiones):
            # Caché vacía en cada repetición: se mide el primer procesamiento.
            with tempfile.TemporaryDirectory() as cache:
                extraccion.CACHE = Path(cache)
                inicio = time.perf_counter()
                try:
                    with contextlib.redirect_stderr(io.StringIO()):
                        salida = extraccion.leer_con_calidad(ruta)
                except ValueError as exc:
                    salida = None
                    error = str(exc).split(":")[-1].strip()
                tiempos.append(time.perf_counter() - inicio)
        fila = {
            "caso": c["caso"],
            "descripcion": c["descripcion"],
            "paginas": len(c["refs"]),
            "segundos": round(statistics.median(tiempos), 3),
            "segundos_por_pagina": round(
                statistics.median(tiempos) / len(c["refs"]), 3
            ),
        }
        if salida is None:
            fila["error"] = error
        else:
            calidad = salida["calidad"]["paginas"]
            fila["metodos"] = sorted({p["metodo"] for p in calidad})
            fila["lecturas_ocr"] = sum(p.get("intentos", 0) for p in calidad)
            fila["requiere_revision"] = sum(p["requiere_revision"] for p in calidad)
            lineas = [x for xs, _ in c["refs"] for x in xs]
            campos = [x for _, cs in c["refs"] for x in cs]
            fila |= _exactitud(salida["texto"], lineas, campos)
        filas.append(fila)
        print(json.dumps(fila, ensure_ascii=False), flush=True)
    return filas


# ── Variantes del OCR sobre páginas escaneadas ───────────────────────────────


def motor(hilos=-1, lote=6, lado_max=2000, arena=False):
    from rapidocr import RapidOCR

    rutas = {n: extraccion.OCR_MODELS / n for n in extraccion._OCR_FILES}
    return RapidOCR(
        params={
            "Global.use_cls": False,
            "Global.log_level": "error",
            "Global.max_side_len": lado_max,
            "EngineConfig.onnxruntime.intra_op_num_threads": hilos,
            "EngineConfig.onnxruntime.enable_cpu_mem_arena": arena,
            "Det.model_path": str(rutas["ch_PP-OCRv5_mobile_det.onnx"]),
            "Rec.model_path": str(rutas["latin_PP-OCRv5_rec_mobile_infer.onnx"]),
            "Rec.rec_batch_num": lote,
        }
    )


def _render(pdf, i, dpi, formato):
    with pymupdf.open(pdf) as doc:
        pix = doc[i].get_pixmap(dpi=dpi)
    if formato == "png":
        return pix.tobytes("png")
    arr = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)
    return np.ascontiguousarray(arr[:, :, ::-1])


VARIANTES = {
    "actual": {},
    "dpi_170": {"dpi": 170},
    "dpi_150": {"dpi": 150},
    "sin_png": {"formato": "array"},
    "lote_rec_16": {"lote": 16},
    "lado_max_1600": {"lado_max": 1600},
    "hilos_4": {"hilos": 4},
    "hilos_8": {"hilos": 8},
    "combinada": {"dpi": 170, "formato": "array", "lote": 16},
    "arena": {"arena": True},
    "arena_sin_png": {"arena": True, "formato": "array"},
}


def medir_variantes(paginas, nombres, evaluar, rondas=2):
    """Tiempo por página de cada variante; `evaluar` resume la exactitud.

    Las variantes se alternan en orden aleatorio dentro de cada página y se
    repiten, para que la temperatura o el modo de energía del equipo no
    favorezcan a la que se mide primero.
    """
    configs, motores, carga = {}, {}, {}
    for nombre in nombres:
        v = {"dpi": 200, "formato": "png", "hilos": -1, "lote": 6, "lado_max": 2000}
        v = configs[nombre] = v | {"arena": False} | VARIANTES[nombre]
        inicio = time.perf_counter()
        motores[nombre] = motor(v["hilos"], v["lote"], v["lado_max"], v["arena"])
        motores[nombre](_render(*paginas[0], v["dpi"], v["formato"]))
        carga[nombre] = time.perf_counter() - inicio
    medidas = {n: [[] for _ in paginas] for n in nombres}
    etapas = {n: [None] * len(paginas) for n in nombres}
    textos = {n: [None] * len(paginas) for n in nombres}
    orden = random.Random(31)  # noqa: S311 orden de medición reproducible
    for _ in range(rondas):
        for k, (pdf, i) in enumerate(paginas):
            for nombre in orden.sample(nombres, len(nombres)):
                v = configs[nombre]
                t0 = time.perf_counter()
                entrada = _render(pdf, i, v["dpi"], v["formato"])
                t1 = time.perf_counter()
                salida = motores[nombre](entrada)
                texto = calidad_ocr.resumir(salida)["texto"]
                medidas[nombre][k].append((time.perf_counter() - t0, t1 - t0))
                lista = list(salida.elapse_list or []) + [None] * 3
                cajas = 0 if salida.boxes is None else len(salida.boxes)
                etapas[nombre][k] = (lista[0] or 0, lista[2] or 0, cajas)
                textos[nombre][k] = texto
    filas = []
    for nombre in nombres:
        tiempos = [statistics.median(x[0] for x in m) for m in medidas[nombre]]
        render = [statistics.median(x[1] for x in m) for m in medidas[nombre]]
        p90 = (
            statistics.quantiles(tiempos, n=10)[-1] if len(tiempos) > 1 else tiempos[0]
        )
        fila = {
            "variante": nombre,
            "config": configs[nombre],
            "carga_y_primera_pagina": round(carga[nombre], 2),
            "segundos_por_pagina": round(statistics.median(tiempos), 3),
            "p90_por_pagina": round(p90, 3),
            "total": round(sum(tiempos), 2),
            "render_por_pagina": round(statistics.median(render), 3),
            "deteccion_por_pagina": round(
                statistics.median(e[0] for e in etapas[nombre]), 3
            ),
            "reconocimiento_por_pagina": round(
                statistics.median(e[1] for e in etapas[nombre]), 3
            ),
            "cajas_por_pagina": statistics.median(e[2] for e in etapas[nombre]),
        } | evaluar(textos[nombre], textos)
        filas.append(fila)
        print(json.dumps(fila), flush=True)
    return filas


def _ocr_pagina(args):
    pdf, i, hilos = args
    m = _motor_proceso(hilos)
    return calidad_ocr.resumir(m(_render(pdf, i, 200, "png")))["texto"]


_MOTORES = {}


def _motor_proceso(hilos):
    if hilos not in _MOTORES:
        _MOTORES[hilos] = motor(hilos)
    return _MOTORES[hilos]


def medir_paralelo(paginas, configuraciones):
    filas = []
    for procesos, hilos in configuraciones:
        with ProcessPoolExecutor(procesos) as pool:
            list(pool.map(_ocr_pagina, [(*paginas[0], hilos)] * procesos))
            inicio = time.perf_counter()
            list(pool.map(_ocr_pagina, [(pdf, i, hilos) for pdf, i in paginas]))
            total = time.perf_counter() - inicio
        fila = {
            "procesos": procesos,
            "hilos_por_proceso": hilos,
            "paginas": len(paginas),
            "segundos": round(total, 2),
            "segundos_por_pagina": round(total / len(paginas), 3),
        }
        filas.append(fila)
        print(json.dumps(fila), flush=True)
    return filas


def _exactitud_sintetica(refs):
    def evaluar(textos, _):
        exact = [_exactitud(t, ls, cs) for t, (ls, cs) in zip(textos, refs)]
        return {
            "similitud_media": round(statistics.mean(e["similitud"] for e in exact), 4),
            "campos_exactos": sum(e["campos_exactos"] for e in exact),
            "campos_posibles": sum(e["campos_posibles"] for e in exact),
        }

    return evaluar


PRIVADO = ROOT / "expedientes_locales" / "auditoria-20261002"


def _paginas_privadas():
    """Página central no vacía de cada caso; solo rutas e índices."""
    paginas = []
    casos = sorted(d for d in PRIVADO.iterdir() if d.is_dir() and any(d.glob("*.pdf")))
    for caso in casos:
        opciones = []
        for pdf in sorted(caso.glob("*.pdf")):
            previo = pdf.with_suffix(".texto.txt").read_text(encoding="utf-8")
            textos = previo.split(extraccion.SEPARADOR_PAGINA)
            opciones += [(pdf, i) for i, t in enumerate(textos) if t.strip()]
        if opciones:
            paginas.append(opciones[len(opciones) // 2])
    return paginas


def _acuerdo_con_actual(textos, previos):
    """Sin etiquetas humanas: compara contra la lectura actual, no contra la verdad."""
    from nucleo import verificar

    base = previos["actual"]
    campos = {"retenidos": 0, "ausentes": 0, "nuevos": 0}
    for antes, despues in zip(base, textos):
        a = verificar.catalogo({"ficticio.pdf": antes})
        d = verificar.catalogo({"ficticio.pdf": despues})
        for k in ("DNI", "NOMBRE", "PARTIDA", "MONTO"):
            campos["retenidos"] += len(a[k] & d[k])
            campos["ausentes"] += len(a[k] - d[k])
            campos["nuevos"] += len(d[k] - a[k])
    similitud = statistics.mean(
        Levenshtein.normalized_similarity(x, y) for x, y in zip(base, textos)
    )
    return {"similitud_con_actual": round(similitud, 4), "campos_vs_actual": campos}


PRIVADAS = [
    "actual",
    "dpi_170",
    "dpi_150",
    "lote_rec_16",
    "lado_max_1600",
    "hilos_8",
    "combinada",
]


def medir_privado(nombres=None, paralelo=True):
    """Muestra privada: escribe solo agregados bajo expedientes_locales."""
    paginas = _paginas_privadas()
    with contextlib.redirect_stdout(io.StringIO()):
        variantes = medir_variantes(paginas, nombres or PRIVADAS, _acuerdo_con_actual)
        en_paralelo = (
            medir_paralelo(paginas, [(1, -1), (2, 8), (4, 4)]) if paralelo else []
        )
    resultado = {
        "paginas": len(paginas),
        "variantes": variantes,
        "paralelo": en_paralelo,
    }
    destino = PRIVADO / "tiempos"
    destino.mkdir(exist_ok=True)
    nombre = "tiempos_privado.json" if nombres is None else "tiempos_privado_motor.json"
    (destino / nombre).write_text(json.dumps(resultado, indent=2), encoding="utf-8")
    print(json.dumps(resultado, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repeticiones", type=int, default=1)
    ap.add_argument("--solo", choices=["casos", "variantes", "paralelo"])
    ap.add_argument("--privado", action="store_true", help="muestra real local")
    ap.add_argument("--variantes", nargs="+", choices=list(VARIANTES))
    a = ap.parse_args()
    if a.privado:
        return medir_privado(a.variantes, paralelo=not a.variantes)
    OUT.mkdir(parents=True, exist_ok=True)
    casos, paginas = generar(OUT)
    resultado = (
        json.loads(RESULTADO.read_text(encoding="utf-8"))
        if a.solo and RESULTADO.exists()
        else {}
    )
    resultado |= {
        "esquema": 1,
        "nota": "Documentos ficticios; tiempos de este equipo, sin aislamiento.",
        "equipo": {
            "procesador": platform.processor(),
            "nucleos_logicos": os.cpu_count(),
            "sistema": platform.platform(),
            "python": platform.python_version(),
        },
    }
    if a.solo in (None, "casos"):
        resultado["casos"] = medir_casos(OUT, casos, a.repeticiones)
    if a.solo in (None, "variantes"):
        resultado["variantes"] = medir_variantes(
            [(OUT / "escaneo-10.pdf", i) for i in range(4)],
            list(VARIANTES),
            _exactitud_sintetica(paginas[:4]),
        )
    if a.solo in (None, "paralelo"):
        resultado["paralelo"] = medir_paralelo(
            [(OUT / "escaneo-10.pdf", i) for i in range(8)],
            [(1, -1), (2, 8), (4, 4), (8, 2)],
        )
    RESULTADO.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
