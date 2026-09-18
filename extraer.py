"""Compatibilidad temporal para la CLI y las apps anteriores a Etapa 4."""

__all__ = [
    "CACHE",
    "DOCS",
    "DPI",
    "IMGS",
    "LEGACY",
    "PARTES_DOCX",
    "RE_FALLBACK",
    "RE_TAB",
    "SOFFICE",
    "_cacheado",
    "_docx",
    "_legacy",
    "_ocr",
    "_pdf",
    "_ruta_legacy",
    "_soffice",
    "_xlsx",
    "leer",
    "main",
    "ocr_lineas",
    "recolectar",
]

from adaptadores.extraccion import (
    CACHE,
    DOCS,
    DPI,
    IMGS,
    LEGACY,
    PARTES_DOCX,
    RE_FALLBACK,
    RE_TAB,
    SOFFICE,
    _cacheado,
    _docx,
    _legacy,
    _ocr,
    _pdf,
    _ruta_legacy,
    _soffice,
    _xlsx,
    leer,
    main,
    ocr_lineas,
    recolectar,
)

if __name__ == "__main__":
    raise SystemExit(main())
