"""F24: solo se exigen los montos de la minuta (datos ficticios)."""

from nucleo.verificar import catalogo, montos_exigibles, revisar

_MINUTA = "PRECIO DE VENTA S/ 150,000.00 PAGADO AL CONTADO."
_FUENTES = {
    "minuta-ficticia.txt": _MINUTA,
    "liquidacion-ficticia.txt": "TASA REGISTRAL S/ 45.50. DERECHOS S/ 1,230.00.",
}


def _montos(borrador, exigibles=frozenset(montos_exigibles([_MINUTA]))):
    cat = catalogo(_FUENTES)
    return [o for o in revisar(cat, borrador, 88, None, exigibles) if "[MONTO]" in o]


def test_monto_de_recaudo_ausente_no_se_exige():
    assert _montos("EL PRECIO ES S/ 150,000.00.") == []


def test_monto_de_minuta_ausente_se_exige():
    assert _montos("SIN IMPORTES") == [
        "[MONTO] FALTA: «150,000.00» esta en las fuentes y no aparece en el destino"
    ]


def test_monto_de_recaudo_en_el_borrador_se_reconoce():
    assert _montos("PRECIO S/ 150,000.00 Y TASA S/ 45.50.") == []


def test_monto_alterado_se_sigue_detectando():
    assert _montos("PRECIO S/ 150,000.00 Y TASA S/ 45.60.") == [
        "[MONTO] «45.60» debe decir «45.50»"
    ]


def test_sin_montos_exigibles_se_exigen_todos():
    faltas = _montos("EL PRECIO ES S/ 150,000.00.", None)
    assert faltas == [
        "[MONTO] FALTA: «1,230.00» esta en las fuentes y no aparece en el destino",
        "[MONTO] FALTA: «45.50» esta en las fuentes y no aparece en el destino",
    ]


def test_montos_exigibles_de_varias_minutas():
    assert montos_exigibles([_MINUTA, "ARRAS S/ 5,000.00", "SIN MONTO"]) == {
        "150,000.00",
        "5,000.00",
    }
