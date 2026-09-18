"""Comparación explícita, local y sintética de modelos OCR; no corre en suite normal."""

from difflib import SequenceMatcher
from hashlib import sha256
from pathlib import Path
from time import perf_counter

import pytest
from PIL import Image, ImageDraw, ImageFont

pytestmark = pytest.mark.ocr_research

TEXTO = [
    "En Lima, los otorgantes declaran válida la unión y la cesión del inmueble.",
    "La señora Ángela Núñez y el señor José Muñoz acuerdan la transmisión.",
    "El cónyuge manifiesta que recibió información íntegra, clara y verídica.",
    "Partida registral ficticia número 80000001, asiento cinco, sección Ñ.",
    "Documento nacional ficticio DNI 90000004, emitido el día miércoles.",
    "El precio pactado asciende a S/. 150,000.75 (ciento cincuenta mil soles).",
    "Quedó leído, ratificado y firmado; también consta la cláusula de garantía.",
    "ÚLTIMA DISPOSICIÓN: habrá revisión, aprobación y anotación en el registro.",
]

MODELOS = {
    "PP-OCRv4 actual": {
        "rec": "ch_PP-OCRv4_rec_infer.onnx",
        "rec_sha": "48fc40f24f6d2a207a2b1091d3437eb3cc3eb6b676dc3ef9c37384005483683b",
        "keys": "ppocr_keys_v1.txt",
        "keys_sha": "28b2362ad4ab2dc38769aa72feb535e3a9ddb3fd2a7585a05920e6393b1dc7f7",
        "use_cls": True,
    },
    "PP-OCRv5 latin (use_cls=False)": {
        "rec": "latin_PP-OCRv5_rec_mobile_infer.onnx",
        "rec_sha": "b20bd37c168a570f583afbc8cd7925603890efbcdc000a59e22c269d160b5f5a",
        "keys": "ppocrv5_dict.txt",
        "keys_sha": "d1979e9f794c464c0d2e0b70a7fe14dd978e9dc644c0e71f14158cdf8342af1b",
        "use_cls": False,
    },
}


def _render(font_path: Path, dpi: int) -> Image.Image:
    scale = dpi / 200
    font = ImageFont.truetype(str(font_path), round(33 * scale))
    image = Image.new(
        "RGB", (1654 if dpi == 200 else 2480, 2339 if dpi == 200 else 3508), "white"
    )
    draw = ImageDraw.Draw(image)
    for index, line in enumerate(TEXTO):
        draw.text(
            (100 * scale, (220 + index * 210) * scale), line, fill="black", font=font
        )
    return image


def _metrics(raw: str) -> tuple[int, int, int]:
    original = " ".join(raw.split())
    expected_original = " ".join(TEXTO)
    normalized = original.casefold()
    expected = expected_original.casefold()
    expected_words, words = expected.split(), normalized.split()
    word_matches = SequenceMatcher(a=expected_words, b=words, autojunk=False)
    exact_words = sum(size for _, _, size in word_matches.get_matching_blocks())
    special = set("áéíóúüñÁÉÍÓÚÜÑ")
    matcher = SequenceMatcher(a=expected_original, b=original, autojunk=False)
    preserved = sum(
        1
        for a, b, size in matcher.get_matching_blocks()
        for c in expected_original[a : a + size]
        if c in special
    )
    return exact_words, preserved


def _line_count(boxes, dpi: int) -> int:
    ys = sorted(
        sum(point[1] for point in box) / len(box)
        for box in (boxes if boxes is not None else [])
    )
    threshold = 65 * dpi / 200
    lines = []
    for y in ys:
        if not lines or y - lines[-1][-1] > threshold:
            lines.append([y])
        else:
            lines[-1].append(y)
    return len(lines)


def test_modelos_sinteticos_por_fuente_y_dpi():
    """Imprime conteos para transcribir a research.md; no escribe páginas ni OCR."""
    import rapidocr
    from rapidocr import RapidOCR

    model_dir = Path(rapidocr.__file__).parent / "models"
    det_name = "ch_PP-OCRv4_det_infer.onnx"
    det_sha = "d2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9"
    cls_name = "ch_ppocr_mobile_v2.0_cls_infer.onnx"
    cls_sha = "e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c"
    resources = [(det_name, det_sha), (cls_name, cls_sha)]
    for model in MODELOS.values():
        resources.extend(
            [(model["rec"], model["rec_sha"]), (model["keys"], model["keys_sha"])]
        )
    for name, expected_hash in resources:
        path = model_dir / name
        assert (
            path.is_file() and sha256(path.read_bytes()).hexdigest() == expected_hash
        ), name

    fonts = {
        "serif": Path(
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
        ),
        "sans": Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    }
    rows = []
    for model_name, model in MODELOS.items():
        params = {
            "Global.use_cls": model["use_cls"],
            "Global.log_level": "error",
            "Det.model_path": str(model_dir / det_name),
            "Cls.model_path": str(model_dir / cls_name),
            "Rec.model_path": str(model_dir / model["rec"]),
            "Rec.rec_keys_path": str(model_dir / model["keys"]),
        }
        ocr = RapidOCR(params=params)
        keys = (model_dir / model["keys"]).read_text(encoding="utf-8").splitlines()
        has_enye = ("Ñ" in keys, "ñ" in keys)
        for font_name, font_path in fonts.items():
            assert font_path.is_file()
            for dpi in (200, 300):
                image = _render(font_path, dpi)
                start = perf_counter()
                output = ocr(image)
                elapsed = perf_counter() - start
                raw = "\n".join(output.txts or [])
                words, special = _metrics(raw)
                lines = _line_count(output.boxes, dpi)
                rows.append(
                    (
                        model_name,
                        font_name,
                        dpi,
                        lines,
                        words,
                        special,
                        elapsed,
                        has_enye,
                    )
                )
    print("OCR_RESEARCH_ROWS=" + repr(rows))
    assert len(rows) == len(MODELOS) * len(fonts) * 2
