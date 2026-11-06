"""F61 · Capa de sentido: ¿el proyecto dice lo mismo que la minuta?

Compara cada oración del cuerpo de cláusulas de la minuta con la del proyecto y
anota los cambios de sentido (una negación, otra parte, una condición quitada o
agregada, otro tiempo verbal), el texto del proyecto sin respaldo en la minuta y
la concordancia de género y número. No decide datos duros ni toca el documento:
sus anotaciones son de apoyo y van en una sección propia (constitución, I).

Funciones puras. Los modelos llegan como funciones (adaptadores/modelos_sentido.py):

- ``analizar(textos)``: análisis gramatical (spaCy); documentos con ``sents``
  (``start_char``, ``end_char``) y tokens con ``text``, ``i``, ``pos_``, ``dep_``,
  ``morph``, ``head`` y ``children``.
- ``parecido(a, b)``: matriz de cosenos entre las frases de ``a`` y las de ``b``.
- ``clasificadores``: ``{nombre: f(pares)}`` que devuelve, por par (premisa,
  hipótesis), las probabilidades (implica, neutral, contradice).
"""

import re
import unicodedata
from difflib import SequenceMatcher

from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein

UMBRAL_SEGURIDAD = 0.6  # por debajo, el modelo no ve el cambio
UMBRAL_PAREJA = 0.9  # coseno mínimo para aceptar la oración más parecida
UMBRAL_LEXICO = 70  # o, si no llega, palabras en común (token_set_ratio)
MIN_PAGINAS_MEMBRETE = 3
MAX_DISTANCIA_SUJETO = 3  # más lejos, el analizador une mal sujeto y verbo
MIN_PALABRAS = 6
MAX_PALABRAS = 150
OBSERVACION = "OBSERVACION"
REVISAR = "REVISAR"
RASGOS = {"Gender": "género", "Number": "número"}

RE_CIFRA = re.compile(r"\d[\d.,/:°ºª-]*")
RE_ROTULO = re.compile(
    r"(?<!\w)((?:PRIMER|SEGUND|TERCER|CUART|QUINT|SEXT|S[EÉ]PTIM|OCTAV|NOVEN|"
    r"D[EÉ]CIM|UND[EÉ]CIM|DUOD[EÉ]CIM)[OA]S?)\s*[.:-]",
    re.IGNORECASE,
)
# Letra, cifra, «_» o «#»: lo que queda de una palabra al quitarle sus bordes.
RE_CARACTER_DE_PALABRA = re.compile(r"[\w#]")
LETRAS_CON_SENTIDO = frozenset("YOAEU")
PALABRAS_DE_CONTEXTO = 5
MAX_PALABRAS_SIN_CAMBIO = 30
RE_RELLENO = re.compile(r"[=_~*]{2,}|-{3,}")  # líneas de relleno del proyecto notarial
RE_PIE = re.compile(r"P[AÁ]GINA\s+\d+\s+DE\s+\d+", re.IGNORECASE)
RE_FIN_CLAUSULAS = re.compile(r"AGREGUE\s+USTED|CONCLUSI[OÓ]N", re.IGNORECASE)
# Al inicio de una oración: rótulo de cláusula, inciso «# NOMBRE:» y marcas de
# lista («A)», «1.», «II)», «-»). Cambian al numerar distinto, no el sentido.
RE_MARCAS = re.compile(
    r"^(?:\s|:|(?:PRIMER|SEGUND|TERCER|CUART|QUINT|SEXT|SEPTIM|OCTAV|NOVEN|DECIM|"
    r"UNDECIM|DUODECIM)[OA]S?\s*[.:-]+|#\s+(?:[A-ZÑ]+\s?){1,5}:|(?:[A-Z]|[IVX]{1,4}|#)[).]"
    r"(?=\s)|#(?=\s)|[-•·*](?=\s))+"
)
# Cifras en letras: «(CIEN MIL CON 00/100 SOLES)» que la notaría agrega junto al número.
NUMEROS = frozenset(
    "DOS TRES CUATRO CINCO SEIS SIETE OCHO NUEVE DIEZ ONCE DOCE TRECE CATORCE QUINCE "
    "DIECISEIS DIECISIETE DIECIOCHO DIECINUEVE VEINTE VEINTIUN VEINTIUNO VEINTIUNA "
    "VEINTIDOS VEINTITRES VEINTICUATRO VEINTICINCO VEINTISEIS VEINTISIETE VEINTIOCHO "
    "VEINTINUEVE TREINTA CUARENTA CINCUENTA SESENTA SETENTA OCHENTA NOVENTA CIEN CIENTO "
    "DOSCIENTOS DOSCIENTAS TRESCIENTOS TRESCIENTAS CUATROCIENTOS CUATROCIENTAS QUINIENTOS "
    "QUINIENTAS SEISCIENTOS SEISCIENTAS SETECIENTOS SETECIENTAS OCHOCIENTOS OCHOCIENTAS "
    "NOVECIENTOS NOVECIENTAS MIL MILLON MILLONES CERO".split()
)
ENLACES_CIFRA = frozenset(
    "Y CON UN UNO UNA # SOLES SOL DOLARES DOLAR AMERICANOS AMERICANO NUEVOS EUROS "
    "CENTIMOS S/ US$ M.N".split()
)


# --- Texto ---------------------------------------------------------------------------
def sin_borde(palabra):
    """La palabra sin los signos de sus extremos («,PERO.» -> «PERO»)."""
    inicio, fin = 0, len(palabra)
    while inicio < fin and not RE_CARACTER_DE_PALABRA.match(palabra[inicio]):
        inicio += 1
    while fin > inicio and not RE_CARACTER_DE_PALABRA.match(palabra[fin - 1]):
        fin -= 1
    return palabra[inicio:fin]


def plano(texto):
    """Mayúsculas, sin tildes, cifras ni espacios dobles."""
    t = unicodedata.normalize("NFKD", texto.upper())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(RE_CIFRA.sub("#", t).split())


def para_modelo(texto):
    """Minúsculas (los modelos se entrenaron con texto normal) y cifras neutras:
    las cifras las juzgan las reglas."""
    return RE_CIFRA.sub("0", texto).lower()


def _sin_cifras_en_letras(palabras):
    """Quita los tramos de dos o más palabras que escriben una cifra en letras."""
    salida, i = [], 0
    while i < len(palabras):
        limpia = palabras[i].strip("().,;:")
        if limpia not in NUMEROS:
            salida.append(palabras[i])
            i += 1
            continue
        fin = i
        while fin < len(palabras) and (
            palabras[fin].strip("().,;:") in NUMEROS | ENLACES_CIFRA
        ):
            fin += 1
        if fin - i < 2:
            salida.append(palabras[i])
            fin = i + 1
        i = fin
    return salida


def comparable(texto):
    """Plano, sin marcas al inicio ni cifras en letras: lo que se compara."""
    t = RE_MARCAS.sub("", plano(texto))
    return " ".join(_sin_cifras_en_letras(t.split()))


def limpiar(texto):
    """Quita el relleno «=====» y los pies de página: es formato, no contenido."""
    return RE_PIE.sub(" ", RE_RELLENO.sub(" ", texto))


def sin_membrete(texto):
    """Quita las líneas que se repiten en tres páginas o más (membrete del escaneo)."""
    paginas = texto.split("\f")
    if len(paginas) < MIN_PAGINAS_MEMBRETE:
        return texto
    cuenta = {}
    for pagina in paginas:
        for linea in {plano(x) for x in pagina.splitlines()}:
            if len(linea.split()) >= 3:
                cuenta[linea] = cuenta.get(linea, 0) + 1
    repetidas = {linea for linea, n in cuenta.items() if n >= MIN_PAGINAS_MEMBRETE}
    if not repetidas:
        return texto
    return "\f".join(
        "\n".join(x for x in pagina.splitlines() if plano(x) not in repetidas)
        for pagina in paginas
    )


def cuerpo(texto):
    """De la primera cláusula («PRIMERA.-») al cierre («AGREGUE USTED»).

    La introducción (comparecencia, datos de RENIEC) la revisan las reglas."""
    inicio = RE_ROTULO.search(texto)
    if not inicio:
        return texto
    fin = RE_FIN_CLAUSULAS.search(texto, inicio.start())
    return texto[inicio.start() : fin.start() if fin else len(texto)]


def unidades(texto, analizar):
    """Oraciones de 6 a 150 palabras, con su texto original."""
    texto = texto.replace("\f", "\n\n")
    texto = re.sub(r"(?<![.;:!?])\n(?!\n)", " ", texto)  # línea cortada por el OCR
    texto = RE_ROTULO.sub(lambda m: "\n" + m.group(0), texto)
    parrafos = [" ".join(p.split()) for p in texto.split("\n")]
    parrafos = [p for p in parrafos if len(p.split()) >= MIN_PALABRAS]
    salida = []
    for parrafo, doc in zip(parrafos, analizar([p.lower() for p in parrafos])):
        for oracion in doc.sents:
            original = parrafo[oracion.start_char : oracion.end_char]
            for trozo in re.split(r"(?<=;)\s+", original):
                palabras = trozo.split()
                for i in range(0, len(palabras), MAX_PALABRAS):
                    if len(palabras[i : i + MAX_PALABRAS]) >= MIN_PALABRAS:
                        salida.append(" ".join(palabras[i : i + MAX_PALABRAS]))
    return salida


# --- ¿Solo cambió la lectura? -----------------------------------------------------------
def misma_palabra(p, q):
    """Dos palabras que solo difieren por letras mal leídas."""
    if {"#", "/"} & set(p) and {"#", "/"} & set(q):
        return True  # cifras: las revisan las reglas («00/100» leído «oo/1oo»)
    if min(len(p), len(q)) == 1 or "NO" in (p, q):
        return p == q  # F69: «Y»/«O» y «NO»/«LO» cambian el sentido
    if len(p) == len(q) and Levenshtein.distance(p, q) <= 1:
        return True  # «EI»/«EL»
    return abs(len(p) - len(q)) <= 1 and fuzz.ratio(p, q) >= 70


def _iguales_salvo_lectura(x, y):
    return len(x) == len(y) and all(map(misma_palabra, x, y))


def solo_lectura(a, b):
    """¿Dos oraciones difieren solo por letras mal leídas dentro de una palabra?

    Una palabra agregada, quitada o reemplazada por otra («NO», «VENDEDOR» →
    «COMPRADOR», «PAGARÁ» → «PAGÓ») es un cambio de contenido."""
    x, y = comparable(a).split(), comparable(b).split()
    for op, i1, i2, j1, j2 in SequenceMatcher(None, x, y, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        if op != "replace" or not _iguales_salvo_lectura(x[i1:i2], y[j1:j2]):
            return False
    return True


def _sin_signos(palabras):
    """F69: sin la puntuación pegada al corte («EL.» es «EL»; «,» no es palabra)."""
    limpias = (sin_borde(p) for p in palabras)
    return [p for p in limpias if p]


def _sin_contenido(palabras):
    """F69: cifras (las juzgan las reglas) y letras sueltas de lectura; «Y» u «O» no."""
    return all(
        "#" in p or (len(p) == 1 and p not in LETRAS_CON_SENTIDO) for p in palabras
    )


def esta_en(texto, doc):
    """¿La oración está en el documento (ya pasado por ``comparable``) palabra por
    palabra, salvo letras mal leídas? Distingue un corte de oración distinto de un
    cambio real: una palabra agregada o quitada no está en el documento."""
    t = comparable(texto)
    if t in doc:
        return True
    al = fuzz.partial_ratio_alignment(t, doc)
    if al is None or al.score < 80:
        return False
    # ventana holgada hasta límites de palabra: lo que sobra en los bordes no cuenta
    ini = doc.rfind(" ", 0, max(0, al.dest_start - 30)) + 1
    fin = doc.find(" ", min(len(doc), al.dest_end + 30))
    x = _sin_signos(t.split())
    ventana = _sin_signos(doc[ini : fin if fin >= 0 else len(doc)].split())
    for op, i1, i2, j1, j2 in SequenceMatcher(
        None, x, ventana, autojunk=False
    ).get_opcodes():
        if op == "equal" or (op == "insert" and (j1 == 0 or j2 == len(ventana))):
            continue
        if op == "replace" and _iguales_salvo_lectura(x[i1:i2], ventana[j1:j2]):
            continue
        # F69: una cifra o letra suelta en medio, o cifra en el borde del corte
        if op == "insert" and _sin_contenido(ventana[j1:j2]):
            continue
        if op == "delete" and _sin_contenido(x[i1:i2]):
            continue
        if op == "replace" and _sin_contenido(x[i1:i2]) and (i1 == 0 or i2 == len(x)):
            continue
        return False
    return True


# --- Lo que se muestra ----------------------------------------------------------------
def _tramos(palabras, foco, marcadas):
    """(texto, ¿distinto?) de las palabras en ``foco``; lo demás se resume con «…»."""
    tramos, previa = [], -1
    for i in sorted(foco):
        separador = " " if tramos else ""
        if i > previa + 1:
            separador = " … " if tramos else "… "
        distinto = i in marcadas
        if tramos and tramos[-1][1] == distinto and separador == " ":
            tramos[-1] = (tramos[-1][0] + " " + palabras[i], distinto)
        elif distinto or separador.strip():
            if separador:
                tramos.append((separador, False))
            tramos.append((palabras[i], distinto))
        else:
            tramos.append((separador + palabras[i], False))
        previa = i
    if tramos and previa < len(palabras) - 1:
        tramos.append((" …", False))
    return tramos


def tramos_de_cambio(minuta, proyecto):
    """F69: los dos textos reducidos a lo que cambia, con unas palabras de contexto.

    Mismo criterio que ``esta_en``: la puntuación, las cifras sueltas, las letras
    mal leídas y lo que sigue tras un corte de oración no se resaltan."""
    a, b = minuta.split(), proyecto.split()
    if not a:
        foco = range(min(len(b), MAX_PALABRAS_SIN_CAMBIO))
        return [], _tramos(b, foco, set())
    x = [sin_borde(plano(p)) for p in a]
    y = [sin_borde(plano(p)) for p in b]
    foco_a, foco_b, marca_a, marca_b = set(), set(), set(), set()
    en_borde = []

    def marcar(i1, i2, j1, j2):
        marca_a.update(range(i1, i2))
        marca_b.update(range(j1, j2))
        foco_a.update(
            range(
                max(0, i1 - PALABRAS_DE_CONTEXTO),
                min(len(a), i2 + PALABRAS_DE_CONTEXTO),
            )
        )
        foco_b.update(
            range(
                max(0, j1 - PALABRAS_DE_CONTEXTO),
                min(len(b), j2 + PALABRAS_DE_CONTEXTO),
            )
        )

    for op, i1, i2, j1, j2 in SequenceMatcher(None, x, y, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        if op == "replace" and _iguales_salvo_lectura(x[i1:i2], y[j1:j2]):
            continue
        if _sin_contenido([p for p in x[i1:i2] + y[j1:j2] if p]):
            continue
        # un texto que empieza a media frase («, IDENTIFICADO…»): solo había un signo
        if (i1 == 0 and not any(y[j1:j2])) or (j1 == 0 and not any(x[i1:i2])):
            continue
        if (op == "insert" and i1 in (0, len(x))) or (
            op == "delete" and j1 in (0, len(y))
        ):
            en_borde.append((i1, i2, j1, j2))  # puede ser solo otro corte de oración
            continue
        marcar(i1, i2, j1, j2)
    if not marca_a and not marca_b:
        # Sin otra diferencia, lo de los bordes es justo lo que el aviso señala.
        for tramo in en_borde:
            marcar(*tramo)
    if not foco_a and not foco_b:
        foco_a = set(range(min(len(a), MAX_PALABRAS_SIN_CAMBIO)))
        foco_b = set(range(min(len(b), MAX_PALABRAS_SIN_CAMBIO)))
    return _tramos(a, foco_a, marca_a), _tramos(b, foco_b, marca_b)


# --- Veredicto ------------------------------------------------------------------------
def relacion(ida, vuelta):
    """ida: minuta ⇒ proyecto; vuelta: proyecto ⇒ minuta. Devuelve (tipo, seguridad)."""
    contradice = max(ida[2], vuelta[2])
    if contradice >= 0.5:
        return "CONTRADICE", contradice
    if ida[0] >= 0.5 and vuelta[0] >= 0.5:
        return "EQUIVALENTE", min(ida[0], vuelta[0])
    if ida[0] >= 0.5:  # la minuta dice más: el proyecto omite
        return "OMITE", 1 - vuelta[0]
    if vuelta[0] >= 0.5:  # el proyecto dice más: agrega
        return "AGREGA", 1 - ida[0]
    return "CAMBIO", 1 - max(ida[0], vuelta[0])


def combinar(veredictos):
    """Observación si los dos modelos ven el cambio; «para revisar» si solo uno.

    MiniLM casi no da falsas alarmas; mDeBERTa ve más cambios de parte y de tiempo.
    Devuelve (nivel, tipo) o None."""
    vistos = [
        nombre
        for nombre, (tipo, seguridad) in veredictos.items()
        if tipo != "EQUIVALENTE" and round(seguridad, 3) >= UMBRAL_SEGURIDAD
    ]
    if not vistos:
        return None
    md = veredictos.get("mdeberta", ("EQUIVALENTE", 0.0))
    ml = veredictos.get("minilm", ("EQUIVALENTE", 0.0))
    tipo = md[0] if md[0] == "CONTRADICE" or "minilm" not in vistos else ml[0]
    return (OBSERVACION if len(vistos) >= 2 else REVISAR), tipo


# --- Flujo ---------------------------------------------------------------------------
def emparejar(M, B, parecido):
    """Por cada oración de la minuta: (índice en el proyecto, ¿idéntica?, ¿aceptada?).

    La copiada tal cual se empareja sin modelos; las demás con la más parecida."""
    indice = {}
    for j, u in enumerate(B):
        indice.setdefault(comparable(u), j)
    pareja = [None] * len(M)
    distintas = []
    for i, u in enumerate(M):
        j = indice.get(comparable(u))
        if j is None:
            distintas.append(i)
        else:
            pareja[i] = (j, True, True)
    if distintas:
        sims = parecido(
            [para_modelo(M[i]) for i in distintas], [para_modelo(u) for u in B]
        )
        for fila, i in zip(sims, distintas):
            j = max(range(len(B)), key=lambda k: fila[k])
            aceptada = (
                fila[j] >= UMBRAL_PAREJA
                or fuzz.token_set_ratio(plano(M[i]), plano(B[j])) >= UMBRAL_LEXICO
            )
            pareja[i] = (j, False, aceptada)
    return pareja


def _anotacion(posicion, nivel, tipo, minuta="", proyecto="", detalle="", modelos=None):
    return {
        "posicion": posicion,
        "nivel": nivel,
        "tipo": tipo,
        "minuta": minuta,
        "proyecto": proyecto,
        "detalle": detalle,
        "modelos": modelos or {},
    }


def _cambios_de_sentido(M, B, pareja, minuta_toda, proyecto_todo, clasificadores):
    pares = [
        (i, j)
        for i, (j, identica, aceptada) in enumerate(pareja)
        if aceptada
        and not identica
        and not solo_lectura(M[i], B[j])
        and not (esta_en(M[i], proyecto_todo) and esta_en(B[j], minuta_toda))
    ]
    if not pares:
        return []
    textos = [(para_modelo(M[i]), para_modelo(B[j])) for i, j in pares]
    veredictos = [{} for _ in pares]
    for nombre, clasificar in clasificadores.items():
        probs = clasificar(textos + [(b, m) for m, b in textos])
        for k, veredicto in enumerate(veredictos):
            veredicto[nombre] = relacion(probs[k], probs[len(pares) + k])
    salida = []
    for (i, j), veredicto in zip(pares, veredictos):
        decision = combinar(veredicto)
        if decision:
            modelos = {n: [t, round(seg, 3)] for n, (t, seg) in veredicto.items()}
            salida.append(_anotacion(j, *decision, M[i], B[j], modelos=modelos))
    return salida


def _sin_respaldo(B, pareja, minuta_toda):
    """Oraciones seguidas del proyecto que no están en ninguna parte de la minuta."""
    usadas = {p[0] for p in pareja if p}
    bloques = []
    for j, u in enumerate(B):
        if j in usadas or esta_en(u, minuta_toda):
            continue
        if bloques and j == bloques[-1][-1] + 1:
            bloques[-1].append(j)
        else:
            bloques.append([j])
    return [
        _anotacion(b[0], REVISAR, "SIN_RESPALDO", proyecto=" ".join(B[j] for j in b))
        for b in bloques
    ]


def concordancias(doc):
    """[(palabra, núcleo, rasgo)] de concordancia nominal y sujeto–verbo."""
    salida = []
    for t in doc:
        nucleo = t.head
        # a lo más dos palabras del sustantivo: más lejos, el analizador suele unir mal
        modificador = abs(t.i - nucleo.i) <= 2 and (
            t.dep_ in ("det", "amod")
            or (t.dep_ == "acl" and "Part" in t.morph.get("VerbForm"))
        )
        coordinado = any(h.dep_ == "conj" for h in nucleo.children)
        if modificador and nucleo.pos_ == "NOUN" and not coordinado:
            rasgo = _rasgo_distinto(t, nucleo, ("Gender", "Number"))
            if rasgo:
                salida.append((t.text, nucleo.text, rasgo))
        conjugado = "Fin" in nucleo.morph.get("VerbForm")  # no participios en pasiva
        if (
            t.dep_ == "nsubj"
            and abs(t.i - nucleo.i) <= MAX_DISTANCIA_SUJETO
            and conjugado
            and t.pos_ == "NOUN"
            and not any(h.dep_ == "conj" for h in t.children)
            and _rasgo_distinto(t, nucleo, ("Number",))
        ):
            salida.append((t.text, nucleo.text, "Number"))
    return salida


def _rasgo_distinto(a, b, nombres):
    for nombre in nombres:
        x, y = a.morph.get(nombre), b.morph.get(nombre)
        if x and y and x[0] != y[0]:
            return nombre
    return None


def _concordancia(M, B, analizar):
    """Errores de concordancia del proyecto que no vienen escritos en la minuta."""
    en_minuta = {
        (palabra, nucleo)
        for doc in analizar([para_modelo(u) for u in M])
        for palabra, nucleo, _ in concordancias(doc)
    }
    salida = []
    for j, doc in enumerate(analizar([para_modelo(u) for u in B])):
        for palabra, nucleo, rasgo in concordancias(doc):
            if (palabra, nucleo) in en_minuta:
                continue
            en_minuta.add((palabra, nucleo))  # una vez por par de palabras
            detalle = f"«{palabra}» no concuerda en {RASGOS[rasgo]} con «{nucleo}»."
            salida.append(
                _anotacion(j, REVISAR, "CONCORDANCIA", proyecto=B[j], detalle=detalle)
            )
    return salida


def anotar(minuta, proyecto, analizar, parecido, clasificadores):
    """Anotaciones de sentido del proyecto frente a la minuta, en orden de lectura."""
    minuta, proyecto = (limpiar(sin_membrete(t or "")) for t in (minuta, proyecto))
    M = unidades(cuerpo(minuta), analizar)
    B = unidades(cuerpo(proyecto), analizar)
    if not M or not B:
        return []
    # búsqueda en la minuta completa: el proyecto puede llevar a las cláusulas lo
    # que la minuta dice en su introducción
    minuta_toda, proyecto_todo = comparable(minuta), comparable(proyecto)
    pareja = emparejar(M, B, parecido)
    anotaciones = [
        *_cambios_de_sentido(M, B, pareja, minuta_toda, proyecto_todo, clasificadores),
        *_sin_respaldo(B, pareja, minuta_toda),
        *_concordancia(M, B, analizar),
    ]
    return sorted(anotaciones, key=lambda a: (a["posicion"], a["nivel"] != OBSERVACION))
