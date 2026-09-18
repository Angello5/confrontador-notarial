"""Medición privada opcional; no lee rutas ni expedientes al recolectar."""

import contextlib
import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


class _MedicionInvalida(Exception):
    pass


@pytest.mark.local_reference
def test_referencia_local(monkeypatch, capfd):
    # Ningún dato del expediente debe salir en capturas, trazas o caché persistente.
    try:
        if os.environ.get("CI"):
            raise ValueError("CI")
        configurada = os.environ.get("EXPEDIENTES_REFERENCIA_DIR")
        if not configurada:
            raise FileNotFoundError
        raiz = Path(configurada).resolve(strict=True)
        repo = Path(__file__).resolve().parents[1]
        if raiz == repo or repo in raiz.parents:
            raise ValueError("El expediente debe estar fuera del repositorio")
        if not (raiz / "cliente").is_dir() or not all(
            (raiz / nombre).is_file() for nombre in ("observado.docx", "correcto.docx")
        ):
            raise FileNotFoundError
        import extraer
        from verificar import catalogo, revisar

        with (
            TemporaryDirectory(prefix="notarial-reference-") as cache,
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            monkeypatch.setattr(extraer, "CACHE", Path(cache))
            fuentes = extraer.recolectar([str(raiz / "cliente")])
            cat = catalogo(fuentes)
            observado = extraer.leer(raiz / "observado.docx")
            correcto = extraer.leer(raiz / "correcto.docx")
            resultados = [revisar(cat, observado, 88) for _ in range(5)]
            if len(resultados[0]) != 8:
                raise _MedicionInvalida
            if any(r != resultados[0] for r in resultados):
                raise _MedicionInvalida
            if revisar(cat, correcto, 88):
                raise _MedicionInvalida
    except FileNotFoundError:
        pytest.fail("Expediente local ausente o incompleto.", pytrace=False)
    except Exception:
        pytest.fail("Medición local no aprobada.", pytrace=False)
    finally:
        capfd.readouterr()
