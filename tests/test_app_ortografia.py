"""Pruebas de la integración de la vía determinista con el núcleo."""

import app_ortografia


class DiccionarioFicticio:
    def lookup(self, palabra):
        return palabra == "texto"


def test_confrontacion_pasa_recursos_completos_a_ortografia():
    """La ruta de confrontación no debe usar la firma antigua de revisar."""
    app_ortografia.diccionario = lambda: (DiccionarioFicticio(), ["texto"])

    resultado = app_ortografia.revisar_ortografia("texto", {"NOMBRE"})

    assert resultado == []
