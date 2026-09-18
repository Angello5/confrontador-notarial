"""Caracterización ficticia de reglas que reciben texto o estructuras."""

import subprocess
import sys
from pathlib import Path

import pytest

NUCLEO = Path(__file__).resolve().parents[1] / "nucleo"


def test_reglas_reciben_texto_sintetico():
    from nucleo.lexico import contar, erratas
    from nucleo.ortografia import plano
    from nucleo.verificar import nombre_reniec, nombres, norm

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
    codigo = "\n".join(
        (
            "import builtins, importlib, os, sys",
            f"[importlib.import_module(m) for m in {modulos.split()!r}]",
            "prohibidos = {'adaptadores', 'extraer', 'rapidocr', 'onnxruntime', 'urllib.request', 'pathlib'}",
            "assert not (prohibidos & sys.modules.keys()), prohibidos & sys.modules.keys()",
            "def deny(*args, **kwargs):",
            "    raise AssertionError('acceso a archivos')",
            "builtins.open = os.open = deny",
            "from nucleo.verificar import norm",
            "from nucleo.lexico import contar, erratas",
            "from nucleo.ortografia import plano",
            "assert norm('LÍNEA Ñ') == 'LINEA N'",
            "assert erratas('OCTAO', contar(['OCTAVO']))[0][1] == 'OCTAVO'",
            "assert plano('ACCIÓN') == 'accion'",
        )
    )
    resultado = subprocess.run(  # noqa: S603 proceso local con intérprete y script de test fijos, sin shell ni entrada externa
        [sys.executable, "-c", codigo], capture_output=True, text=True
    )
    assert resultado.returncode == 0, resultado.stderr
