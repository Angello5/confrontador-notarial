"""Comprueba la barrera de datos privados sin usar expedientes reales."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

RAIZ = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "args,ci,codigo",
    [
        (["--collect-only"], False, 5),
        (["-o", "addopts=", "--collect-only"], False, 5),
        (["-o", "addopts=", "-m", "local_reference"], True, 4),
        (["-o", "addopts=", "-m", "local_reference or otro"], True, 4),
        (
            [
                "-o",
                "addopts=",
                "-m",
                "local_reference",
                "--showlocals",
                "--tb=long",
                "-s",
            ],
            False,
            1,
        ),
    ],
)
def test_seleccion_privada(args, ci, codigo, tmp_path):
    env = dict(os.environ)
    for clave in (
        "CI",
        "PYTEST_ADDOPTS",
        "COV_CORE_SOURCE",
        "COV_CORE_CONFIG",
        "COV_CORE_DATAFILE",
    ):
        env.pop(clave, None)
    if ci:
        env["CI"] = "true"
    # El centinela detecta incluso exposición de una ruta por un traceback.
    env["EXPEDIENTES_REFERENCIA_DIR"] = str(tmp_path / "CENTINELA_PRIVACIDAD")
    resultado = subprocess.run(  # noqa: S603 intérprete propio y argumentos de prueba fijos, sin shell
        [sys.executable, "-m", "pytest", "tests/test_referencia_local.py", "-q", *args],
        cwd=RAIZ,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert resultado.returncode == codigo, resultado.stdout + resultado.stderr
    assert "CENTINELA_PRIVACIDAD" not in resultado.stdout + resultado.stderr
    if codigo == 1:
        assert "Expediente local ausente o incompleto." in resultado.stdout
