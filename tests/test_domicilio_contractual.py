"""F37 con datos ficticios: domicilio contractual de la minuta y tipo de habilitación."""

from datetime import date

from nucleo.verificar import (
    Catalogo,
    Persona,
    Procedencia,
    domicilios_contractuales,
    revisar_persona_ampliada,
)

HOY = date(2025, 1, 1)
MINUTA = (
    "ALBA LUMARIA ZAFIRO, CON DOMICILIO PARA EFECTOS DE ESTE CONTRATO EN AV. SOL 300, "
    "OFICINA 4, DISTRITO DE LIMA. TODOS SEÑALANDO DOMICILIO PARA EFECTOS DE ESTE "
    "CONTRATO EN PUEBLO JOVEN LOS CEDROS MZ G LOTE 5, DISTRITO DE ANCON."
)


def _persona(domicilio):
    origen = Procedencia("reniec-ficticio.pdf", 1)
    return Persona(
        "ALBA LUMARIA ZAFIRO",
        "90000011",
        (origen,),
        domicilio=domicilio,
        procedencia_domicilio=origen,
    )


def _tipos(observaciones):
    return [fila["tipo"] for fila in observaciones]


def test_domicilios_contractuales_de_la_minuta():
    assert domicilios_contractuales([MINUTA]) == [
        "AV. SOL 300, OFICINA 4",
        "PUEBLO JOVEN LOS CEDROS MZ G LOTE 5",
    ]


def test_domicilio_contractual_de_la_minuta_es_valido():
    cat = Catalogo((_persona("JR. LUNA 12"),))
    linea = (
        "ALBA LUMARIA ZAFIRO, SOLTERA, CON DOMICILIO EN AVENIDA SOL 300 OFICINA 4, "
        "DISTRITO DE LIMA."
    )
    assert _tipos(revisar_persona_ampliada(cat, linea, HOY)) == [
        "DOMICILIO_NO_ENCONTRADO"
    ]
    contractuales = domicilios_contractuales([MINUTA])
    assert revisar_persona_ampliada(cat, linea, HOY, contractuales) == ()


def test_tipo_de_habilitacion_omitido_o_cambiado_es_aviso_leve():
    cat = Catalogo((_persona("MZ. G LT. 5 ASENT.H. LOS CEDROS"),))
    for linea in (
        "ALBA LUMARIA ZAFIRO, SOLTERA, CON DOMICILIO EN MANZANA G LOTE 05 LOS CEDROS.",
        "ALBA LUMARIA ZAFIRO, SOLTERA, CON DOMICILIO EN P.J. LOS CEDROS MZ G LT 5.",
    ):
        observaciones = revisar_persona_ampliada(cat, linea, HOY)
        assert _tipos(observaciones) == ["DOMICILIO_HABILITACION"], linea
        assert observaciones[0]["referencia"] == "RENIEC"
    completo = (
        "ALBA LUMARIA ZAFIRO, SOLTERA, CON DOMICILIO EN ASENTAMIENTO HUMANO LOS "
        "CEDROS MANZANA G LOTE 5."
    )
    assert revisar_persona_ampliada(cat, completo, HOY) == ()
