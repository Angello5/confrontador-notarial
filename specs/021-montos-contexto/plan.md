# Implementation Plan: F27 · Montos por posición, con moneda y concepto

**Branch**: `Angello5/f27-montos-contexto` | **Date**: 2026-09-28 | **Sources**: [spec.md](spec.md)

## Summary and scope

`nucleo/verificar.py`: `RE_MONTO` con moneda, una función `_monto()` que da el
valor comparable, `_montos_por_posicion()` y el parámetro `minutas` de
`revisar()`. `expedientes/services.py`: pasa la minuta por archivo y separa
`concepto` y `fuente` del sufijo. Sin migraciones, dependencias ni plantillas.

Ronda 2: `adaptadores/extraccion.py` (`_docx` por filas de tabla y
`_FORMATO_TEXTO` en `version_extractor()`) y el comando
`expedientes/management/commands/reextraer_expediente.py`. Sin migraciones.

## Contrato

```text
revisar(cat, destino, umbral, exigibles=None, montos_exigibles=None, minutas=None)
minutas: {archivo: texto} | None
```

## Constitution Check

| Principio | Comprobación |
|---|---|
| I. Determinismo | Regex, `rapidfuzz` ya instalado, empates por orden. |
| II. Núcleo puro | Recibe textos; el rol minuta lo resuelve `services.py`. |
| III. Tests primero | Pruebas rojas ficticias antes del código. |
| IV. Privacidad | Solo datos ficticios. |
| V. Simplicidad | Un parámetro opcional y dos funciones privadas. |

## Complexity Tracking

Ninguna violación.
