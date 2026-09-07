"""Check del filtro: cada caso viene de un hallazgo real observado en las pruebas.

No llama a la API. python3 test_revisor_llm.py
"""
from revisor_llm import filtrar

DOC = ("LAS DONANTES, DECLARAN QUÉ PARA EFECTOS REGISTRALES. OCTAO: SE INSTRUYO "
       "EN LA UIRBANIZACION, DE OCUPACIÒN DOCENTE, JIRON LAS ÁGUILAS 24 TORRE 1. "
       "RATIFICANDOSE EDELMIRA AVELLANEDA.")
FUENTES = "URBANIZACION OCUPACION EDELMIRA AVELLANEDA"

CASOS = [
    # (encontrado, correccion, se_acepta, por que)
    ("OCTAO", "OCTAVO", True, "error real de prosa"),
    ("OCUPACIÒN", "OCUPACIÓN", True, "tilde invertida: el texto ya trae tilde"),
    ("QUÉ", "QUE", True, "tilde sobrante, no agregada"),
    ("UIRBANIZACION", "URBANIZACION", True, "el error tambien esta en la minuta"),
    ("EDELMANDA", "EDELMIRA", False, "no existe en el documento"),
    ("MENDOZ", "MENDOZ", False, "correccion identica al error"),
    ("24", "248", False, "dato numerico"),
    ("ÁGUILAS 24", "ÁGUILAS 284", False, "dato numerico"),
    ("SE INSTRUYO", "SE INSTRUYÓ", False, "tilde sobre mayusculas"),
    ("RATIFICANDOSE", "RATIFICÁNDOSE", False, "tilde sobre mayusculas"),
]

if __name__ == "__main__":
    ok, fuera = filtrar([{"encontrado": e, "correccion": c} for e, c, _, _ in CASOS],
                        DOC, FUENTES)
    aceptados = {h["encontrado"] for h in ok}
    for enc, cor, esperado, motivo in CASOS:
        real = enc in aceptados
        estado = "acepta" if real else "descarta"
        assert real == esperado, f"{enc!r} -> {cor!r}: {estado} y deberia ser lo contrario ({motivo})"

    # el respaldo distingue lo que se puede confirmar contra la minuta
    respaldos = {h["encontrado"]: h["respaldo"] for h in ok}
    assert respaldos["UIRBANIZACION"] == "en las fuentes", respaldos
    assert respaldos["OCTAO"] == "solo prosa", respaldos

    print(f"OK — {len(ok)} aceptados, {len(fuera)} descartados, {len(CASOS)} casos")
