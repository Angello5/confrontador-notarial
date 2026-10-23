"""F61 · Modelos de la capa de sentido, en CPU y sin red.

spaCy separa oraciones y hace el análisis gramatical; e5 empareja oraciones y dos
clasificadores NLI (mDeBERTa y MiniLM) dicen si implican, son neutrales o se
contradicen. Los tres modelos corren en ONNX Runtime (el motor del OCR), sin
PyTorch, en 32 bits y con hilos fijos: la misma entrada da la misma salida.

Cada archivo se verifica contra su SHA-256 del manifiesto antes de cargarlo. Las
bibliotecas se importan al cargar: el ERP no las necesita con la capa apagada.
"""

import hashlib
import tomllib
from pathlib import Path

MANIFIESTO = Path(__file__).with_name("modelos_sentido.toml")
NLI = ("mdeberta", "minilm")
LARGO_MAXIMO = 512
LOTE_NLI = 16
LOTE_E5 = 8


class ModelosNoDisponibles(RuntimeError):
    """Faltan modelos o alguno no coincide con su huella."""


def leer_manifiesto(ruta=MANIFIESTO):
    return tomllib.loads(Path(ruta).read_text(encoding="utf-8"))


def version(manifiesto=None):
    """Versión registrada en cada análisis: fecha y huella del manifiesto."""
    datos = leer_manifiesto() if manifiesto is None else manifiesto
    huella = hashlib.sha256(repr(sorted(_archivos(datos))).encode()).hexdigest()
    return f"{datos['version']}+{huella[:12]}"


def _archivos(manifiesto):
    """[(archivo, sha256)] de los modelos ONNX y sus tokenizadores."""
    return [
        (manifiesto[clave][campo], manifiesto[clave][f"sha256_{campo}"])
        for clave in ("e5", *NLI)
        for campo in ("onnx", "vocabulario")
    ]


def _sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def faltantes(carpeta, manifiesto=None):
    """Archivos que no están en la carpeta (sin calcular huellas: es rápido)."""
    datos = leer_manifiesto() if manifiesto is None else manifiesto
    return [
        nombre
        for nombre, _ in _archivos(datos)
        if not (Path(carpeta) / nombre).is_file()
    ]


def verificar(carpeta, manifiesto=None):
    """Archivos que faltan o cuya huella no coincide con el manifiesto."""
    datos = leer_manifiesto() if manifiesto is None else manifiesto
    problemas = []
    for nombre, esperado in _archivos(datos):
        ruta = Path(carpeta) / nombre
        if not ruta.is_file():
            problemas.append(f"{nombre}: no está")
        elif _sha256(ruta) != esperado:
            problemas.append(f"{nombre}: huella distinta")
    return problemas


def _sesion(ruta, hilos):
    import onnxruntime as ort

    opciones = ort.SessionOptions()
    opciones.intra_op_num_threads = hilos
    opciones.inter_op_num_threads = 1
    opciones.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    opciones.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(str(ruta), opciones, providers=["CPUExecutionProvider"])


def _tokenizador(ruta, relleno):
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(str(ruta))
    tok.enable_truncation(max_length=LARGO_MAXIMO)
    tok.enable_padding(pad_id=tok.token_to_id(relleno), pad_token=relleno)
    return tok


def _spacy(paquete, version_esperada):
    import spacy

    nlp = spacy.load(paquete, exclude=["ner"])
    if nlp.meta.get("version") != version_esperada:
        raise ModelosNoDisponibles(f"{paquete}: versión distinta de {version_esperada}")
    return nlp


def _entradas(codificados):
    import numpy as np

    return {
        "input_ids": np.array([c.ids for c in codificados], dtype=np.int64),
        "attention_mask": np.array(
            [c.attention_mask for c in codificados], dtype=np.int64
        ),
    }


class Modelos:
    """Los modelos cargados una vez por proceso (el worker los reutiliza)."""

    def __init__(self, nlp, e5, nli):
        self.nlp = nlp
        self.e5 = e5  # (sesión, tokenizador)
        self.nli = nli  # {nombre: (sesión, tokenizador, etiquetas)}

    @classmethod
    def cargar(
        cls,
        carpeta,
        hilos=3,
        manifiesto=None,
        sesion=_sesion,
        tokenizador=_tokenizador,
        spacy=_spacy,
    ):
        datos = leer_manifiesto() if manifiesto is None else manifiesto
        problemas = verificar(carpeta, datos)
        if problemas:
            raise ModelosNoDisponibles("; ".join(problemas))
        carpeta = Path(carpeta)

        def par(clave):
            m = datos[clave]
            return sesion(carpeta / m["onnx"], hilos), tokenizador(
                carpeta / m["vocabulario"], m["relleno"]
            )

        return cls(
            spacy(datos["spacy"]["paquete"], datos["spacy"]["version"]),
            par("e5"),
            {nombre: (*par(nombre), datos[nombre]["etiquetas"]) for nombre in NLI},
        )

    def analizar(self, textos):
        return list(self.nlp.pipe(textos))

    def _embeber(self, frases):
        import numpy as np

        sesion, tok = self.e5
        salida = []
        for i in range(0, len(frases), LOTE_E5):
            entradas = _entradas(
                tok.encode_batch(["query: " + f for f in frases[i : i + LOTE_E5]])
            )
            oculto = sesion.run(None, entradas)[0]
            mascara = entradas["attention_mask"][..., None]
            media = (oculto * mascara).sum(1) / mascara.sum(1)
            salida.append(media / np.linalg.norm(media, axis=1, keepdims=True))
        return np.concatenate(salida)

    def parecido(self, a, b):
        return (self._embeber(a) @ self._embeber(b).T).tolist()

    def _clasificar(self, nombre, pares):
        import numpy as np

        sesion, tok, etiquetas = self.nli[nombre]
        salida = []
        for i in range(0, len(pares), LOTE_NLI):
            logits = sesion.run(
                None, _entradas(tok.encode_batch(pares[i : i + LOTE_NLI]))
            )[0]
            e = np.exp(logits - logits.max(-1, keepdims=True))
            probs = e / e.sum(-1, keepdims=True)
            salida += [tuple(float(fila[k]) for k in etiquetas) for fila in probs]
        return salida

    @property
    def clasificadores(self):
        return {
            nombre: (lambda pares, n=nombre: self._clasificar(n, pares))
            for nombre in NLI
        }
