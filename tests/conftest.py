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
        esperados = {
            "extraer.py",
            "verificar.py",
            "lexico.py",
            "ortografia.py",
            "nucleo/verificar.py",
            "nucleo/lexico.py",
            "nucleo/ortografia.py",
            "nucleo/__init__.py",
            "nucleo/correccion.py",
            "adaptadores/__init__.py",
            "adaptadores/paginas.py",
            "adaptadores/extraccion.py",
            "adaptadores/calidad_ocr.py",
            "adaptadores/diccionario.py",
            "adaptadores/docx_corregido.py",
            "expedientes/__init__.py",
            "expedientes/apps.py",
            "expedientes/forms.py",
            "expedientes/models.py",
            "expedientes/migrations/0001_initial.py",
            "expedientes/migrations/0002_documento_roles.py",
            "expedientes/migrations/0003_manifiesto_auditoria.py",
            "expedientes/migrations/0004_decisioncorreccion_aplicacion.py",
            "expedientes/migrations/0005_expediente_archivado.py",
            "expedientes/migrations/0006_corrida_origen_presentacion.py",
            "expedientes/migrations/0007_expediente_codigo_activo_unico.py",
            "expedientes/migrations/0008_textoextraido_calidad.py",
            "expedientes/migrations/__init__.py",
            "expedientes/services.py",
            "expedientes/solicitudes.py",
            "expedientes/bloqueos.py",
            "expedientes/migrations/0009_carga_continua.py",
            "expedientes/migrations/0010_rol_recaudos.py",
            "expedientes/urls.py",
            "expedientes/views.py",
            "expedientes/management/__init__.py",
            "expedientes/management/commands/__init__.py",
            "expedientes/management/commands/limpiar_temporales.py",
            "expedientes/management/commands/procesar_documentos.py",
            "expedientes/management/commands/reconstruir_corrida.py",
            "expedientes/management/commands/reextraer_expediente.py",
            "expedientes/management/commands/suprimir_texto_expediente.py",
            "app.py",
            "app_ortografia.py",
            "manage.py",
            "accounts/management/__init__.py",
            "accounts/management/commands/__init__.py",
            "accounts/management/commands/bootstrap_admin.py",
        }
        archivos = {c.attrib["filename"] for c in clases}
        if not {"config/settings.py", "accounts/models.py", "manage.py"} <= archivos:
            raise _CoberturaInvalida
        if not esperados <= archivos or any(
            not (
                nombre in esperados
                or nombre.startswith(("config/", "accounts/", "core/"))
            )
            for nombre in archivos
        ):
            raise _CoberturaInvalida
    except (OSError, ValueError, KeyError, _CoberturaInvalida, ElementTree.ParseError):
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
        terminal = config.pluginmanager.get_plugin("terminalreporter")
        if terminal:
            terminal.write_line(
                "Cobertura no válida: se requiere XML con líneas productivas y rutas relativas.",
                red=True,
            )


@pytest.fixture
def usuario_ficticio(db):
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group

    user = get_user_model().objects.create_user(username="usuario_ficticio")
    user.groups.add(Group.objects.get(name="Usuario"))
    return user


@pytest.fixture
def administrador_ficticio(db):
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group

    user = get_user_model().objects.create_user(
        username="administrador_ficticio",
        is_staff=True,
    )
    user.groups.add(Group.objects.get(name="Administrador"))
    return user
