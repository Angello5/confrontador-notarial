# Implementation Plan: F15 · Una persona por DNI entre fichas oficiales

**Branch**: `feature/f15-unificar-fichas` | **Date**: 2026-09-27 |
**Sources**: [spec.md](spec.md), `specs/008-anclaje-fichas/plan.md`.

## Summary and scope

Dos anclas (fichas RENIEC o biométricas) con el mismo documento exacto se
unifican siempre en una persona. Solo cambia `nucleo/verificar.py` y sus
pruebas. Sin migraciones, dependencias, red ni cambio del sondeo JSON; la
plantilla ya muestra adjuntos.

## Technical context

Python 3.13, núcleo puro. Se reutilizan `Persona.adjuntos` (F13),
`_nombre_clave()`, la regla de emisión de F12 y
`rapidfuzz.distance.Levenshtein`, ya instalado. Sin clase ni campo nuevo.

## Constitution Check

| Principio | Comprobación |
|---|---|
| I. Determinismo | Documento exacto decide la identidad; la distancia solo decide el estado. Orden de páginas estable. |
| II. Núcleo puro | Cambio en funciones puras de `verificar.py`; `services.py` y plantilla sin cambios. |
| III. Tests primero | Paridad y pruebas rojas ficticias antes del código. |
| IV. Privacidad | Solo datos ficticios; nada nuevo en logs ni sondeo. |
| V. Simplicidad | Un parámetro opcional en `unificar_personas()`; sin abstracción nueva. |
| VI. Seguridad | Sin cambios de vistas ni permisos. |
| VII. DevSecOps | Suite, Ruff, `check`, `makemigrations --check`, `git diff --check`. |
| VIII. Usabilidad | La variante se ve como dato adjunto con su procedencia (tabla F13). |

## Contrato

```text
unificar_personas(personas, tipos=None)
```

- Sin `tipos`: comportamiento actual (menciones, pruebas F11/F12).
- Con `tipos` (paralelo a `personas`, solo desde `catalogo()` para anclas):
  mismo documento exacto basta para fusionar (FR-001).
  - Nombre ganador: RENIEC antes que biométrica; entre iguales, la
    `fecha_emision` más reciente; fecha antes que sin fecha; empate → primera
    por orden de página (FR-002).
  - El registro perdedor con nombre distinto pasa a `adjuntos` con su nombre,
    documento y procedencias (FR-003).
  - Estado: `REVISION_MANUAL` si Levenshtein sobre `_nombre_clave()` sin
    espacios > 2, o si una clave está contenida en la otra y es más corta
    (FR-004); los conflictos F12 siguen igual (FR-005).
  - Procedencias: todas (FR-006).
- `_pegar()` conserva los adjuntos que ya trae el ancla y compara el nombre
  de un registro sin documento también con los adjuntos del ancla, para que
  la variante de la ficha siga atrayendo lo que antes pegaba al ancla
  duplicada.

## Verificación y entrega

1. Paridad literal (SC-004): ya cubierta por
   `test_paridad_capa_de_campos_con_legajo_ficticio`; se comprueba en verde
   antes de tocar código.
2. Pruebas rojas ficticias (tasks.md), luego código.
3. Fixtures, suite con cobertura, Ruff, `check`, `makemigrations --check`,
   `git diff --check`.
4. Medición SC-001..SC-003 sobre los 10 expedientes: la hace el revisor.
5. Commits locales, sin push ni PR.

## Complexity Tracking

Ninguna violación.
