# Implementation Plan: F19 · Errores del borrador fuera de la comparecencia

**Branch**: `feature/f19-errores-borrador` | **Date**: 2026-09-27 | **Sources**: [spec.md](spec.md)

## Summary and scope

Solo `nucleo/verificar.py`: tres bloques más dentro de `revisar()` y una
función pura `numero_en_letras()`. `services.py` y la plantilla no cambian: las
salidas usan el formato `[CAMPO] «hallado» debe decir «esperado»` / `no coincide
con ninguna fuente` que el adaptador ya interpreta.

## Contrato

```text
RE_DNI_BORRADOR  rótulo de DNI (+ NRO) y (\d{6,10}); 8 dígitos -> check() actual
numero_en_letras(palabras) -> int | None   None si alguna palabra no es numérica
revisar(...)     añade [DNI] de longitud incorrecta, [NOMBRE] por ventana, [NUMERO_EN_LETRAS]
```

## Constitution Check

| Principio | Comprobación |
|---|---|
| I. Determinismo | Regex, rapidfuzz y Levenshtein con desempate fijo. |
| II. Núcleo puro | Todo en `nucleo/verificar.py`; sin Django ni E/S. |
| III. Tests primero | Pruebas rojas ficticias con casos positivos y negativos. |
| IV. Privacidad | Solo datos ficticios. |
| V. Simplicidad | Sin dependencias; diccionario de palabras y suma. |
| VII. DevSecOps | Suite, Ruff, `check`, `makemigrations --check`, `git diff --check`. |

## Complexity Tracking

Ninguna violación.
