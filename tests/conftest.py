"""Selección privada explícita y validación del informe de cobertura."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest


class _CoberturaInvalida(Exception):
    pass


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
    privados = [item for item in items if item.get_closest_marker("local_reference")]
    if privados and os.environ.get("CI"):
        raise pytest.UsageError("La medición local está prohibida en CI.")
    if privados and config.option.markexpr.strip() != "local_reference":
        items[:] = [item for item in items if item not in privados]
        config.hook.pytest_deselected(items=privados)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    reporte = yield
    if item.get_closest_marker("local_reference"):
        reporte.sections = []
        if reporte.failed:
            reporte.longrepr = "Medición local no aprobada: revisar disponibilidad y resultados localmente."
            if call.excinfo and isinstance(call.excinfo.value, pytest.fail.Exception):
                if str(call.excinfo.value) == "Expediente local ausente o incompleto.":
                    reporte.longrepr = "Expediente local ausente o incompleto."
    return reporte


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    config = session.config
    if not getattr(config.option, "cov_source", None) or config.option.collectonly:
        return
    if getattr(config.option, "no_cov", False):
        return
    ruta = config.option.cov_report.get("xml")
    try:
        if "xml" not in config.option.cov_report:
            raise ValueError("XML requerido")
        raiz = ElementTree.parse(Path(ruta or "coverage.xml")).getroot()  # noqa: S314 artefacto local de confianza generado por coverage
        if raiz.tag != "coverage" or int(raiz.attrib["lines-valid"]) <= 0:
            raise _CoberturaInvalida
        clases = raiz.findall(".//class")
        if not clases or any(Path(c.attrib["filename"]).is_absolute() for c in clases):
            raise _CoberturaInvalida
        if any(
            c.attrib["filename"].startswith(("test_", "tests/", "scripts/"))
            for c in clases
        ):
            raise _CoberturaInvalida
        if {c.attrib["filename"] for c in clases} != {
            "extraer.py",
            "verificar.py",
            "lexico.py",
            "ortografia.py",
            "revisor_llm.py",
            "app.py",
            "app_ortografia.py",
            "bench_llm.py",
        }:
            raise _CoberturaInvalida
    except (OSError, ValueError, KeyError, _CoberturaInvalida, ElementTree.ParseError):
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
        terminal = config.pluginmanager.get_plugin("terminalreporter")
        if terminal:
            terminal.write_line(
                "Cobertura no válida: se requiere XML con líneas productivas y rutas relativas.",
                red=True,
            )
