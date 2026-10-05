"""F39: el anexo de la minuta omitido en el borrador, con datos ficticios."""

from nucleo.verificar import anexos_omitidos, montos_exigibles, sin_anexos_insertados

_CLAUSULA = (
    "PRIMERA: LAS PARTES FICTICIAS CELEBRAN EL PRESENTE CONTRATO DE MUTUO "
    "CON LAS CONDICIONES QUE SE DETALLAN A CONTINUACION."
)
_ANEXO = (
    "ANEXO 1 – HOJA RESUMEN\n"
    "EL ACREEDOR FICTICIO PUEDE DAR POR VENCIDO TODO EL PLAZO SI EL DEUDOR "
    "FICTICIO DEJA DE PAGAR DOS CUOTAS SEGUIDAS DE SU CRONOGRAMA.\n"
    "LA PRENDA FICTICIA GARANTIZA TODAS LAS DEUDAS DEL DEUDOR FICTICIO FRENTE "
    "AL ACREEDOR FICTICIO HASTA SU TOTAL CANCELACION.\n"
    "MONTO: S/ 1,000.00\n"
)
_MINUTA = f"{_CLAUSULA}\n{_ANEXO}"


def test_anexo_ausente_es_una_sola_observacion():
    assert anexos_omitidos([_MINUTA], _CLAUSULA, 88) == [
        "[ANEXO] FALTA: «ANEXO 1 – HOJA RESUMEN»"
    ]


def test_anexo_presente_no_se_observa():
    assert anexos_omitidos([_MINUTA], _MINUTA, 88) == []


def test_parrafo_fuera_de_anexo_ya_no_se_observa():
    minuta = (
        f"{_CLAUSULA}\nSEGUNDA: UN PARRAFO FICTICIO DE LA MINUTA QUE EL BORRADOR "
        f"NO COPIA Y QUE NO FORMA PARTE DE NINGUN ANEXO.\n{_ANEXO}"
    )
    assert anexos_omitidos([minuta], _MINUTA, 88) == []


def test_minuta_sin_anexo_no_se_observa():
    assert anexos_omitidos([_CLAUSULA], "", 88) == []


def test_cada_anexo_se_evalua_por_separado():
    cronograma = "ANEXO II CRONOGRAMA\n" + "CUOTA FICTICIA MENSUAL DE CIEN SOLES " * 3
    assert anexos_omitidos([f"{_MINUTA}\n{cronograma}"], _MINUTA, 88) == [
        "[ANEXO] FALTA: «ANEXO II CRONOGRAMA»"
    ]


_CON_MONTO = f"{_MINUTA}MONTO DEL CREDITO FICTICIO: S/ 12,345.67\n"
_INSERTO = f"{_CLAUSULA}\nINSERTO: =====\nSIGUE UNA FIRMA ILEGIBLE"


def test_anexo_insertado_como_recaudo_no_se_observa_ni_exige_sus_montos():
    """F39: la hoja resumen escaneada va como inserto (Recaudos.pdf)."""
    recaudo = "HOJA RESUMEN ESCANEADA  IMPORTE  12,345.67"
    minutas = sin_anexos_insertados([_CON_MONTO], _INSERTO, [recaudo])

    assert anexos_omitidos(minutas, _INSERTO, 88) == []
    assert not any("12,345.67" in m for m in montos_exigibles(minutas))
    assert _CLAUSULA in minutas[0]


def test_sin_inserto_o_sin_el_monto_en_los_recaudos_el_anexo_cuenta():
    recaudo = "HOJA RESUMEN ESCANEADA  IMPORTE  12,345.67"
    assert sin_anexos_insertados([_CON_MONTO], _CLAUSULA, [recaudo]) == [_CON_MONTO]
    assert sin_anexos_insertados([_CON_MONTO], _INSERTO, ["OTRO 99,999.99"]) == [
        _CON_MONTO
    ]
