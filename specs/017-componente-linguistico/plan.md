# Implementation Plan: F23 · Componente lingüístico

**Branch**: `Angello5/componente-lingüístico-f23-linguistico` | **Date**: 2026-09-28 | **Sources**: [spec.md](spec.md)

## Summary and scope

- `nucleo/ortografia.py`: nueva función pura `redaccion(texto, protegidos)`.
- `expedientes/services.py::confrontar_borrador`: descomenta la ortografía,
  captura `DiccionarioNoAprovisionado` como aviso (no bloquea), amplía las
  palabras propias (domicilio, distrito, hallados de regla/personas) y añade
  `redaccion`. Clave nueva `linguistico_aviso`.
- Ronda 2 (2026-09-28): `_capa_linguistica` recibe los textos de las fuentes
  y suma sus palabras (≥ 3 letras) a las propias; `redaccion` pierde la regla
  «doble espacio».
- `templates/expedientes/confrontacion.html`: descomenta tarjeta y sección
  como «Lingüístico», con aviso.

## Contrato

```text
redaccion(texto: str, protegidos: Iterable[str]) -> list[tuple[str, str, str]]
resultado["ortografia"]         filas lingüísticas (ortografía + redacción)
resultado["linguistico_aviso"]  "" | aviso de diccionario ausente
```

## Constitution Check

| Principio | Comprobación |
|---|---|
| I. Determinismo | Regex y hunspell; orden de aparición. Capa «ortografía» permitida. |
| II. Núcleo puro | `redaccion` en `nucleo/ortografia.py`, sin E/S. |
| III. Tests primero | Pruebas rojas ficticias antes del código. |
| IV. Privacidad | Solo datos ficticios. |
| V. Simplicidad | Sin dependencias ni archivos nuevos de código. |
| VII. DevSecOps | Suite, Ruff, `check`, `makemigrations --check`, `git diff --check`. |

## Complexity Tracking

Ninguna violación.
