# Implementation Plan: F22 · RUC y direcciones

**Branch**: `Angello5/RUC-y-direcciones-f22-ruc-direcciones` | **Date**: 2026-09-28 | **Sources**: [spec.md](spec.md)

## Summary and scope

Solo `nucleo/verificar.py`: dos proyecciones más en `Catalogo` (`RUC`,
`DIRECCION`), su lectura en `catalogo()`, dos bloques en `revisar()`, los RUC
de la minuta en `nombres_exigibles()` y la supresión del duplicado en
`revisar_persona_ampliada()`. `services.py` y la plantilla no cambian.

## Contrato

```text
RE_RUC_DOC / RE_RUC_BORRADOR   rótulo de RUC + (\d{11}) / (\d{9,13})
_direcciones(texto, rotulo)    tramos tras el rótulo hasta fin de cláusula
_direcciones_observadas(fuente, borrador) -> [(hallado, esperado)]
revisar(...)                   añade [RUC] por aparición, [RUC] FALTA y [DIRECCION]
```

## Constitution Check

| Principio | Comprobación |
|---|---|
| I. Determinismo | Regex, rapidfuzz y Levenshtein con desempate fijo. |
| II. Núcleo puro | Todo en `nucleo/verificar.py`; sin Django ni E/S. |
| III. Tests primero | Pruebas rojas ficticias con casos positivos y negativos. |
| IV. Privacidad | Solo datos ficticios. |
| V. Simplicidad | Sin dependencias; reutiliza `_direccion_tokens` y `_VIAS`. |
| VII. DevSecOps | Suite, Ruff, `check`, `makemigrations --check`, `git diff --check`. |

## Complexity Tracking

Ninguna violación.
