"""Mide OCR local en imagenes sinteticas reproducibles (no es un benchmark real).

Uso:
    .venv/Scripts/python.exe scripts/medir_ocr_sintetico.py

Genera imagenes ficticias en .venv/ocr-medicion/imagenes y escribe solo
metricas agregadas en docs/ocr-baseline.json. No contacta la red.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import statistics
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
OUT = ROOT / ".venv" / "ocr-medicion"
IMAGES = OUT / "imagenes"
BASELINE = ROOT / "docs" / "ocr-baseline.json"
EXPECTED = {
    "dni": "90000001",
    "nombre": "ALBA ZURBELIA LUMARIA",
    "importe": "12345.67",
}


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default(size=size)


def _base() -> Image.Image:
    image = Image.new("RGB", (1600, 560), "white")
    draw = ImageDraw.Draw(image)
    title = _font(36)
    body = _font(42)
    draw.text(
        (90, 45), "ESCRITURA PUBLICA - DATOS DE REFERENCIA", font=title, fill="#111111"
    )
    draw.text((90, 155), "DNI: 90000001", font=body, fill="#111111")
    draw.text((90, 260), "NOMBRES: ALBA ZURBELIA LUMARIA", font=body, fill="#111111")
    draw.text((90, 365), "IMPORTE: 12345.67", font=body, fill="#111111")
    draw.text(
        (90, 470),
        "Documento de prueba con datos completamente ficticios",
        font=title,
        fill="#111111",
    )
    return image


def _variants() -> dict[str, Image.Image]:
    base = _base()
    skew7 = base.rotate(
        7, resample=Image.Resampling.BICUBIC, expand=True, fillcolor="white"
    )
    skew10 = base.rotate(
        -10, resample=Image.Resampling.BICUBIC, expand=True, fillcolor="white"
    )
    low_contrast = ImageEnhance.Contrast(base).enhance(0.27)
    diagonal = base.copy()
    draw = ImageDraw.Draw(diagonal, "RGBA")
    for offset in range(-600, 1900, 210):
        draw.line((offset, 0, offset + 560, 560), fill=(180, 35, 35, 50), width=5)
    return {
        "limpia": base,
        "inclinada_7_grados": skew7,
        "inclinada_10_grados": skew10,
        "giro_90_grados": base.rotate(90, expand=True),
        "giro_180_grados": base.rotate(180, expand=True),
        "bajo_contraste": low_contrast,
        "marcas_diagonales": diagonal,
    }


def _load_extractor(module_path: Path | None):
    if module_path is None:
        from adaptadores import extraccion

        return extraccion
    # Por defecto se mide una copia congelada, independiente del codigo activo.
    if not module_path.is_file():
        raise FileNotFoundError(f"No existe el snapshot del extractor: {module_path}")
    spec = importlib.util.spec_from_file_location("extraccion_baseline", module_path)
    if spec is None or spec.loader is None:
        raise ImportError("No se pudo cargar el snapshot local del extractor")
    extraccion = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = extraccion
    spec.loader.exec_module(extraccion)
    return extraccion


def _raw_stats(extraccion, path: Path) -> dict:
    result = extraccion._ocr()(str(path))
    boxes = result.boxes if result.boxes is not None else []
    raw_scores = result.scores if result.scores is not None else []
    scores = [float(score) for score in raw_scores]
    angles = []
    for box in boxes:
        (x0, y0), (x1, y1) = box[0], box[1]
        angle = math.degrees(math.atan2(float(y1) - float(y0), float(x1) - float(x0)))
        angles.append((angle + 90) % 180 - 90)
    return {
        "cajas": len(boxes),
        "confianza_media": round(statistics.mean(scores), 4) if scores else None,
        "confianza_minima": round(min(scores), 4) if scores else None,
        "angulo_borde_superior_mediano_grados": (
            round(statistics.median(angles), 2) if angles else None
        ),
        "angulo_borde_superior_rango_grados": (
            [round(min(angles), 2), round(max(angles), 2)] if angles else None
        ),
    }


def _run(module_path: Path | None) -> dict:
    extraccion = _load_extractor(module_path)

    OUT.mkdir(parents=True, exist_ok=True)
    IMAGES.mkdir(parents=True, exist_ok=True)
    results = []
    for case, image in _variants().items():
        path = IMAGES / f"{case}.png"
        image.save(path, format="PNG", optimize=False)
        started = time.perf_counter()
        text = extraccion.ocr_lineas(path)
        elapsed = time.perf_counter() - started
        raw = _raw_stats(extraccion, path)
        results.append(
            {
                "caso": case,
                "campos_exactos": {
                    key: value in text for key, value in EXPECTED.items()
                },
                "campos_correctos": sum(value in text for value in EXPECTED.values()),
                "latencia_ms": round(elapsed * 1000, 2),
                "imagen_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "deteccion_bruta": raw,
            }
        )

    model_digests = {
        name: hashlib.sha256((extraccion.OCR_MODELS / name).read_bytes()).hexdigest()
        for name in extraccion._OCR_FILES
    }
    return {
        "esquema": 1,
        "nota": "Medicion sintetica local; no predice precision en documentos reales.",
        "motor": {
            "rapidocr": extraccion.importlib.metadata.version("rapidocr"),
            "modelos_sha256": model_digests,
            "version_extractor": extraccion.version_extractor(),
        },
        "resumen": {
            "casos": len(results),
            "campos_posibles": len(results) * len(EXPECTED),
            "campos_exactos": sum(r["campos_correctos"] for r in results),
            "latencia_mediana_ms": round(
                statistics.median(r["latencia_ms"] for r in results), 2
            ),
            "latencia_total_ms": round(sum(r["latencia_ms"] for r in results), 2),
        },
        "casos": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--actual",
        action="store_true",
        help="mide adaptadores.extraccion activo (requiere --salida)",
    )
    parser.add_argument(
        "--extractor",
        type=Path,
        default=OUT / "extraccion_baseline.py",
        help="snapshot del adaptador extraccion.py a medir",
    )
    parser.add_argument(
        "--salida",
        type=Path,
        default=BASELINE,
        help="ruta para el JSON agregado",
    )
    args = parser.parse_args()
    if args.actual and args.salida == BASELINE:
        parser.error("--actual requiere --salida para conservar docs/ocr-baseline.json")
    try:
        report = _run(None if args.actual else args.extractor.resolve())
    except Exception as exc:  # Mensaje sin volcar texto OCR ni datos de imagen.
        print(
            f"Medicion OCR no completada: {type(exc).__name__}: {exc}", file=sys.stderr
        )
        return 1
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["resumen"], ensure_ascii=False))
    print(f"Metricas agregadas: {args.salida}")
    print(f"Imagenes ficticias: {IMAGES.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
