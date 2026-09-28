# Implementation Plan: F18 · Lectura de fichas RENIEC escaneadas

**Branch**: `feature/f18-lectura-reniec` | **Date**: 2026-09-27 |
**Sources**: [spec.md](spec.md), `specs/007-persona-ampliada`, `specs/010-unificar-fichas`.

## Summary and scope

Cuatro ajustes de lectura en `nucleo/verificar.py`, sin tocar servicios,
plantillas, modelos ni dependencias.

## Contrato

- `_fecha_reniec(valor)`: quita `.` o espacio entre dos dígitos y valida igual que F12 (FR-001).
- `_campo_reniec(raw, etiqueta)`: sin valor en la celda propia ni en la
  siguiente, toma la primera celda de la línea siguiente si no casa `_ROTULO`
  (`^[letras .]{3,40}:`); para `DIRECCION`, solo con dígito o abreviatura de
  `_VIAS` (FR-002).
- `nombre_reniec(raw)`: considera también el rótulo en la última celda; con
  valor vacío o no alfabético, prueba la primera celda de la línea siguiente
  con la misma condición de rótulo (FR-003).
- `catalogo()`: el registro de una página RENIEC que solo trae documento se
  une, con los campos de `_campos_reniec()` de esa página, al ancla del mismo
  documento mediante `unificar_personas()` (regla F12 de emisión y
  conflicto); sin ancla sigue su camino actual (FR-004).

## Constitution Check

| Principio | Comprobación |
|---|---|
| I. Determinismo | Reglas de texto fijas; el documento exacto decide la unión. |
| II. Núcleo puro | Solo funciones puras de `verificar.py`. |
| III. Tests primero | Pruebas rojas ficticias y paridad antes del código. |
| IV. Privacidad | Solo datos ficticios; nada nuevo en logs. |
| V. Simplicidad | Se reutilizan `_VIAS`, `_campos_reniec()` y `unificar_personas()`; sin abstracción nueva. |
| VI. Seguridad | Sin cambios de vistas ni permisos. |
| VII. DevSecOps | Suite con cobertura, Ruff, `check`, `makemigrations --check`, `git diff --check`. |
| VIII. Usabilidad | Más campos con procedencia en la tabla existente. |

## Verificación y entrega

1. Paridad literal (SC-004) en verde antes de tocar código.
2. Pruebas rojas, código, fixtures, suite, Ruff, `check`, `makemigrations --check`, `git diff --check`.
3. SC-001..SC-003: los mide el revisor fuera del repositorio.
4. Commits locales, sin push ni PR.

## Complexity Tracking

Ninguna violación.
