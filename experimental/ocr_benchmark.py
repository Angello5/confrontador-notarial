"""Benchmark experimental de OCR sobre el mismo núcleo determinista.

Este módulo no cambia el extractor productivo. Normaliza una entrada a páginas
rasterizadas, ejecuta un motor opcional por página y pasa el texto resultante por
``nucleo.verificar.catalogo``. Así la comparación incluye tanto el OCR como el
contrato que consume el confrontador.
"""

from __future__ import annotations

import json
import os
import shutil
import time
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from nucleo.verificar import SEPARADOR_PAGINA, catalogo

OCR_DPI = 200


@dataclass(frozen=True)
class EngineSpec:
    """Descripción visible de un motor, sin importar sus dependencias."""

    id: str
    label: str
    description: str
    warning: str = ""


ENGINE_SPECS: Mapping[str, EngineSpec] = {
    "paddleocr-v4": EngineSpec(
        "paddleocr-v4",
        "PaddleOCR v4",
        "Detector PP-OCRv4 mobile",
        "PP-OCRv4 no ofrece un reconocedor español/latino equivalente en la API actual; se usa el reconocedor latino PP-OCRv5 disponible.",
    ),
    "paddleocr-v5": EngineSpec(
        "paddleocr-v5",
        "PaddleOCR v5",
        "Detector y reconocedor latino PP-OCRv5 mobile",
    ),
    "paddleocr-v6": EngineSpec(
        "paddleocr-v6",
        "PaddleOCR v6",
        "Modelo multilingüe PP-OCRv6 medium con cobertura latina",
    ),
    "liteparse": EngineSpec(
        "liteparse",
        "LiteParse",
        "Parser local con OCR Tesseract en español (spa)",
    ),
}


@dataclass
class BenchmarkResult:
    """Resultado reproducible de un motor para una entrada."""

    engine_id: str
    paginas: int = 0
    caracteres: int = 0
    tiempo_preparacion: float = 0.0
    tiempo_procesamiento: float = 0.0
    tiempo_total: float = 0.0
    textos: tuple[str, ...] = ()
    catalogo: dict[str, int] = field(default_factory=dict)
    cer: float | None = None
    wer: float | None = None
    error: str | None = None


def _normalizar(texto: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", texto).casefold().split())


def _distancia(a: Sequence[str], b: Sequence[str]) -> int:
    """Distancia Levenshtein con memoria lineal."""
    anterior = list(range(len(b) + 1))
    for i, elemento_a in enumerate(a, 1):
        actual = [i]
        for j, elemento_b in enumerate(b, 1):
            actual.append(
                min(
                    actual[-1] + 1,
                    anterior[j] + 1,
                    anterior[j - 1] + (elemento_a != elemento_b),
                )
            )
        anterior = actual
    return anterior[-1]


def error_rate(reconocido: str, referencia: str) -> dict[str, float | None]:
    """Calcula CER y WER; sin referencia no inventa una métrica."""
    referencia_normalizada = _normalizar(referencia)
    if not referencia_normalizada:
        return {"cer": None, "wer": None}
    reconocido_normalizado = _normalizar(reconocido)
    cer = _distancia(list(reconocido_normalizado), list(referencia_normalizada)) / len(
        referencia_normalizada
    )
    palabras_reconocidas = reconocido_normalizado.split()
    palabras_referencia = referencia_normalizada.split()
    wer = _distancia(palabras_reconocidas, palabras_referencia) / len(
        palabras_referencia
    )
    return {"cer": cer, "wer": wer}


def read_reference(origen: Path) -> str:
    """Lee una referencia de texto o Word usando el extractor existente."""
    origen = Path(origen)
    suffix = origen.suffix.lower()
    if suffix in {".txt", ".md"}:
        return origen.read_text(encoding="utf-8", errors="replace")
    if suffix in {".docx", ".doc", ".rtf"}:
        from adaptadores.extraccion import leer

        return leer(origen)
    raise ValueError("La referencia debe ser TXT, MD, DOCX, DOC o RTF")


def _catalogo_metricas(nombre: str, textos: Sequence[str]) -> dict[str, int]:
    resultado = catalogo({nombre: SEPARADOR_PAGINA.join(textos)})
    return {
        "personas": len(resultado.personas),
        "nombres": len(resultado["NOMBRE"]),
        "documentos": len(resultado["DNI"]),
        "partidas": len(resultado["PARTIDA"]),
        "montos": len(resultado["MONTO"]),
    }


def benchmark(
    paginas: Sequence[Path],
    engine_ids: Sequence[str],
    *,
    factory: Callable[[str], Callable[[Path], str]] | None = None,
    referencia: str = "",
    nombre_fuente: str = "benchmark.pdf",
) -> list[BenchmarkResult]:
    """Ejecuta motores independientes y conserva fallos por motor."""
    desconocidos = [engine for engine in engine_ids if engine not in ENGINE_SPECS]
    if desconocidos:
        raise ValueError(f"Motores desconocidos: {', '.join(desconocidos)}")
    factory = factory or make_engine_runner
    resultados = []
    for engine_id in engine_ids:
        runner = None
        inicio = time.perf_counter()
        try:
            runner = factory(engine_id)
            preparacion = time.perf_counter() - inicio
            textos = []
            inicio_proceso = time.perf_counter()
            for pagina in paginas:
                textos.append(runner(Path(pagina)))
            procesamiento = time.perf_counter() - inicio_proceso
            metricas = error_rate(SEPARADOR_PAGINA.join(textos), referencia)
            resultados.append(
                BenchmarkResult(
                    engine_id=engine_id,
                    paginas=len(textos),
                    caracteres=sum(map(len, textos)),
                    tiempo_preparacion=preparacion,
                    tiempo_procesamiento=procesamiento,
                    tiempo_total=time.perf_counter() - inicio,
                    textos=tuple(textos),
                    catalogo=_catalogo_metricas(nombre_fuente, textos),
                    cer=metricas["cer"],
                    wer=metricas["wer"],
                )
            )
        except Exception as exc:  # cada motor debe poder fallar sin ocultar los demás
            resultados.append(
                BenchmarkResult(
                    engine_id=engine_id,
                    tiempo_total=time.perf_counter() - inicio,
                    error=str(exc),
                )
            )
        finally:
            close = getattr(locals().get("runner"), "close", None)
            if close is not None:
                close()
    return resultados


def render_pages(origen: Path, destino: Path) -> tuple[Path, ...]:
    """Convierte PDF o imagen a páginas PNG para una entrada comparable."""
    origen = Path(origen)
    destino.mkdir(parents=True, exist_ok=True)
    if origen.suffix.lower() in {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    }:
        pagina = destino / f"page-001{origen.suffix.lower()}"
        shutil.copyfile(origen, pagina)
        return (pagina,)
    if origen.suffix.lower() != ".pdf":
        raise ValueError("El benchmark acepta PDF e imágenes")

    import pymupdf

    paginas = []
    with pymupdf.open(origen) as documento:
        for numero, pagina in enumerate(documento, 1):
            salida = destino / f"page-{numero:03d}.png"
            pagina.get_pixmap(dpi=OCR_DPI, alpha=False).save(salida)
            paginas.append(salida)
    if not paginas:
        raise ValueError("El documento no tiene páginas")
    return tuple(paginas)


def _prepare_paddle_runtime():
    """Evita la ruta OneDNN/PIR incompatible en este benchmark CPU."""
    os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "False")


def dependency_status(engine_id: str) -> tuple[bool, str]:
    """Indica si el adaptador opcional está instalado, sin inicializar modelos."""
    if engine_id.startswith("paddleocr-"):
        _prepare_paddle_runtime()
        try:
            import paddle  # noqa: F401
            import paddleocr  # noqa: F401
        except ImportError as exc:
            return False, f"Instala PaddlePaddle y PaddleOCR: {exc.name}"
        return True, "PaddlePaddle/PaddleOCR disponibles"
    if engine_id == "liteparse":
        try:
            import liteparse  # noqa: F401
        except ImportError as exc:
            return False, f"Instala liteparse: {exc.name}"
        return True, "LiteParse disponible"
    raise ValueError(f"Motor desconocido: {engine_id}")


def _paddle_result_data(resultado: Any) -> Any:
    if isinstance(resultado, Mapping):
        return resultado
    for atributo in ("json", "to_dict"):
        valor = getattr(resultado, atributo, None)
        if callable(valor):
            valor = valor()
        if isinstance(valor, str):
            try:
                valor = json.loads(valor)
            except json.JSONDecodeError:
                continue
        if isinstance(valor, Mapping):
            return valor
    try:
        return dict(resultado)
    except (TypeError, ValueError):
        return resultado


def _paddle_text(resultados: Sequence[Any]) -> str:
    textos = []
    for resultado in resultados:
        data = _paddle_result_data(resultado)
        if isinstance(data, Mapping):
            valores = data.get("rec_texts") or data.get("texts") or data.get("text")
            if isinstance(valores, str):
                textos.append(valores)
            elif valores:
                textos.extend(str(valor) for valor in valores)
            continue
        if isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
            for fila in data:
                if isinstance(fila, Sequence) and len(fila) >= 2:
                    reconocimiento = fila[1]
                    if isinstance(reconocimiento, Sequence) and reconocimiento:
                        textos.append(str(reconocimiento[0]))
    return "\n".join(textos)


def _paddle_runner(engine_id: str) -> Callable[[Path], str]:
    _prepare_paddle_runtime()
    from paddleocr import PaddleOCR

    common: dict[str, object] = {
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        "use_textline_orientation": False,
    }
    if engine_id == "paddleocr-v4":
        common.update(
            text_detection_model_name="PP-OCRv4_mobile_det",
            text_recognition_model_name="latin_PP-OCRv5_mobile_rec",
        )
    elif engine_id == "paddleocr-v5":
        common.update(
            text_detection_model_name="PP-OCRv5_mobile_det",
            text_recognition_model_name="latin_PP-OCRv5_mobile_rec",
        )
    elif engine_id == "paddleocr-v6":
        common.update(
            text_detection_model_name="PP-OCRv6_medium_det",
            text_recognition_model_name="PP-OCRv6_medium_rec",
        )
    else:
        raise ValueError(f"Motor Paddle desconocido: {engine_id}")
    try:
        ocr = PaddleOCR(**common)
    except Exception as exc:
        raise RuntimeError(f"No se pudo inicializar {engine_id}: {exc}") from exc

    def run(pagina: Path) -> str:
        try:
            return _paddle_text(ocr.predict(input=str(pagina)))
        except AttributeError:
            return _paddle_text(ocr.ocr(str(pagina), cls=False))

    return run


class _LiteParseRunner:
    def __init__(self):
        from liteparse import LiteParse

        self.parser = LiteParse(
            ocr_enabled=True,
            ocr_language="spa",
            output_format="text",
            dpi=OCR_DPI,
            quiet=True,
        )

    def __call__(self, pagina: Path) -> str:
        return self.parser.parse(pagina).text

    def close(self):
        self.parser.close()


def make_engine_runner(engine_id: str) -> Callable[[Path], str]:
    """Construye un adaptador bajo demanda; los modelos no se cargan al importar."""
    if engine_id.startswith("paddleocr-"):
        return _paddle_runner(engine_id)
    if engine_id == "liteparse":
        return _LiteParseRunner()
    raise ValueError(f"Motor desconocido: {engine_id}")
