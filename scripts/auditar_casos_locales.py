"""Inventario privado y extracción segura de expedientes ZIP reales.

No imprime nombres de archivos ni contenido de documentos. Los archivos se
renombran al extraerlos y quedan bajo expedientes_locales/auditoria-20261002.
"""

from __future__ import annotations

import argparse
import json
import re
import stat
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
DESTINO = ROOT / "expedientes_locales" / "auditoria-20261002"
LIMITE_ARCHIVO = 50 * 1024 * 1024
LIMITE_TOTAL = 500 * 1024 * 1024
EXTENSIONES = {".docx", ".doc", ".pdf", ".txt", ".jpeg", ".jpg", ".png"}


def _clasificar_grupos(z: ZipFile, etiqueta: str):
    archivos = [i for i in z.infolist() if not i.is_dir()]
    grupos = defaultdict(list)
    for info in archivos:
        partes = Path(info.filename.replace("\\", "/")).parts
        if (
            not partes
            or any(p in {"", ".", ".."} for p in partes)
            or info.filename.startswith(("/", "\\"))
            or re.match(r"^[A-Za-z]:", info.filename)
            or info.flag_bits & 1
            or stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK
            or info.file_size > LIMITE_ARCHIVO
        ):
            raise ValueError("ZIP inseguro o archivo excede el límite")
        if Path(info.filename).suffix.lower() not in EXTENSIONES:
            raise ValueError("Formato no previsto en ZIP")
        clave = tuple(partes[:-1]) if etiqueta == "Casos" else (etiqueta,)
        grupos[clave].append(info)
    if sum(i.file_size for i in archivos) > LIMITE_TOTAL:
        raise ValueError("ZIP excede el límite total")
    return grupos


def _docx_caracteres(ruta: Path):
    # Cuenta texto XML sin volcar contenido; incluye cuadros de texto/encabezados.
    from defusedxml import ElementTree as ET

    total = 0
    with ZipFile(ruta) as z:
        for nombre in z.namelist():
            if nombre == "word/document.xml" or re.fullmatch(
                r"word/(header|footer)\d+\.xml", nombre
            ):
                raiz = ET.fromstring(z.read(nombre))
                total += sum(
                    len(n.text or "") for n in raiz.iter() if n.tag.endswith("}t")
                )
    return total


def _analizar(ruta: Path):
    sufijo = ruta.suffix.lower()
    try:
        if sufijo == ".pdf":
            with pymupdf.open(ruta) as lector:
                if lector.is_encrypted:
                    return {
                        "estado": "cifrado",
                        "paginas": 0,
                        "con_texto": 0,
                        "escasas": 0,
                        "sin_texto": 0,
                    }
                conteos = [len(p.get_text() or "") for p in lector]
            return {
                "estado": "leido",
                "paginas": len(conteos),
                "con_texto": sum(n >= 40 for n in conteos),
                "escasas": sum(0 < n < 40 for n in conteos),
                "sin_texto": sum(n == 0 for n in conteos),
            }
        if sufijo == ".docx":
            n = _docx_caracteres(ruta)
            return {"estado": "leido" if n else "sin_texto", "caracteres": n}
        if sufijo == ".txt":
            datos = ruta.read_bytes()
            for enc in ("utf-8-sig", "cp1252", "latin1"):
                try:
                    return {"estado": "leido", "caracteres": len(datos.decode(enc))}
                except UnicodeDecodeError:
                    pass
        return {"estado": "requiere_conversor_u_ocr"}
    except Exception as error:
        # Nunca propagar mensajes de biblioteca: pueden contener texto del documento.
        return {"estado": "error", "tipo_error": type(error).__name__}


def auditar(entradas: list[tuple[str, Path]]):
    DESTINO.mkdir(parents=True, exist_ok=True)
    resumen = []
    for etiqueta, origen in entradas:
        with ZipFile(origen) as z:
            grupos = _clasificar_grupos(z, etiqueta)
            for indice, clave in enumerate(sorted(grupos), 1):
                caso = etiqueta if etiqueta != "Casos" else f"C{indice:02d}"
                carpeta = DESTINO / caso
                carpeta.mkdir(parents=True, exist_ok=True)
                documentos = []
                for num, info in enumerate(
                    sorted(grupos[clave], key=lambda i: i.filename), 1
                ):
                    extension = Path(info.filename).suffix.lower()
                    destino = carpeta / f"D{num:03d}{extension}"
                    if destino.exists():
                        raise FileExistsError(
                            "El destino ya contiene un archivo de auditoría"
                        )
                    with z.open(info) as fuente, destino.open("xb") as salida:
                        import shutil

                        shutil.copyfileobj(fuente, salida, length=1024 * 1024)
                    estado = _analizar(destino)
                    documentos.append(
                        {"id": destino.stem, "formato": extension, **estado}
                    )
                resumen.append({"caso": caso, "documentos": documentos})
    ruta = DESTINO / "resumen.json"
    with ruta.open("x", encoding="utf-8") as salida:
        json.dump(resumen, salida, ensure_ascii=False, indent=2)
    return resumen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("caso_11", type=Path)
    parser.add_argument("caso_12", type=Path)
    parser.add_argument("casos", type=Path)
    args = parser.parse_args()
    datos = auditar(
        [
            ("C11", args.caso_11),
            ("C12", args.caso_12),
            ("Casos", args.casos),
        ]
    )
    for caso in datos:
        documentos = caso["documentos"]
        formatos = Counter(d["formato"] for d in documentos)
        pdf = [d for d in documentos if d["formato"] == ".pdf"]
        estados = Counter(d["estado"] for d in documentos)
        print(
            json.dumps(
                {
                    "caso": caso["caso"],
                    "archivos": len(documentos),
                    "formatos": formatos,
                    "estados": estados,
                    "paginas_pdf": sum(d.get("paginas", 0) for d in pdf),
                    "paginas_con_texto": sum(d.get("con_texto", 0) for d in pdf),
                    "paginas_escasas": sum(d.get("escasas", 0) for d in pdf),
                    "paginas_sin_texto": sum(d.get("sin_texto", 0) for d in pdf),
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
