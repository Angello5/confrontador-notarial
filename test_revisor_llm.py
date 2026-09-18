"""Test del filtro con casos de prosa inventados, sin documentos de clientes.

No llama a la API. python3 test_revisor_llm.py
"""
from revisor_llm import filtrar

DOC = ("LOS COMPARECIENTES DECLARAN QUÉ SON DE ESTADO CIVIL. OCTAO: SAN MARTIN "
       "EN LA UIRBANIZACION, DE OCUPACIÒN ARTESANO, CON LOTE 42 MANZANA 2. "
       "MARIA NUBELIA ZURBELIA.")
FUENTES = "URBANIZACION CIVIL NUBELIA ZURBELIA"

CASOS = [
    # (encontrado, correccion, se_acepta, por que)
    ("OCTAO", "OCTAVO", True, "error real de prosa"),
    ("OCUPACIÒN", "OCUPACIÓN", True, "tilde invertida: el texto ya trae tilde"),
    ("QUÉ", "QUE", True, "tilde sobrante, no agregada"),
    ("UIRBANIZACION", "URBANIZACION", True, "el error tambien esta en la minuta"),
    ("ZARDELIA", "NUBELIA", False, "no existe en el documento"),
    ("ARTESANO", "ARTESANO", False, "correccion identica al error"),
    ("42", "428", False, "dato numerico"),
    ("LOTE 42", "LOTE 482", False, "dato numerico"),
    ("SAN MARTIN", "SAN MARTÍN", False, "tilde sobre mayusculas"),
    ("MARIA", "MARÍA", False, "tilde sobre mayusculas"),
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
