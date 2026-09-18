"""Test de ortografia.py con errores y nombres ficticios.

python -m pytest test_ortografia.py
"""

from ortografia import lista_casa, revisar

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
    "OCUPACIÒN": "no existe en castellano",
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
    hallado = {w: m for w, m, _ in revisar(texto, extra={"ZURBELIA", "LAMPARA"})}

    for w, motivo in ERRORES.items():
        assert w in hallado, f"{w} deberia marcarse y no se marco"
        assert hallado[w] == motivo, f"{w}: {hallado[w]!r} en vez de {motivo!r}"
    for w in CORRECTAS:
        assert w not in hallado, f"{w} se marco y es correcta ({hallado.get(w)})"

    # los apellidos se pasan en `extra`, no a la lista de la casa: cambian por caso
    assert "ZURBELIA" not in hallado and "LAMPARA" not in hallado
    # LAMPARA no se marca: existe "lámpara" y se acepta la tilde ausente.
    sin_extra = {w for w, _, _ in revisar("ZURBELIA LAMPARA")}
    assert "ZURBELIA" in sin_extra, sin_extra

    # la correccion de tilde mal puesta es exacta, no adivinada
    sug = {w: s for w, _, s in revisar("CLAÚSULA CÍVIL SÉXTA")}
    assert sug == {"CLAÚSULA": "clausula", "CÍVIL": "civil", "SÉXTA": "sexta"}, sug

    print(
        f"OK — {len(ERRORES)} errores detectados, {len(CORRECTAS)} correctas respetadas, "
        f"lista de la casa: {len(lista_casa())} términos"
    )
