"""Pruebas de la integración de la vía determinista con el núcleo."""

import app_ortografia
from pathlib import Path
from streamlit.testing.v1 import AppTest


class DiccionarioFicticio:
    def lookup(self, palabra):
        return palabra == "texto"


def test_confrontacion_pasa_recursos_completos_a_ortografia():
    """La ruta de confrontación no debe usar la firma antigua de revisar."""
    app_ortografia.diccionario = lambda: (DiccionarioFicticio(), ["texto"])

    resultado = app_ortografia.revisar_ortografia("texto", {"NOMBRE"})

    assert resultado == []


def test_via_determinista_confronta_archivos_ficticios():
    texto = b"NOMBRE ANA LUZ QUISPE MAMANI DE NACIONALIDAD PERUANA DNI 90000001\n"
    app = AppTest.from_file(Path(__file__).parents[1] / "app_ortografia.py").run(
        timeout=30
    )
    app.file_uploader[0].set_value(("fuente.txt", texto, "text/plain")).run(timeout=30)
    app.file_uploader[1].set_value(("borrador.txt", texto, "text/plain")).run(
        timeout=30
    )
    app.button[0].click().run(timeout=30)

    assert not app.exception
    assert any("Ortografía sin observaciones" in item.value for item in app.success)


def test_lista_de_casa_se_actualiza_sin_duplicados(monkeypatch, tmp_path):
    import adaptadores.diccionario as recursos

    lista = tmp_path / "lista.txt"
    lista.write_text("# comentario\nSIGLA\n", encoding="utf-8")
    monkeypatch.setattr(recursos, "LISTA", lista)

    assert app_ortografia.lista_casa() == {"SIGLA"}
    assert app_ortografia.agregar_a_lista(["SIGLA", "TÉRMINO"]) == 1
    assert app_ortografia.lista_casa() == {"SIGLA", "TÉRMINO"}
