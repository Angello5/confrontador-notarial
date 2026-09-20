"""Carga del diccionario y lista local de términos de la casa."""

from functools import lru_cache
from pathlib import Path

DIC = Path.home() / ".cache" / "notaria-ocr" / "es_PE"

# Conservado para el shim histórico; el adaptador no descarga recursos.
URL = "https://raw.githubusercontent.com/LibreOffice/dictionaries/32b006a2c22a4ac7e8ed3f03346f7b3d85a970a4/es/es_PE"

LISTA = Path(__file__).resolve().parents[1] / "lista_notarial.txt"


class DiccionarioNoAprovisionado(RuntimeError):
    """El diccionario es_PE debe existir antes de iniciar el servicio."""


@lru_cache(maxsize=1)
def diccionario():
    """(hunspell, lemas). Cacheado: cargarlo cuesta 0.3 s y 55 MB."""
    from spylls.hunspell import Dictionary

    if not all(DIC.with_suffix(ext).is_file() for ext in (".aff", ".dic")):
        raise DiccionarioNoAprovisionado(
            "Falta aprovisionar el diccionario es_PE antes de iniciar el servicio."
        )
    d = Dictionary.from_files(str(DIC))
    return d, [w.stem for w in d.dic.words]


def lista_casa() -> set[str]:
    """Terminos que el diccionario general no trae pero la notaria usa."""
    if not LISTA.exists():
        return set()
    return {
        linea.split("#")[0].strip().upper()
        for linea in LISTA.read_text(encoding="utf-8").splitlines()
        if linea.split("#")[0].strip()
    }


def agregar_a_lista(palabras) -> int:
    """Guarda terminos aceptados. Devuelve cuantos se agregaron de verdad."""
    ya = lista_casa()
    nuevas = sorted({p.strip().upper() for p in palabras if p.strip()} - ya)
    if nuevas:
        with LISTA.open("a", encoding="utf-8") as f:
            if not LISTA.stat().st_size:
                f.write(
                    "# Terminos aceptados por la notaria: siglas, juridico, toponimos.\n"
                )
            f.write("\n".join(nuevas) + "\n")
    return len(nuevas)
