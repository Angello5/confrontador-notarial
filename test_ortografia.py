"""Test de ortografia.py con errores y nombres ficticios.

python -m pytest test_ortografia.py
"""

from adaptadores.diccionario import diccionario, lista_casa
from nucleo.ortografia import plano, revisar, tildada

ERRORES = {
    "DEUDORR": "no existe en castellano",
    "OCTAO": "no existe en castellano",
    "MEIO": "no existe en castellano",
    "CONSTACIA": "no existe en castellano",
    "UIRBANIZACION": "no existe en castellano",
    "CLAÚSULA": "tilde mal puesta",
    "CÍVIL": "tilde mal puesta",
    "DÍARIA": "tilde mal puesta",
    "SÉXTA": "tilde mal puesta",
    "INVALIDÉZ": "tilde mal puesta",
    "OCUPACIÒN": "acento grave",  # F39: correccion exacta, OCUPACIÓN
}
# lo que NO puede marcarse: convencion de mayusculas, nombres propios, la lista
CORRECTAS = [
    "OBLIGACION",
    "CLAUSULA",
    "OCUPACION",
    "TAMBIEN",
    "DECIMO",
    "PERÚ",
    "ISIDRO",
    "OCUPACIÓN",
    "CLÁUSULA",
    "SUNARP",
    "EVICCIÓN",
]


def test_ortografia():
    # ZURBELIA es inventado; LAMPARA prueba la aceptación de una tilde ausente.
    # Ambos se pasan como apellidos ficticios mediante extra.
    texto = " ".join(list(ERRORES) + CORRECTAS + ["ZURBELIA", "LAMPARA"])
    d, lemas = diccionario()
    aceptadas = lista_casa()
    hallado = {
        w: m
        for w, m, _ in revisar(
            texto, d, lemas, aceptadas, extra={"ZURBELIA", "LAMPARA"}
        )
    }

    for w, motivo in ERRORES.items():
        assert w in hallado, f"{w} deberia marcarse y no se marco"
        assert hallado[w] == motivo, f"{w}: {hallado[w]!r} en vez de {motivo!r}"
    for w in CORRECTAS:
        assert w not in hallado, f"{w} se marco y es correcta ({hallado.get(w)})"

    # los apellidos se pasan en `extra`, no a la lista de la casa: cambian por caso
    assert "ZURBELIA" not in hallado
    assert "LAMPARA" not in hallado
    # LAMPARA no se marca: existe "lámpara" y se acepta la tilde ausente.
    sin_extra = {w for w, _, _ in revisar("ZURBELIA LAMPARA", d, lemas, aceptadas)}
    assert "ZURBELIA" in sin_extra, sin_extra

    # la correccion de tilde mal puesta es exacta, no adivinada
    sug = {w: s for w, _, s in revisar("CLAÚSULA CÍVIL SÉXTA", d, lemas, aceptadas)}
    assert sug == {"CLAÚSULA": "clausula", "CÍVIL": "civil", "SÉXTA": "sexta"}, sug

    print(
        f"OK — {len(ERRORES)} errores detectados, {len(CORRECTAS)} correctas respetadas, "
        f"lista de la casa: {len(lista_casa())} términos"
    )


def test_plano_conserva_enie_sin_alterar_aceptacion_de_tilde_ausente():
    class DiccionarioFicticio:
        def lookup(self, palabra):
            return palabra in {"lámpara", "LÁMPARA"}

    assert plano("MUÑOZ") == "muñoz"
    assert tildada("MUÑOZ") is False
    assert plano("ACCIÓN") == "accion"
    assert revisar("LAMPARA", DiccionarioFicticio(), ["lámpara"], set()) == []
