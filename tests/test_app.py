"""Prueba sintética del flujo completo de la UI de confrontación."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_confrontacion_ui_sin_ia_con_archivos_ficticios():
    texto = b"NOMBRE ANA LUZ QUISPE MAMANI DE NACIONALIDAD PERUANA DNI 90000001\n"
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py").run(timeout=30)
    app.file_uploader[0].set_value(("fuente.txt", texto, "text/plain")).run(timeout=30)
    app.file_uploader[1].set_value(("borrador.txt", texto, "text/plain")).run(
        timeout=30
    )
    app.checkbox[0].set_value(False).run(timeout=30)
    app.button[0].click().run(timeout=30)

    assert not app.exception
    assert any("Sin observaciones" in item.value for item in app.success)
