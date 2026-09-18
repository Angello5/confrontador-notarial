"""Pruebas ficticias de fronteras y dependencias del núcleo."""

import ast
import importlib
from pathlib import Path

NUCLEO = Path(__file__).resolve().parents[1] / "nucleo"
IMPORTS_PERMITIDOS = {
    "collections",
    "dataclasses",
    "rapidfuzz",
    "re",
    "typing",
    "unicodedata",
}


def _errores_pureza(codigo):
    arbol = ast.parse(codigo)
    errores = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            errores.extend(
                alias.name.split(".")[0]
                for alias in nodo.names
                if alias.name.split(".")[0] not in IMPORTS_PERMITIDOS
            )
        elif isinstance(nodo, ast.ImportFrom):
            raiz = (nodo.module or "").split(".")[0]
            if raiz not in IMPORTS_PERMITIDOS:
                errores.append(raiz or "import relativo")
        elif isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
            if nodo.func.id in {"open", "exec", "eval", "compile", "__import__"}:
                errores.append(nodo.func.id)
    return errores


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


def test_nucleo_solo_importa_lista_blanca_y_no_abre_accesos():
    for archivo in sorted(NUCLEO.glob("*.py")):
        assert not _errores_pureza(archivo.read_text()), archivo.name


def test_guard_ast_detecta_imports_peligrosos_y_diferidos():
    for codigo in (
        "import subprocess",
        "import socket",
        "import shutil",
        "import glob",
        "import http.client",
        "import os",
        "import io",
        "import pathlib",
        "import urllib.request",
        "def fn():\n import pathlib",
        "def fn():\n open('x')",
        "eval('1')",
    ):
        assert _errores_pureza(codigo), codigo


def test_shims_reutilizan_nucleo_y_adaptadores():
    import extraer
    import lexico
    import ortografia
    import verificar
    from adaptadores import extraccion
    from nucleo import lexico as nucleo_lexico, ortografia as nucleo_ortografia
    from nucleo import verificar as nucleo_verificar

    assert extraer.leer is extraccion.leer
    assert extraer.IMGS is nucleo_verificar.IMGS
    assert lexico.contar is nucleo_lexico.contar
    assert verificar.catalogo is nucleo_verificar.catalogo
    assert ortografia._revisar is nucleo_ortografia.revisar


def test_apps_declaran_imports_de_nuevos_modulos_sin_ejecutar_streamlit():
    raiz = NUCLEO.parent
    for nombre in ("app.py", "app_ortografia.py"):
        arbol = ast.parse((raiz / nombre).read_text())
        nodos = [n for n in ast.walk(arbol) if isinstance(n, ast.ImportFrom)]
        imports = {nodo.module for nodo in nodos}
        assert "adaptadores.extraccion" in imports
        assert "nucleo.verificar" in imports
        nombres_importados = {
            alias.asname or alias.name for nodo in nodos for alias in nodo.names
        }
        usados = {
            nodo.id
            for nodo in ast.walk(arbol)
            if isinstance(nodo, ast.Name) and isinstance(nodo.ctx, ast.Load)
        }
        assert nombres_importados & usados
        for modulo in ("adaptadores.extraccion", "nucleo.verificar"):
            componente = importlib.import_module(modulo)
            for nodo in nodos:
                if nodo.module == modulo:
                    assert all(hasattr(componente, alias.name) for alias in nodo.names)
