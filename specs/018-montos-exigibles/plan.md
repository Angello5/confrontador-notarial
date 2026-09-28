# Implementation Plan: F24 · Montos exigibles

**Branch**: `Angello5/montos-exigibles-P-05-f24-montos-exigibles` | **Date**: 2026-09-28 | **Sources**: [spec.md](spec.md)

## Summary and scope

`nucleo/verificar.py` (`revisar()` y una función nueva de una línea) y
`confrontar_borrador()` de `expedientes/services.py`. Sin migraciones,
dependencias ni cambios de plantilla.

## Contrato

```text
revisar(cat, destino, umbral, exigibles=None, montos_exigibles=None)
montos_exigibles(minutas) -> frozenset[str]
```

- `montos_exigibles=None`: comportamiento actual. Con conjunto: el `FALTA` de
  `MONTO` se limita a `cat["MONTO"] & montos_exigibles`; el reconocimiento usa
  `cat["MONTO"]` completo.

## Constitution Check

| Principio | Comprobación |
|---|---|
| I. Determinismo | Regex y conjuntos. |
| II. Núcleo puro | El núcleo recibe textos; el rol minuta lo resuelve `services.py`. |
| III. Tests primero | Pruebas rojas ficticias antes del código. |
| IV. Privacidad | Solo datos ficticios. |
| V. Simplicidad | Un parámetro opcional y una función de una línea, como F16. |
| VII. DevSecOps | Suite, Ruff, `check`, `makemigrations --check`, `git diff --check`. |

## Complexity Tracking

Ninguna violación.
