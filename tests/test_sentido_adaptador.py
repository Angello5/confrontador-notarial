"""F61 · Adaptador de modelos de la capa de sentido, con dobles (sin modelos reales)."""

import hashlib
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from adaptadores import modelos_sentido as ms


def _manifiesto(carpeta, contenido=b"modelo ficticio"):
    datos = {
        "version": "2099-01-01",
        "spacy": {"paquete": "es_ficticio", "version": "1.0"},
    }
    for clave in ("e5", "mdeberta", "minilm"):
        datos[clave] = {"relleno": "<pad>", "etiquetas": [2, 1, 0]}
        for campo in ("onnx", "vocabulario"):
            nombre = f"{clave}.{campo}"
            (carpeta / nombre).write_bytes(contenido)
            datos[clave][campo] = nombre
            datos[clave][f"sha256_{campo}"] = hashlib.sha256(contenido).hexdigest()
    return datos


def test_manifiesto_del_repositorio_fija_las_huellas():
    datos = ms.leer_manifiesto()
    assert datos["spacy"]["paquete"] == "es_core_news_md"
    for clave in ("e5", "mdeberta", "minilm"):
        assert len(datos[clave]["sha256_onnx"]) == 64
        assert len(datos[clave]["sha256_vocabulario"]) == 64
    assert ms.version().startswith(datos["version"] + "+")


def test_version_cambia_si_cambia_una_huella(tmp_path):
    datos = _manifiesto(tmp_path)
    otra = {**datos, "e5": {**datos["e5"], "sha256_onnx": "0" * 64}}
    assert ms.version(datos) != ms.version(otra)


def test_verificar_detecta_faltante_y_huella_distinta(tmp_path):
    datos = _manifiesto(tmp_path)
    assert ms.verificar(tmp_path, datos) == []
    assert ms.faltantes(tmp_path, datos) == []
    (tmp_path / "e5.onnx").unlink()
    (tmp_path / "minilm.onnx").write_bytes(b"alterado")
    assert ms.verificar(tmp_path, datos) == [
        "e5.onnx: no está",
        "minilm.onnx: huella distinta",
    ]
    assert ms.faltantes(tmp_path, datos) == ["e5.onnx"]


def test_cargar_rechaza_modelos_incompletos(tmp_path):
    datos = _manifiesto(tmp_path)
    (tmp_path / "mdeberta.vocabulario").unlink()
    with pytest.raises(ms.ModelosNoDisponibles, match="mdeberta.vocabulario"):
        ms.Modelos.cargar(tmp_path, manifiesto=datos)


# --- Dobles de ONNX Runtime, tokenizers y spaCy --------------------------------------
class Codificado(SimpleNamespace):
    pass


class Tokenizador:
    """Un token por palabra; el id es la longitud de la palabra."""

    def encode_batch(self, textos):
        filas = [" ".join(t) if isinstance(t, tuple) else t for t in textos]
        largo = max(len(f.split()) for f in filas)
        return [
            Codificado(
                ids=[len(p) for p in f.split()] + [0] * (largo - len(f.split())),
                attention_mask=[1] * len(f.split()) + [0] * (largo - len(f.split())),
            )
            for f in filas
        ]


class SesionE5:
    """Vector oculto por token: [id, 1]; el relleno no debe contar en la media."""

    def run(self, _salidas, entradas):
        ids = entradas["input_ids"].astype(float)
        return [
            np.stack([ids, np.ones_like(ids)], axis=-1)
            + (1 - entradas["attention_mask"])[..., None] * 99
        ]


class SesionNLI:
    def run(self, _salidas, entradas):
        n = len(entradas["input_ids"])
        return [np.tile(np.array([[0.0, 1.0, 3.0]]), (n, 1))]


def _modelos(etiquetas=(2, 1, 0)):
    nlp = SimpleNamespace(pipe=lambda textos: [f"doc:{t}" for t in textos])
    nli = {n: (SesionNLI(), Tokenizador(), list(etiquetas)) for n in ms.NLI}
    return ms.Modelos(nlp, (SesionE5(), Tokenizador()), nli)


def test_analizar_usa_spacy():
    assert _modelos().analizar(["uno", "dos"]) == ["doc:uno", "doc:dos"]


def test_parecido_es_coseno_con_media_sin_relleno():
    sims = np.array(_modelos().parecido(["aa", "aa bbbbbbbbbb"], ["aa", "c"]))
    assert sims.shape == (2, 2)
    assert sims[0, 0] == pytest.approx(1.0)  # misma frase
    assert sims[1, 0] < 1.0
    assert np.all(sims <= 1.0 + 1e-9)


def test_parecido_procesa_por_lotes():
    frases = [f"frase {'x' * k}" for k in range(1, ms.LOTE_E5 * 2 + 2)]
    assert np.array(_modelos().parecido(frases, ["x"])).shape == (len(frases), 1)


def test_clasificar_softmax_en_orden_implica_neutral_contradice():
    probs = _modelos(etiquetas=(2, 1, 0)).clasificadores["mdeberta"]([("a", "b")] * 20)
    assert len(probs) == 20
    implica, neutral, contradice = probs[0]
    assert implica > neutral > contradice
    assert sum(probs[0]) == pytest.approx(1.0)
    assert set(_modelos().clasificadores) == {"mdeberta", "minilm"}


def test_cargar_arma_los_modelos_con_las_fabricas(tmp_path):
    datos = _manifiesto(tmp_path)
    llamadas = []

    def sesion(ruta, hilos):
        llamadas.append((ruta.name, hilos))
        return SesionNLI()

    modelos = ms.Modelos.cargar(
        tmp_path,
        hilos=2,
        manifiesto=datos,
        sesion=sesion,
        tokenizador=lambda ruta, relleno: Tokenizador(),
        spacy=lambda paquete, version: SimpleNamespace(pipe=lambda t: list(t)),
    )
    assert sorted(llamadas) == [
        ("e5.onnx", 2),
        ("mdeberta.onnx", 2),
        ("minilm.onnx", 2),
    ]
    assert set(modelos.nli) == {"mdeberta", "minilm"}
    assert modelos.nli["minilm"][2] == [2, 1, 0]


def test_sesion_onnx_con_hilos_fijos_y_cpu(monkeypatch, tmp_path):
    creadas = []
    ort = SimpleNamespace(
        SessionOptions=SimpleNamespace,
        ExecutionMode=SimpleNamespace(ORT_SEQUENTIAL="secuencial"),
        GraphOptimizationLevel=SimpleNamespace(ORT_ENABLE_ALL="todo"),
        InferenceSession=lambda ruta, opciones, providers: creadas.append(
            (ruta, opciones, providers)
        ),
    )
    monkeypatch.setitem(sys.modules, "onnxruntime", ort)
    ms._sesion(tmp_path / "m.onnx", 3)
    ruta, opciones, proveedores = creadas[0]
    assert ruta.endswith("m.onnx") and proveedores == ["CPUExecutionProvider"]
    assert (opciones.intra_op_num_threads, opciones.inter_op_num_threads) == (3, 1)
    assert opciones.execution_mode == "secuencial"


def test_tokenizador_trunca_a_512_y_rellena(monkeypatch, tmp_path):
    class Tok:
        @classmethod
        def from_file(cls, ruta):
            tok = cls()
            tok.ruta, tok.config = ruta, {}
            return tok

        def token_to_id(self, token):
            return {"<pad>": 1}[token]

        def enable_truncation(self, max_length):
            self.config["truncar"] = max_length

        def enable_padding(self, pad_id, pad_token):
            self.config["relleno"] = (pad_id, pad_token)

    monkeypatch.setitem(sys.modules, "tokenizers", SimpleNamespace(Tokenizer=Tok))
    tok = ms._tokenizador(tmp_path / "t.json", "<pad>")
    assert tok.config == {"truncar": 512, "relleno": (1, "<pad>")}


def test_spacy_exige_la_version_del_manifiesto(monkeypatch):
    cargados = []

    def load(paquete, exclude):
        cargados.append((paquete, exclude))
        return SimpleNamespace(meta={"version": "3.8.0"})

    monkeypatch.setitem(sys.modules, "spacy", SimpleNamespace(load=load))
    assert ms._spacy("es_core_news_md", "3.8.0").meta["version"] == "3.8.0"
    assert cargados == [("es_core_news_md", ["ner"])]
    with pytest.raises(ms.ModelosNoDisponibles):
        ms._spacy("es_core_news_md", "9.9.9")
