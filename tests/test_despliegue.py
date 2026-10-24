"""F8: lo que el despliegue en Windows añade al ERP, con datos ficticios."""

import importlib
import os
import shutil
import subprocess
from datetime import timedelta
from pathlib import Path

import pytest
from django.urls import reverse
from django.utils import timezone

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts" / "windows"


def _settings(monkeypatch, **entorno):
    from config import settings

    for nombre, valor in entorno.items():
        if valor is None:
            monkeypatch.delenv(nombre, raising=False)
        else:
            monkeypatch.setenv(nombre, str(valor))
    return importlib.reload(settings)


@pytest.fixture
def recargar(monkeypatch):
    from config import settings

    yield lambda **entorno: _settings(monkeypatch, **entorno)
    monkeypatch.undo()
    importlib.reload(settings)


def test_registros_rotan_por_rol_solo_con_carpeta(recargar, tmp_path):
    con = recargar(ERP_REGISTROS_DIR=tmp_path, ERP_ROL="worker")
    archivo = con.LOGGING["handlers"]["archivo"]
    assert archivo["class"] == "logging.handlers.RotatingFileHandler"
    assert Path(archivo["filename"]) == tmp_path / "worker.log"
    assert (archivo["maxBytes"], archivo["backupCount"]) == (5 * 1024 * 1024, 10)
    assert con.LOGGING["root"]["handlers"] == ["archivo"]

    sin = recargar(ERP_REGISTROS_DIR=None)
    assert "handlers" not in sin.LOGGING


def test_static_root_y_estado_se_configuran_en_el_servidor(recargar, tmp_path):
    con = recargar(ERP_STATIC_ROOT=tmp_path / "estaticos", ERP_ESTADO_DIR=tmp_path)
    assert (con.STATIC_ROOT, con.ERP_ESTADO_DIR) == (tmp_path / "estaticos", tmp_path)

    sin = recargar(ERP_STATIC_ROOT=None, ERP_ESTADO_DIR=None)
    assert sin.STATIC_ROOT == sin.BASE_DIR / "staticfiles"
    assert sin.ERP_ESTADO_DIR is None


@pytest.mark.parametrize("script", sorted(SCRIPTS.glob("*.ps1")), ids=lambda p: p.name)
def test_los_scripts_de_windows_no_tienen_errores_de_sintaxis(script):
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if not powershell:
        pytest.skip("PowerShell no está instalado")
    analisis = (
        "$e = $null; [void][System.Management.Automation.Language.Parser]::ParseFile("
        f"'{script}', [ref]$null, [ref]$e); $e | ForEach-Object {{ $_.Message }}"
    )
    salida = subprocess.run(  # noqa: S603 PowerShell del sistema, solo analiza scripts del repo, sin shell
        [powershell, "-NoProfile", "-NonInteractive", "-Command", analisis],
        capture_output=True,
        text=True,
        check=True,
    )
    assert salida.stdout.strip() == ""


@pytest.mark.django_db
def test_el_worker_deja_latido_solo_si_hay_carpeta_de_estado(settings, tmp_path):
    from expedientes.management.commands.procesar_documentos import Command

    settings.ERP_ESTADO_DIR = None
    Command().procesar_vuelta()
    assert list(tmp_path.iterdir()) == []

    settings.ERP_ESTADO_DIR = tmp_path
    Command().procesar_vuelta()
    latido = tmp_path / "worker.latido"
    assert timezone.now().timestamp() - latido.stat().st_mtime < 60


def _estado(directorio, ahora, latido_hace, respaldo_hace, vence_en):
    latido = directorio / "worker.latido"
    latido.touch()
    marca = (ahora - latido_hace).timestamp()
    os.utime(latido, (marca, marca))
    (directorio / "respaldo.ok").write_text(
        (ahora - respaldo_hace).isoformat(), encoding="utf-8"
    )
    (directorio / "certificado.vence").write_text(
        (ahora + vence_en).date().isoformat(), encoding="utf-8"
    )


def test_sin_carpeta_de_estado_no_hay_avisos(settings):
    from expedientes.services import avisos_sistema

    settings.ERP_ESTADO_DIR = None
    assert avisos_sistema() == []


def test_todo_al_dia_no_avisa(settings, tmp_path):
    from expedientes.services import avisos_sistema

    settings.ERP_ESTADO_DIR = tmp_path
    ahora = timezone.now()
    _estado(
        tmp_path, ahora, timedelta(minutes=2), timedelta(hours=25), timedelta(days=31)
    )
    assert avisos_sistema(ahora) == []


def test_avisa_cada_condicion_en_lenguaje_llano(settings, tmp_path):
    from expedientes.services import avisos_sistema

    settings.ERP_ESTADO_DIR = tmp_path
    ahora = timezone.now()
    _estado(
        tmp_path, ahora, timedelta(minutes=11), timedelta(hours=27), timedelta(days=30)
    )
    vence = (ahora + timedelta(days=30)).date().strftime("%d/%m/%Y")
    assert avisos_sistema(ahora) == [
        "El procesamiento de documentos no está activo. Avise al encargado de sistemas.",
        "El respaldo de anoche no se completó. Avise al encargado de sistemas.",
        f"El certificado de seguridad vence el {vence}. Avise al encargado de sistemas.",
    ]


def test_un_archivo_ausente_o_ilegible_cuenta_como_fallo(settings, tmp_path):
    from expedientes.services import avisos_sistema

    settings.ERP_ESTADO_DIR = tmp_path
    (tmp_path / "respaldo.ok").write_text("no es una fecha", encoding="utf-8")
    avisos = avisos_sistema()
    assert len(avisos) == 3
    assert all("Avise al encargado de sistemas." in aviso for aviso in avisos)
    assert not any(str(tmp_path) in aviso or ".ok" in aviso for aviso in avisos)


def test_un_error_del_servidor_se_explica_en_espanol(rf):
    from django.views.defaults import server_error

    respuesta = server_error(rf.get("/"))
    assert respuesta.status_code == 500
    assert "El sistema no está disponible" in respuesta.content.decode()


@pytest.mark.django_db
def test_solo_el_inicio_del_administrador_muestra_los_avisos(
    client, settings, tmp_path, administrador_ficticio, usuario_ficticio
):
    settings.ERP_ESTADO_DIR = tmp_path
    aviso = "El procesamiento de documentos no está activo"

    client.force_login(administrador_ficticio)
    assert aviso in client.get(reverse("home")).content.decode()

    client.force_login(usuario_ficticio)
    assert aviso not in client.get(reverse("home")).content.decode()
