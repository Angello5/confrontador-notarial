from pathlib import Path

import pytest

from experimental.ocr_benchmark import (
    ENGINE_SPECS,
    benchmark,
    error_rate,
    render_pages,
    read_reference,
)


@pytest.mark.ocr_research
def test_engine_catalogue_has_requested_ocr_variants():
    assert tuple(ENGINE_SPECS) == (
        "paddleocr-v4",
        "paddleocr-v5",
        "paddleocr-v6",
        "liteparse",
    )


@pytest.mark.ocr_research
def test_benchmark_runs_each_page_and_measures_core_catalogue(tmp_path):
    pages = (tmp_path / "page-1.png", tmp_path / "page-2.png")
    for page in pages:
        page.write_bytes(b"synthetic page")

    textos = {
        pages[0].name: "ALBA ZURBELIA LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000001.",
        pages[1].name: "PARTIDA ELECTRONICA N° 80000001. MONTO S/ 12,345.67.",
    }

    def factory(engine_id):
        return lambda path: textos[Path(path).name]

    resultados = benchmark(pages, ("paddleocr-v5",), factory=factory)

    assert len(resultados) == 1
    resultado = resultados[0]
    assert resultado.error is None
    assert resultado.paginas == 2
    assert resultado.caracteres == sum(len(texto) for texto in textos.values())
    assert resultado.catalogo == {
        "personas": 1,
        "nombres": 1,
        "documentos": 1,
        "partidas": 1,
        "montos": 1,
    }
    assert resultado.tiempo_total >= 0
    assert resultado.tiempo_preparacion >= 0


@pytest.mark.ocr_research
def test_one_engine_failure_does_not_hide_other_results(tmp_path):
    page = tmp_path / "page.png"
    page.write_bytes(b"synthetic page")

    def factory(engine_id):
        if engine_id == "paddleocr-v4":
            raise RuntimeError("dependencia ausente")
        return lambda _path: "texto ficticio"

    resultados = benchmark(
        (page,),
        ("paddleocr-v4", "liteparse"),
        factory=factory,
    )

    assert resultados[0].error == "dependencia ausente"
    assert resultados[1].error is None
    assert resultados[1].caracteres == len("texto ficticio")


@pytest.mark.ocr_research
def test_error_rate_returns_cer_and_wer_against_reference():
    metrics = error_rate("DNI 90000001\nALBA", "DNI 90000002\nALBA")

    assert metrics == {"cer": pytest.approx(1 / 17), "wer": pytest.approx(1 / 3)}


@pytest.mark.ocr_research
def test_error_rate_is_unavailable_without_reference():
    assert error_rate("texto", "") == {"cer": None, "wer": None}


@pytest.mark.ocr_research
def test_render_pages_creates_one_png_per_pdf_page(tmp_path):
    pymupdf = pytest.importorskip("pymupdf")
    origen = tmp_path / "entrada.pdf"
    with pymupdf.open() as documento:
        documento.new_page()
        documento.new_page()
        documento.save(origen)

    paginas = render_pages(origen, tmp_path / "pages")

    assert len(paginas) == 2
    assert all(p.suffix == ".png" and p.stat().st_size > 0 for p in paginas)


@pytest.mark.ocr_research
def test_read_reference_extracts_fictional_docx():
    referencia = Path(__file__).parent / "tests" / "fixtures" / "cliente" / "minuta.docx"

    texto = read_reference(referencia)

    assert "ALBA ZURBELIA LUMARIA" in texto
