"""F61 · Exporta los modelos de la capa de sentido a ONNX (32 bits) y copia sus tokenizadores.

Se corre una vez, en un equipo de desarrollo con red y un entorno aparte con
PyTorch y transformers (no van en requirements*.txt):

    python scripts/exportar_modelos_sentido.py --destino ~/notaria-modelos/sentido

Imprime el SHA-256 de cada archivo. Los archivos entregados a la notaría son los
que fija adaptadores/modelos_sentido.toml: si se vuelven a exportar, las huellas
pueden cambiar, y entonces hay que actualizar el manifiesto y repetir la
validación de paridad con PyTorch (specs/043-capa-sentido/quickstart.md).
"""

import argparse
import hashlib
import shutil
import tomllib
from pathlib import Path

import torch
from huggingface_hub import hf_hub_download
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

MANIFIESTO = (
    Path(__file__).resolve().parents[1] / "adaptadores" / "modelos_sentido.toml"
)


class SoloOculto(torch.nn.Module):
    """e5 sin el resto de la salida de transformers: (input_ids, attention_mask) → oculto."""

    def __init__(self, modelo):
        super().__init__()
        self.modelo = modelo

    def forward(self, input_ids, attention_mask):
        return self.modelo(
            input_ids=input_ids, attention_mask=attention_mask
        ).last_hidden_state


def _ejemplo(repo, pares):
    """Las mismas entradas de ejemplo con que se validó la paridad (22/10/2026)."""
    tok = AutoTokenizer.from_pretrained(repo)
    if pares:
        enc = tok(["una cláusula de prueba"], ["otra cláusula"], return_tensors="pt")
    else:  # con relleno: el grafo conserva la máscara
        frases = [
            "una frase de prueba",
            "otra frase de prueba algo más larga que la primera",
        ]
        enc = tok(frases, padding=True, return_tensors="pt")
    return enc["input_ids"], enc["attention_mask"]


def exportar_nli(repo, ruta):
    modelo = AutoModelForSequenceClassification.from_pretrained(repo).float().eval()
    ejes = {0: "lote", 1: "largo"}
    torch.onnx.export(
        modelo,
        _ejemplo(repo, True),
        str(ruta),
        input_names=["input_ids", "attention_mask"],
        output_names=["salida"],
        dynamic_axes={"input_ids": ejes, "attention_mask": ejes, "salida": {0: "lote"}},
        opset_version=17,
        dynamo=False,
    )


def exportar_e5(repo, ruta):
    # el exportador por trazado deja la máscara fija (coseno 0,98): se usa dynamo
    modelo = AutoModel.from_pretrained(repo, attn_implementation="eager").float().eval()
    lote = torch.export.Dim("lote", min=1, max=64)
    largo = torch.export.Dim("largo", min=2, max=512)
    programa = torch.onnx.export(
        SoloOculto(modelo),
        _ejemplo(repo, False),
        dynamo=True,
        input_names=["input_ids", "attention_mask"],
        output_names=["salida"],
        dynamic_shapes={
            "input_ids": {0: lote, 1: largo},
            "attention_mask": {0: lote, 1: largo},
        },
    )
    programa.save(str(ruta))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, required=True)
    destino = parser.parse_args().destino.expanduser()
    destino.mkdir(parents=True, exist_ok=True)
    manifiesto = tomllib.loads(MANIFIESTO.read_text(encoding="utf-8"))
    for clave in ("e5", "mdeberta", "minilm"):
        datos = manifiesto[clave]
        repo, revision = datos["origen"].split("@")
        exportar = exportar_e5 if clave == "e5" else exportar_nli
        exportar(repo, destino / datos["onnx"])
        tokenizador = hf_hub_download(repo, "tokenizer.json", revision=revision)
        shutil.copyfile(tokenizador, destino / datos["vocabulario"])
        for campo in ("onnx", "vocabulario"):
            ruta = destino / datos[campo]
            huella = hashlib.sha256(ruta.read_bytes()).hexdigest()
            estado = "igual" if huella == datos[f"sha256_{campo}"] else "DISTINTA"
            print(f"{ruta.name}: {huella} ({estado} al manifiesto)")


if __name__ == "__main__":
    main()
