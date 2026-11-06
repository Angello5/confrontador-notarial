"""F61 · Capa de sentido: núcleo puro, con frases ficticias y modelos simulados."""

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from nucleo import sentido as s


# --- Dobles de los modelos ------------------------------------------------------------
@dataclass
class Oracion:
    start_char: int
    end_char: int


@dataclass
class Token:
    text: str
    i: int
    pos_: str = "NOUN"
    dep_: str = "ROOT"
    rasgos: dict = field(default_factory=dict)
    head: "Token" = None
    children: list = field(default_factory=list)

    @property
    def morph(self):
        return self

    def get(self, nombre):
        valor = self.rasgos.get(nombre)
        return [valor] if valor else []


@dataclass
class Doc:
    texto: str
    tokens: list = field(default_factory=list)

    @property
    def sents(self):
        return [
            Oracion(m.start(), m.end())
            for m in re.finditer(r".+?(?:[.;](?=\s|$)|$)", self.texto)
        ]

    def __iter__(self):
        return iter(self.tokens)


def analizar(textos):
    return [Doc(t) for t in textos]


def parecido(a, b):
    return [[SequenceMatcher(None, x, y).ratio() for y in b] for x in a]


def nli_negacion(pares):
    """Contradicción si solo una de las dos frases tiene «no»; si no, equivalentes."""
    salida = []
    for premisa, hipotesis in pares:
        negadas = [" no " in f" {t} " for t in (premisa, hipotesis)]
        salida.append(
            (0.02, 0.03, 0.95) if negadas[0] != negadas[1] else (0.97, 0.02, 0.01)
        )
    return salida


def nli_neutral(pares):
    return [(0.1, 0.8, 0.1) for _ in pares]


CLASIFICADORES = {"mdeberta": nli_negacion, "minilm": nli_negacion}

MINUTA = (
    "MINUTA DE COMPRAVENTA. SEÑOR NOTARIO: SIRVASE EXTENDER LA PRESENTE.\n"
    "PRIMERA.- EL VENDEDOR SE OBLIGA A ENTREGAR EL INMUEBLE AL COMPRADOR EN LA FECHA PACTADA.\n"
    "SEGUNDA.- EL COMPRADOR PAGARA LOS GASTOS NOTARIALES Y REGISTRALES DE ESTA ESCRITURA.\n"
    "TERCERA.- LAS PARTES DECLARAN QUE NO EXISTE DEUDA ALGUNA SOBRE EL BIEN VENDIDO.\n"
    "AGREGUE USTED SEÑOR NOTARIO LO QUE FUERE DE LEY."
)


# --- Texto ----------------------------------------------------------------------------
def test_plano_quita_tildes_cifras_y_espacios():
    assert s.plano("  Pagará  S/ 1,500.00 al vendedor ") == "PAGARA S/ # AL VENDEDOR"


def test_limpiar_quita_relleno_y_pie_de_pagina():
    assert s.limpiar("CLAUSULA ======= FIN Página 2 de 7").split() == [
        "CLAUSULA",
        "FIN",
    ]


def test_cuerpo_va_de_la_primera_clausula_al_cierre():
    cuerpo = s.cuerpo(MINUTA)
    assert cuerpo.startswith("PRIMERA.-")
    assert "SEÑOR NOTARIO: SIRVASE" not in cuerpo
    assert "AGREGUE USTED" not in cuerpo


def test_cuerpo_sin_clausulas_devuelve_todo():
    assert s.cuerpo("TEXTO SIN ROTULOS") == "TEXTO SIN ROTULOS"


def test_sin_membrete_quita_la_linea_repetida_en_tres_paginas():
    pagina = "ESTUDIO JURIDICO FICTICIO SAC\nTEXTO PROPIO DE LA HOJA {n}\n"
    texto = "\f".join(pagina.format(n=n) for n in ("UNO", "DOS", "TRES"))
    limpio = s.sin_membrete(texto)
    assert "ESTUDIO JURIDICO" not in limpio
    assert limpio.count("TEXTO PROPIO") == 3


def test_sin_membrete_conserva_lineas_de_dos_paginas():
    texto = "LINEA REPETIDA DOS VECES\fLINEA REPETIDA DOS VECES"
    assert s.sin_membrete(texto) == texto


# --- ¿Solo cambió la lectura? -----------------------------------------------------------
def test_solo_lectura_acepta_letras_mal_leidas():
    assert s.solo_lectura(
        "EL VENDEDOR SE OBLIGA A ENTREGAR EL INMUEBLE",
        "EI VENDEDOR SE OBLIGA A ENTREGAR EL INMUEBIE",
    )


def test_solo_lectura_rechaza_negacion_y_cambio_de_parte():
    base = "EL VENDEDOR SE OBLIGA A ENTREGAR EL INMUEBLE"
    assert not s.solo_lectura(base, "EL VENDEDOR NO SE OBLIGA A ENTREGAR EL INMUEBLE")
    assert not s.solo_lectura(base, "EL COMPRADOR SE OBLIGA A ENTREGAR EL INMUEBLE")


def test_solo_lectura_ignora_marca_de_lista():
    assert s.solo_lectura(
        "a) EL PRECIO SE PAGA AL CONTADO", "EL PRECIO SE PAGA AL CONTADO"
    )


def test_solo_lectura_ignora_cifras_en_letras_agregadas():
    assert s.solo_lectura(
        "EL PRECIO ES DE S/ 100,000.00 QUE SE PAGA AL CONTADO",
        "EL PRECIO ES DE S/ 100,000.00 (CIEN MIL CON 00/100 SOLES) QUE SE PAGA AL CONTADO",
    )


def test_cifras_en_letras_no_borra_un_numero_suelto():
    assert "DOS" in s.comparable("EL PLAZO ES DE DOS AÑOS")


def test_esta_en_tolera_otro_corte_de_oracion():
    doc = s.comparable(
        "EL VENDEDOR DECLARA. EL BIEN ESTA LIBRE DE CARGAS Y GRAVAMENES."
    )
    assert s.esta_en("EL BIEN ESTA LIBRE DE CARGAS", doc)


def test_esta_en_rechaza_una_palabra_agregada():
    doc = s.comparable("EL BIEN ESTA LIBRE DE CARGAS Y GRAVAMENES")
    assert not s.esta_en("EL BIEN NO ESTA LIBRE DE CARGAS", doc)


def test_esta_en_falla_si_no_se_parece():
    assert not s.esta_en("TEXTO QUE NO APARECE", s.comparable("OTRA COSA DISTINTA"))


def test_esta_en_tolera_letras_mal_leidas():
    doc = s.comparable("LAS PARTES SE SOMETEN A LOS JUECES DE LIMA")
    assert s.esta_en("LAS PARTES SE SOMETEN A LOS JUECES DE LIMA", doc)
    assert s.esta_en(
        "LAS PARTES SE SOMETEN A LOS JUECES DE LIMA",
        s.comparable("LAS PARTES SE SOMETEN A LOS JUECES DE LlMA"),
    )


# --- Veredicto ----------------------------------------------------------------------------
def test_relacion_en_las_dos_direcciones():
    implica, neutral, contradice = (0.9, 0.05, 0.05), (0.1, 0.8, 0.1), (0, 0.1, 0.9)
    assert s.relacion(contradice, implica) == ("CONTRADICE", 0.9)
    assert s.relacion(implica, implica) == ("EQUIVALENTE", 0.9)
    assert s.relacion(implica, neutral) == ("OMITE", 0.9)
    assert s.relacion(neutral, implica) == ("AGREGA", 0.9)
    assert s.relacion(neutral, neutral) == ("CAMBIO", 0.9)


def test_combinar_observacion_si_ambos_y_revisar_si_uno():
    cambio, igual, dudoso = ("CAMBIO", 0.95), ("EQUIVALENTE", 0.9), ("CAMBIO", 0.55)
    assert s.combinar({"mdeberta": cambio, "minilm": cambio}) == (
        s.OBSERVACION,
        "CAMBIO",
    )
    assert s.combinar({"mdeberta": cambio, "minilm": igual}) == (s.REVISAR, "CAMBIO")
    assert s.combinar({"mdeberta": dudoso, "minilm": igual}) is None


def test_combinar_prefiere_la_contradiccion_de_mdeberta():
    veredicto = {"mdeberta": ("CONTRADICE", 0.9), "minilm": ("CAMBIO", 0.8)}
    assert s.combinar(veredicto) == (s.OBSERVACION, "CONTRADICE")
    veredicto = {"mdeberta": ("OMITE", 0.9), "minilm": ("AGREGA", 0.8)}
    assert s.combinar(veredicto) == (s.OBSERVACION, "AGREGA")


# --- Flujo completo ----------------------------------------------------------------------
def proyecto(*cambios):
    texto = MINUTA.replace(
        "MINUTA DE COMPRAVENTA. SEÑOR NOTARIO: SIRVASE EXTENDER LA PRESENTE.",
        "ESCRITURA PUBLICA.",
    )
    for de, a in cambios:
        texto = texto.replace(de, a)
    return texto


def anotar(minuta, borrador, clasificadores=CLASIFICADORES):
    return s.anotar(minuta, borrador, analizar, parecido, clasificadores)


def test_sin_cambios_no_hay_anotaciones():
    assert anotar(MINUTA, proyecto()) == []


def test_negacion_agregada_es_observacion():
    anotaciones = anotar(
        MINUTA, proyecto(("EL VENDEDOR SE OBLIGA", "EL VENDEDOR NO SE OBLIGA"))
    )
    assert len(anotaciones) == 1
    a = anotaciones[0]
    assert (a["nivel"], a["tipo"]) == (s.OBSERVACION, "CONTRADICE")
    assert "NO SE OBLIGA" in a["proyecto"] and "NO SE OBLIGA" not in a["minuta"]
    assert a["modelos"]["mdeberta"] == ["CONTRADICE", 0.95]


def test_un_solo_modelo_deja_para_revisar():
    clasificadores = {
        "mdeberta": nli_negacion,
        "minilm": lambda p: [(0.97, 0.02, 0.01)] * len(p),
    }
    anotaciones = anotar(
        MINUTA,
        proyecto(("EL VENDEDOR SE OBLIGA", "EL VENDEDOR NO SE OBLIGA")),
        clasificadores,
    )
    assert [a["nivel"] for a in anotaciones] == [s.REVISAR]


def test_clausula_sin_respaldo_en_la_minuta():
    agregada = (
        "CUARTA.- EL COMPRADOR RENUNCIA A TODA ACCION DE SANEAMIENTO POR EVICCION."
    )
    anotaciones = anotar(
        MINUTA, proyecto(("AGREGUE USTED", agregada + "\nAGREGUE USTED"))
    )
    assert [(a["nivel"], a["tipo"]) for a in anotaciones] == [
        (s.REVISAR, "SIN_RESPALDO")
    ]
    assert "RENUNCIA" in anotaciones[0]["proyecto"]
    assert anotaciones[0]["minuta"] == ""


def test_la_introduccion_de_la_minuta_cuenta_como_respaldo():
    """Una oración que el proyecto pone en las cláusulas pero la minuta en su
    introducción no es texto sin respaldo (búsqueda en la minuta completa)."""
    intro = "SEÑOR NOTARIO: SIRVASE EXTENDER LA PRESENTE."
    anotaciones = anotar(
        MINUTA, proyecto(("AGREGUE USTED", "CUARTA.- " + intro + "\nAGREGUE USTED"))
    )
    assert anotaciones == []


def test_parafrasis_que_los_modelos_ven_igual_no_se_anota():
    anotaciones = anotar(
        MINUTA, proyecto(("SE OBLIGA A ENTREGAR", "SE COMPROMETE A ENTREGAR"))
    )
    assert anotaciones == []


def test_modelos_neutrales_anotan_cambio():
    anotaciones = anotar(
        MINUTA,
        proyecto(("PAGARA LOS GASTOS", "PAGO LOS GASTOS")),
        {"mdeberta": nli_neutral, "minilm": nli_neutral},
    )
    assert [(a["nivel"], a["tipo"]) for a in anotaciones] == [(s.OBSERVACION, "CAMBIO")]


def test_anotar_es_reproducible_y_ordena_por_posicion():
    borrador = proyecto(
        ("EL VENDEDOR SE OBLIGA", "EL VENDEDOR NO SE OBLIGA"),
        ("QUE NO EXISTE DEUDA", "QUE EXISTE DEUDA"),
    )
    primera, segunda = anotar(MINUTA, borrador), anotar(MINUTA, borrador)
    assert primera == segunda
    assert [a["proyecto"][:7] for a in primera] == ["PRIMERA", "TERCERA"]


def test_sin_minuta_o_sin_proyecto_no_anota():
    assert anotar("", proyecto()) == []
    assert anotar(MINUTA, "") == []


def test_cifras_distintas_no_pasan_a_los_modelos():
    llamados = []

    def espia(pares):
        llamados.extend(pares)
        return nli_negacion(pares)

    anotar(
        MINUTA,
        proyecto(("ESTA ESCRITURA", "ESTA ESCRITURA N 25")),
        {"mdeberta": espia, "minilm": espia},
    )
    assert all("25" not in p for par in llamados for p in par)


# --- Concordancia (análisis gramatical) -----------------------------------------------
def _frase(*tokens):
    """tokens: (texto, pos, dep, rasgos, índice del núcleo o None)."""
    lista = [Token(t, i, p, d, r) for i, (t, p, d, r, _) in enumerate(tokens)]
    for tok, (*_, nucleo) in zip(lista, tokens):
        tok.head = lista[nucleo] if nucleo is not None else tok
        if nucleo is not None:
            lista[nucleo].children.append(tok)
    return lista


def test_concordancia_nominal_de_genero_y_numero():
    tokens = _frase(
        ("los", "DET", "det", {"Gender": "Masc", "Number": "Plur"}, 1),
        ("inmuebles", "NOUN", "ROOT", {"Gender": "Masc", "Number": "Plur"}, None),
        ("descrito", "ADJ", "amod", {"Gender": "Masc", "Number": "Sing"}, 1),
    )
    assert s.concordancias(tokens) == [("descrito", "inmuebles", "Number")]


def test_concordancia_ignora_modificador_lejano_y_coordinado():
    lejano = _frase(
        ("inmuebles", "NOUN", "ROOT", {"Number": "Plur"}, None),
        ("de", "ADP", "case", {}, 0),
        ("la", "DET", "det", {}, 0),
        ("zona", "NOUN", "nmod", {}, 0),
        ("descrito", "ADJ", "amod", {"Number": "Sing"}, 0),
    )
    assert s.concordancias(lejano) == []
    coordinado = _frase(
        ("casa", "NOUN", "ROOT", {"Gender": "Fem", "Number": "Sing"}, None),
        ("y", "CCONJ", "cc", {}, 2),
        ("terreno", "NOUN", "conj", {"Gender": "Masc", "Number": "Sing"}, 0),
        ("descritos", "ADJ", "amod", {"Gender": "Masc", "Number": "Plur"}, 0),
    )
    assert s.concordancias(coordinado) == []


def test_concordancia_sujeto_verbo():
    tokens = _frase(
        ("los", "DET", "det", {"Number": "Plur"}, 1),
        ("vendedores", "NOUN", "nsubj", {"Number": "Plur"}, 2),
        ("declara", "VERB", "ROOT", {"Number": "Sing", "VerbForm": "Fin"}, None),
    )
    assert s.concordancias(tokens) == [("vendedores", "declara", "Number")]


def test_anotar_incluye_concordancia_que_no_viene_de_la_minuta():
    def analizar_con_error(textos):
        docs = []
        for t in textos:
            doc = Doc(t)
            if "descrito" in t:
                doc.tokens = _frase(
                    ("inmuebles", "NOUN", "ROOT", {"Number": "Plur"}, None),
                    ("descrito", "ADJ", "amod", {"Number": "Sing"}, 0),
                )
            docs.append(doc)
        return docs

    borrador = proyecto(("SOBRE EL BIEN VENDIDO", "SOBRE LOS INMUEBLES DESCRITO"))
    anotaciones = s.anotar(
        MINUTA, borrador, analizar_con_error, parecido, CLASIFICADORES
    )
    concordancia = [a for a in anotaciones if a["tipo"] == "CONCORDANCIA"]
    assert len(concordancia) == 1
    assert concordancia[0]["nivel"] == s.REVISAR
    assert (
        concordancia[0]["detalle"]
        == "«descrito» no concuerda en número con «inmuebles»."
    )
    # el mismo error escrito en la minuta no se anota: lo trae el cliente
    assert not [
        a
        for a in s.anotar(
            MINUTA.replace("SOBRE EL BIEN VENDIDO", "SOBRE LOS INMUEBLES DESCRITO"),
            borrador,
            analizar_con_error,
            parecido,
            CLASIFICADORES,
        )
        if a["tipo"] == "CONCORDANCIA"
    ]


def test_concordancia_ignora_sujeto_lejano_del_verbo():
    """En oraciones largas el analizador une mal sujeto y verbo lejanos."""
    relleno = [("palabra", "NOUN", "nmod", {}, 1) for _ in range(4)]
    tokens = _frase(
        ("vendedores", "NOUN", "nsubj", {"Number": "Plur"}, 5),
        *relleno,
        ("declara", "VERB", "ROOT", {"Number": "Sing", "VerbForm": "Fin"}, None),
    )
    assert s.concordancias(tokens) == []


# --- F69: falsas alarmas por oraciones cortadas ----------------------------------------
def test_f69_esta_en_tolera_la_puntuacion_pegada_al_corte():
    doc = s.comparable("GIRADO POR EXPRESA INSTRUCCION DE EL MUTUATARIO DEL CONTRATO")
    assert s.esta_en("GIRADO POR EXPRESA INSTRUCCION DE EL.", doc)
    doc = s.comparable("LA EMPRESA FICTICIA S.A.C., IDENTIFICADA CON RUC EN LIMA")
    assert s.esta_en(", IDENTIFICADA CON RUC EN LIMA", doc)


def test_f69_esta_en_tolera_una_cifra_suelta():
    # Las cifras las juzgan las reglas, no esta capa.
    doc = s.comparable("LA PENALIDAD ES DE DOSCIENTOS POR CADA 1 DIA DE ATRASO")
    assert s.esta_en("LA PENALIDAD ES DE DOSCIENTOS POR CADA DIA DE ATRASO", doc)
    doc = s.comparable("LA PENALIDAD ES DE DOSCIENTOS POR CADA DIA DE ATRASO")
    assert s.esta_en("LA PENALIDAD ES DE DOSCIENTOS POR CADA 1", doc)


def test_f69_esta_en_tolera_una_letra_suelta_de_lectura():
    doc = s.comparable("EL BIEN ESTA LIBRE DE CARGAS Y GRAVAMENES EN LIMA")
    assert s.esta_en("EL BIEN ESTA LIBRE L DE CARGAS Y GRAVAMENES", doc)


def test_f69_esta_en_no_pierde_los_cambios_reales():
    doc = s.comparable(
        "EL VENDEDOR SE OBLIGA A ENTREGAR EL BIEN A LA FIRMA DE LA ESCRITURA"
    )
    # palabra quitada, en medio
    assert not s.esta_en("EL VENDEDOR NO SE OBLIGA A ENTREGAR EL BIEN", doc)
    # última palabra cambiada, aunque esté en el borde del corte
    assert not s.esta_en("EL VENDEDOR SE OBLIGA A ENTREGAR EL COMPRADOR", doc)
    # primera palabra cambiada
    assert not s.esta_en("COMPRADOR SE OBLIGA A ENTREGAR EL BIEN", doc)
    # conjunción: una letra suelta que sí cambia el sentido
    doc = s.comparable("PAGARA EN EFECTIVO O CON CHEQUE DE GERENCIA EN LIMA")
    assert not s.esta_en("PAGARA EN EFECTIVO Y CON CHEQUE DE GERENCIA", doc)
    # varias palabras en medio
    doc = s.comparable("LA SUMA SE ENTREGA MEDIANTE CHEQUE A LA FIRMA")
    assert not s.esta_en(
        "LA SUMA SE ENTREGA CON GARANTIA HIPOTECARIA MEDIANTE CHEQUE", doc
    )


def test_f69_tramos_muestran_solo_lo_que_cambia():
    largo = "UNA DOS TRES CUATRO CINCO SEIS SIETE OCHO NUEVE DIEZ ONCE DOCE "
    minuta = largo + "EL VENDEDOR NO SE OBLIGA A ENTREGAR " + largo
    proyecto = largo + "EL VENDEDOR SE OBLIGA A ENTREGAR " + largo
    tramos_m, tramos_p = s.tramos_de_cambio(minuta, proyecto)
    assert [t for t, distinto in tramos_m if distinto] == ["NO"]
    assert [t for t, distinto in tramos_p if distinto] == []
    visible = "".join(t for t, _ in tramos_m)
    assert visible.startswith("… ")
    assert visible.endswith(" …")
    assert "EL VENDEDOR NO SE OBLIGA" in visible
    assert len(visible.split()) < len(minuta.split()) / 2


def test_f69_tramos_no_resaltan_cifras_ni_letras_mal_leidas():
    tramos_m, tramos_p = s.tramos_de_cambio(
        "LA PENALIDAD POR CADA 1 DIA EI VENDEDOR PAGARA",
        "LA PENALIDAD POR CADA DIA EL VENDEDOR PAGARA.",
    )
    assert not [t for t, distinto in tramos_m if distinto]
    assert not [t for t, distinto in tramos_p if distinto]


def test_f69_tramos_sin_minuta_recorta_el_proyecto():
    largo = " ".join(f"PALABRA{i}" for i in range(60))
    tramos_m, tramos_p = s.tramos_de_cambio("", largo)
    assert tramos_m == []
    assert "".join(t for t, _ in tramos_p).endswith(" …")
    assert len("".join(t for t, _ in tramos_p).split()) <= 31


def test_f69_tramos_no_resaltan_lo_anterior_a_un_corte_con_signo():
    tramos_m, tramos_p = s.tramos_de_cambio(
        "LA EMPRESA FICTICIA DE LIMA, IDENTIFICADA CON RUC EN LA CIUDAD DE TRUJILLO",
        ", IDENTIFICADA CON RUC EN LA CIUDAD DE TRUJILLO",
    )
    assert not [t for t, distinto in tramos_m if distinto]
    assert not [t for t, distinto in tramos_p if distinto]


def test_f69_tramos_resaltan_lo_agregado_al_final_si_no_hay_otra_diferencia():
    base = "EL PAGO SE HARA MEDIANTE CHEQUE DE GERENCIA"
    tramos_m, tramos_p = s.tramos_de_cambio(base, base + " NO NEGOCIABLE")
    assert [t for t, distinto in tramos_p if distinto] == ["NO NEGOCIABLE"]
    assert not [t for t, distinto in tramos_m if distinto]
    # Con otra diferencia en medio, lo del borde se toma como otro corte.
    tramos_m, tramos_p = s.tramos_de_cambio(
        "EL VENDEDOR NO PAGARA LOS GASTOS DE LA ESCRITURA",
        "EL VENDEDOR PAGARA LOS GASTOS DE LA ESCRITURA PUBLICA Y SUS TRASLADOS",
    )
    assert [t for t, distinto in tramos_m if distinto] == ["NO"]
    assert not [t for t, distinto in tramos_p if distinto]
