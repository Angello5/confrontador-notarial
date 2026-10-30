"""F64: sugerencias en cifras y cuotas, con datos ficticios."""

import pytest

from nucleo.correccion import correcciones
from nucleo.verificar import (
    Catalogo,
    Persona,
    Procedencia,
    letras_de,
    numero_en_letras,
    revisar,
)

_VACIO = Catalogo(())
_ORIGEN = (Procedencia("ficticio.pdf", 1),)
_PARTES = Catalogo(
    tuple(
        Persona(nombre, documento, _ORIGEN)
        for nombre, documento in (
            ("ALBA LUMARIA ZAFIRO", "90000011"),
            ("BRUNO TELURIO NEBULOSA", "90000022"),
            ("CIRO VALDANO QUINTEL", "90000033"),
        )
    )
)


def _obs(borrador, campo, minuta=None, cat=_VACIO):
    minutas = None if minuta is None else {"minuta-ficticia.txt": minuta}
    salidas = revisar(cat, borrador, 88, minutas=minutas)
    return [o for o in salidas if o.startswith(f"[{campo}] «")]


# --- Fundamentos: letras_de ----------------------------------------------------


@pytest.mark.parametrize(
    ("numero", "letras"),
    [
        (0, "CERO"),
        (16, "DIECISEIS"),
        (21, "VEINTIUNO"),
        (36, "TREINTA Y SEIS"),
        (100, "CIEN"),
        (101, "CIENTO UNO"),
        (1000, "MIL"),
        (1500, "MIL QUINIENTOS"),
        (21000, "VEINTIUN MIL"),
        (1_000_000, "UN MILLON"),
        (2_000_000, "DOS MILLONES"),
        (1_000_000_000, "MIL MILLONES"),
    ],
)
def test_letras_de(numero, letras):
    assert letras_de(numero) == letras


def test_letras_de_con_apocope_antes_de_la_moneda():
    assert letras_de(21, apocope=True) == "VEINTIUN"
    assert letras_de(31, apocope=True) == "TREINTA Y UN"


def test_letras_de_ida_y_vuelta():
    muestra = [*range(0, 2100), 999_999, 1_000_001, 21_021_021, 999_999_999_999]
    muestra += [n * 7_919 + 13 for n in range(0, 10**8, 9_973)]
    for n in muestra:
        assert numero_en_letras(letras_de(n).split()) == n, n


# --- Fundamentos: la cola de la observación ------------------------------------


def test_adaptador_separa_el_detalle():
    from expedientes.services import parsear_observacion_regla

    salida = (
        "[NUMERO_EN_LETRAS] «TREINTA Y SEI POR CIENTO (36%)» debe decir «36%»   "
        "(letras mal escritas; se sugiere «TREINTA Y SEIS POR CIENTO (36%)»)"
    )
    fila = parsear_observacion_regla(salida, "TREINTA Y SEI POR CIENTO (36%)")
    assert (fila["hallado"], fila["esperado"]) == (
        "TREINTA Y SEI POR CIENTO (36%)",
        "36%",
    )
    assert fila["detalle"] == (
        "letras mal escritas; se sugiere «TREINTA Y SEIS POR CIENTO (36%)»"
    )


def test_observacion_sin_detalle_no_cambia():
    from expedientes.services import parsear_observacion_regla

    salida = "[NUMERO_EN_LETRAS] «TREINTA Y SIETE (36)» debe decir «36»"
    fila = parsear_observacion_regla(salida, "TREINTA Y SIETE (36)")
    assert "detalle" not in fila
    assert fila["esperado"] == "36"


def test_las_sugerencias_no_entran_en_el_documento_corregido():
    """FR-010: siguen fuera de la corrección automática (F21)."""
    salidas = _obs(
        "EL TREINTA Y SEI POR CIENTO (36%).", "NUMERO_EN_LETRAS", "MINUTA."
    ) + _obs("EN COPROPIEDAD EL 40% DE ANA Y EL 50% DE EVA.", "COPROPIEDAD", "MINUTA.")
    assert len(salidas) == 2
    assert correcciones(salidas, {"minuta-ficticia.txt": "TREINTA Y SEIS"}) == []


# --- Historia 1: letras mal escritas -------------------------------------------


@pytest.mark.parametrize(
    ("borrador", "sugerido"),
    [
        ("EL TREINTA Y SEI POR CIENTO (36%).", "TREINTA Y SEIS POR CIENTO (36%)"),
        ("EN EL PLAZO DE TREINTAY SEIS (36) MESES.", "TREINTA Y SEIS (36)"),
        (
            "LA SUMA DE MIL QUINIENTOZ Y 00/100 SOLES (S/ 1,500.00).",
            "MIL QUINIENTOS Y 00/100 SOLES (S/ 1,500.00)",
        ),
        ("EL 36% (TREINTA Y SEI POR CIENTO).", "36% (TREINTA Y SEIS POR CIENTO)"),
    ],
)
def test_letras_mal_escritas_sugieren_el_texto_correcto(borrador, sugerido):
    (obs,) = _obs(borrador, "NUMERO_EN_LETRAS")
    assert obs.endswith(f"   (letras mal escritas; se sugiere «{sugerido}»)")


def test_area_con_letras_mal_escritas():
    (obs,) = _obs("UN AREA DE CIENTO VEINTEE METROS CUADRADOS (120 M2).", "AREA", "X.")
    assert obs.endswith(
        "(letras mal escritas; se sugiere «CIENTO VEINTE METROS CUADRADOS (120 M2)»)"
    )


def test_errata_que_no_da_la_cifra_no_es_errata():
    (obs,) = _obs("EL PLAZO DE TREINTA Y SEI (37) MESES.", "NUMERO_EN_LETRAS", "X.")
    assert "letras mal escritas" not in obs
    assert "las letras dicen «36»" in obs


def test_la_misma_entrada_da_la_misma_sugerencia():
    """FR-011."""
    borrador = "EL TREINTA Y CINCO POR CIENTO (36%). EN COPROPIEDAD 40% Y 50%."
    minuta = "EL 36 % DEL INMUEBLE."
    primera = revisar(_VACIO, borrador, 88, minutas={"m.txt": minuta})
    assert primera == revisar(_VACIO, borrador, 88, minutas={"m.txt": minuta})


# --- Historia 2: desempata la minuta -------------------------------------------

_DISTINTO = "LE CORRESPONDE EL TREINTA Y CINCO POR CIENTO (36%) DEL BIEN."


def test_la_minuta_confirma_la_cifra():
    (obs,) = _obs(_DISTINTO, "NUMERO_EN_LETRAS", "LE CORRESPONDE EL 36% DEL BIEN.")
    assert obs == (
        "[NUMERO_EN_LETRAS] «TREINTA Y CINCO POR CIENTO (36%)» debe decir «36%»   "
        "(las letras dicen «35%»; la minuta dice «36%»; se sugiere corregir las "
        "letras «TREINTA Y SEIS POR CIENTO (36%)»)"
    )


def test_la_minuta_confirma_las_letras():
    (obs,) = _obs(
        _DISTINTO, "NUMERO_EN_LETRAS", "LE CORRESPONDE EL TREINTA Y CINCO POR CIENTO."
    )
    assert obs.endswith(
        "(las letras dicen «35%»; la minuta dice «35%»; se sugiere corregir la "
        "cifra «TREINTA Y CINCO POR CIENTO (35%)»)"
    )


@pytest.mark.parametrize(
    "minuta",
    [
        "LA MINUTA NO DICE EL PORCENTAJE.",
        "UNA PARTE DEL 35% Y OTRA DEL 36%.",
        "DNI 90000036, PARTIDA 11000035, FECHA 2026-10-30.",
    ],
)
def test_sin_dato_en_la_minuta_no_se_sugiere(minuta):
    (obs,) = _obs(_DISTINTO, "NUMERO_EN_LETRAS", minuta)
    assert obs.endswith("(las letras dicen «35%»; la minuta no trae el dato)")


def test_monto_y_area_siguen_las_mismas_reglas():
    (monto,) = _obs(
        "LA SUMA DE MIL QUINIENTOS Y 00/100 SOLES (S/ 1,600.00).",
        "NUMERO_EN_LETRAS",
        "EL PRECIO ES S/ 1,500.00.",
    )
    assert monto.endswith(
        "se sugiere corregir la cifra «MIL QUINIENTOS Y 00/100 SOLES (S/ 1,500.00)»)"
    )
    (area,) = _obs(
        "UN AREA DE CIENTO VEINTE METROS CUADRADOS (125.00 M2).",
        "AREA",
        "EL TERRENO TIENE 125.00 M2.",
    )
    assert area.endswith(
        "se sugiere corregir las letras «CIENTO VEINTICINCO METROS CUADRADOS "
        "(125.00 M2)»)"
    )


def test_numero_suelto_sin_unidad_no_desempata():
    (obs,) = _obs(
        "EN EL PLAZO DE TREINTA Y CINCO (36) MESES.",
        "NUMERO_EN_LETRAS",
        "EXPEDIENTE 36 DEL AÑO.",
    )
    assert obs.endswith("la minuta no trae el dato)")
    (obs,) = _obs(
        "EN EL PLAZO DE TREINTA Y CINCO (36) MESES.",
        "NUMERO_EN_LETRAS",
        "EN EL PLAZO DE TREINTA Y SEIS (36) MESES.",
    )
    assert obs.endswith("se sugiere corregir las letras «TREINTA Y SEIS (36)»)")


# --- Historia 3: cuotas en todos los actos -------------------------------------

_REPARTO_MINUTA = (
    "ADQUIEREN: ALBA LUMARIA ZAFIRO EL 20%, BRUNO TELURIO NEBULOSA EL 20% Y "
    "CIRO VALDANO QUINTEL EL 60%."
)


def test_cuota_distinta_de_la_minuta_se_sugiere_por_persona():
    (obs,) = _obs(
        "ADQUIEREN: ALBA LUMARIA ZAFIRO EL 20%, BRUNO TELURIO NEBULOSA EL 20% Y "
        "CIRO VALDANO QUINTEL EL 50%.",
        "COPROPIEDAD",
        _REPARTO_MINUTA,
        _PARTES,
    )
    assert obs.endswith(
        "(las cuotas suman 90 %; la minuta dice «CIRO VALDANO QUINTEL 60 %»; "
        "se sugiere «CIRO VALDANO QUINTEL 60 % (dice 50 %)»)"
    )


def test_dos_cuotas_distintas_en_el_orden_del_proyecto():
    (obs,) = _obs(
        "ADQUIEREN: ALBA LUMARIA ZAFIRO EL 30%, BRUNO TELURIO NEBULOSA EL 20% Y "
        "CIRO VALDANO QUINTEL EL 40%.",
        "COPROPIEDAD",
        _REPARTO_MINUTA,
        _PARTES,
    )
    assert obs.endswith(
        "se sugiere «ALBA LUMARIA ZAFIRO 20 % (dice 30 %), "
        "CIRO VALDANO QUINTEL 60 % (dice 40 %)»)"
    )


@pytest.mark.parametrize(
    "borrador",
    [
        "APORTAN AL CAPITAL SOCIAL: ALBA LUMARIA ZAFIRO EL 50% Y BRUNO TELURIO "
        "NEBULOSA EL 40%.",
        "LOS HEREDEROS RECIBEN LA HERENCIA ASI: 50% Y 40%.",
        "ALBA LUMARIA ZAFIRO ADQUIERE EL 50% Y BRUNO TELURIO NEBULOSA EL 40%.",
    ],
)
def test_cuotas_en_otros_actos_sin_reparto_en_la_minuta(borrador):
    (obs,) = _obs(borrador, "COPROPIEDAD", "LA MINUTA NO REPARTE.", _PARTES)
    assert obs.endswith("(las cuotas suman 90 %; la minuta no trae el dato)")


@pytest.mark.parametrize(
    "borrador",
    [
        "PAGARA UN INTERES DEL 2% MENSUAL Y UNA MORA DEL 1% DIARIO.",
        "ALBA LUMARIA ZAFIRO PAGARA UNA PENALIDAD DEL 10% Y BRUNO TELURIO "
        "NEBULOSA UNA COMISION DEL 5%.",
        "CADA UNO TIENE 40% DE LA COPROPIEDAD Y ADQUIERE 50% DEL BIEN.",
        "VENDEN EL 100% DE LAS ACCIONES Y DERECHOS Y ADQUIEREN 50% Y 50%.",
    ],
)
def test_porcentajes_que_no_reparten_no_avisan(borrador):
    assert _obs(borrador, "COPROPIEDAD", "MINUTA.", _PARTES) == []


def test_personas_distintas_en_la_minuta_no_se_sugiere():
    (obs,) = _obs(
        "ADQUIEREN: ALBA LUMARIA ZAFIRO EL 50% Y BRUNO TELURIO NEBULOSA EL 40%.",
        "COPROPIEDAD",
        _REPARTO_MINUTA,
        _PARTES,
    )
    assert obs.endswith("la minuta no trae el dato)")


# --- Pantalla (aviso_de) -------------------------------------------------------


def _fila(campo, hallado, esperado, detalle):
    return {
        "campo": campo,
        "hallado": hallado,
        "esperado": esperado,
        "detalle": detalle,
    }


@pytest.mark.parametrize(
    ("fila", "verificar", "lista"),
    [
        (
            _fila(
                "NUMERO_EN_LETRAS",
                "TREINTA Y SEI POR CIENTO (36%)",
                "36%",
                "letras mal escritas; se sugiere «TREINTA Y SEIS POR CIENTO (36%)»",
            ),
            "Las letras están mal escritas. "
            "Se sugiere: TREINTA Y SEIS POR CIENTO (36%).",
            "Letras mal escritas: TREINTA Y SEI POR CIENTO (36%) → "
            "TREINTA Y SEIS POR CIENTO (36%)",
        ),
        (
            _fila(
                "NUMERO_EN_LETRAS",
                "TREINTA Y CINCO POR CIENTO (36%)",
                "36%",
                "las letras dicen «35%»; la minuta dice «36%»; se sugiere corregir "
                "las letras «TREINTA Y SEIS POR CIENTO (36%)»",
            ),
            "La minuta dice 36%. Se sugiere corregir las letras: "
            "TREINTA Y SEIS POR CIENTO (36%).",
            "Cifra y letras no coinciden: TREINTA Y CINCO POR CIENTO (36%) → "
            "TREINTA Y SEIS POR CIENTO (36%)",
        ),
        (
            _fila(
                "AREA",
                "CIENTO VEINTE METROS CUADRADOS (125.00 M2)",
                "125.00 M2",
                "las letras dicen «120.00 M2»; la minuta dice «120.00 M2»; se "
                "sugiere corregir la cifra «CIENTO VEINTE METROS CUADRADOS "
                "(120.00 M2)»",
            ),
            "La minuta dice 120.00 M2. Se sugiere corregir la cifra: "
            "CIENTO VEINTE METROS CUADRADOS (120.00 M2).",
            "Cifra y letras no coinciden: CIENTO VEINTE METROS CUADRADOS "
            "(125.00 M2) → CIENTO VEINTE METROS CUADRADOS (120.00 M2)",
        ),
        (
            _fila(
                "NUMERO_EN_LETRAS",
                "TREINTA Y CINCO POR CIENTO (36%)",
                "36%",
                "las letras dicen «35%»; la minuta no trae el dato",
            ),
            "La cifra dice 36% y las letras dicen 35%. "
            "La minuta no trae este dato: revise cuál corresponde.",
            "Cifra y letras no coinciden: TREINTA Y CINCO POR CIENTO (36%)",
        ),
        (
            _fila(
                "COPROPIEDAD",
                "20%, ANA EL 20% Y LUIS EL 50%",
                "100 %",
                "las cuotas suman 90 %; la minuta dice «LUIS 60 %»; "
                "se sugiere «LUIS 60 % (dice 50 %)»",
            ),
            "Las cuotas suman 90 %. La minuta dice LUIS 60 %. "
            "Se sugiere: LUIS 60 % (dice 50 %).",
            "Las cuotas no suman 100 %: 20%, ANA EL 20% Y LUIS EL 50% → "
            "LUIS 60 % (dice 50 %)",
        ),
        (
            _fila(
                "COPROPIEDAD",
                "50% Y 40%",
                "100 %",
                "las cuotas suman 90 %; la minuta no trae el dato",
            ),
            "Las cuotas suman 90 %. La minuta no trae el reparto: "
            "revise cuál corresponde.",
            "Las cuotas no suman 100 %: 50% Y 40%",
        ),
    ],
)
def test_aviso_con_lo_hallado_la_minuta_y_la_sugerencia(fila, verificar, lista):
    from expedientes.services import aviso_de

    assert aviso_de(fila) == {
        "borrador": fila["hallado"],
        "verificar": verificar,
        "lista": lista,
    }
