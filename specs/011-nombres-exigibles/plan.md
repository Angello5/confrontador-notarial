# Implementation Plan: F16 · Nombres exigibles y domicilio por DNI

**Branch**: `feature/f16-nombres-exigibles` | **Date**: 2026-09-27 | **Sources**: [spec.md](spec.md)

## Summary and scope

Cambios en `nucleo/verificar.py` (`revisar()` y la búsqueda de domicilio de
`revisar_persona_ampliada()`) y en `confrontar_borrador()` de
`expedientes/services.py`. Sin migraciones, dependencias ni cambios de plantilla.

## Contrato

```text
revisar(cat, destino, umbral, exigibles=None)
nombres_exigibles(cat, minutas) -> frozenset[str]
```

- `exigibles=None`: comportamiento actual. Con conjunto: el `FALTA` de `NOMBRE`
  se limita a `cat["NOMBRE"] & exigibles`; el reconocimiento usa `cat["NOMBRE"]`
  completo.
- `nombres_exigibles`: nombres de las anclas más la proyección `NOMBRE` de cada
  texto recibido. El llamador decide qué textos son minuta.
- Domicilio: líneas que contienen el nombre clave o el DNI exacto
  (`(?<!\d)DNI(?!\d)`).

## Constitution Check

| Principio | Comprobación |
|---|---|
| I. Determinismo | Conjuntos y regex; misma entrada, misma salida. |
| II. Núcleo puro | El núcleo recibe textos; el rol minuta lo resuelve `services.py`. |
| III. Tests primero | Pruebas rojas ficticias antes del código. |
| IV. Privacidad | Solo datos ficticios. |
| V. Simplicidad | Un parámetro opcional y una función de una línea. |
| VII. DevSecOps | Suite, Ruff, `check`, `makemigrations --check`, `git diff --check`. |

## Complexity Tracking

Ninguna violación.
