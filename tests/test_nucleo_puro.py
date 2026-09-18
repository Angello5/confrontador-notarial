"""Caracterización ficticia de reglas que reciben texto o estructuras."""

import subprocess
import sys
from pathlib import Path

import pytest

NUCLEO = Path(__file__).resolve().parents[1] / "nucleo"


def test_reglas_reciben_texto_sintetico():
    from lexico import contar, erratas
    from ortografia import plano
    from verificar import nombre_reniec, nombres, norm

    assert norm("LÍNEA Ñ") == "LINEA N"
    assert nombres("ALBA ZURBELIA LUMARIA, DE NACIONALIDAD PERUANA") == [
        "ALBA ZURBELIA LUMARIA"
    ]
    assert (
        nombre_reniec(
            "NOMBRES  ALBA\nAPELLIDO PATERNO  ZURBELIA\nAPELLIDO MATERNO  LUMARIA"
        )
        == "ALBA ZURBELIA LUMARIA"
    )
    vocab = contar(["OCTAVO URBANIZACION"])
    assert [(palabra, cerca) for palabra, cerca, _ in erratas("OCTAO", vocab)] == [
        ("OCTAO", "OCTAVO")
    ]
    assert plano("ACCIÓN") == "accion"


@pytest.mark.xfail(
    not NUCLEO.is_dir(), strict=True, reason="T004–T010 aún no crean nucleo/"
)
def test_importar_reglas_no_carga_limites_de_archivos_ocr_o_red():
    modulos = "nucleo.verificar nucleo.lexico nucleo.ortografia"
    codigo = (
        "import importlib, sys; "
        f"[importlib.import_module(m) for m in {modulos.split()!r}]; "
        "prohibidos = {'adaptadores', 'extraer', 'rapidocr', 'onnxruntime', 'urllib.request', 'pathlib'}; "
        "assert not (prohibidos & sys.modules.keys()), prohibidos & sys.modules.keys()"
    )
    resultado = subprocess.run(  # noqa: S603 proceso local con intérprete y script de test fijos, sin shell ni entrada externa
        [sys.executable, "-c", codigo], capture_output=True, text=True
    )
    assert resultado.returncode == 0, resultado.stderr
