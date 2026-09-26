# Implementation Plan: F13 · Anclaje por ficha oficial

**Branch**: `feature/f13-anclaje-fichas` | **Date**: 2026-09-25 |
**Sources**: [spec.md](spec.md), [research.md](research.md),
`docs/catalogo-datos.md`, `docs/catalogo-fuentes.md`.

## Summary and scope

Solo las fichas RENIEC y biométricas crean personas (anclas). Todo lo demás se
pega a un ancla o queda como mención sin ficha. La capa de campos no cambia.
Sin migraciones, dependencias, red ni cambio del sondeo JSON. Tocan código:
`nucleo/verificar.py`, `expedientes/services.py`,
`templates/expedientes/confrontacion.html` y sus pruebas.

## Technical context

Python 3.13, núcleo puro. Se reutilizan `Persona`, `Procedencia`, `Catalogo`,
`_nombre_clave()`, `_linea_etiquetada()` y `unificar_personas()`. No hay
abstracción nueva: un conjunto de tipos ancla y una función de pegado.

## Constitution Check

| Principio | Comprobación |
|---|---|
| I. Determinismo | Igualdad exacta de documento y `_nombre_clave()`; ninguna aproximación. Anclas unificadas antes de pegar, orden de páginas estable. |
| II. Núcleo puro | Cambios en funciones puras de `verificar.py`; `services.py` solo presenta. La medición de referencia se repite antes de integrar. |
| III. Tests primero | Paridad de la capa de campos y pruebas rojas ficticias antes del código. |
| IV. Privacidad | Adjuntos, menciones y cónyuge solo en HTML autorizado; ni sondeo ni logs. Solo datos ficticios. |
| V. Simplicidad | Tres campos opcionales en `Persona`, una ranura en `Catalogo`; sin clase nueva. |
| VI. Seguridad | Misma vista, permisos, POST y CSRF. |
| VII. DevSecOps | Suite, Ruff, `makemigrations --check`, `git diff --check`; Quality Gate remoto pendiente sin push. |
| VIII. Usabilidad | Anclas y menciones en tablas separadas con texto de ayuda; procedencia junto a cada valor. |

## Contrato

```text
Persona(nombre, documento, procedencias, estado="CONFIRMADA",
        ...10 campos F12 sin cambio...,
        adjuntos=None, conyuge=None, procedencia_conyuge=None)

Catalogo(personas, partidas=..., montos=..., paginas_descartadas=...,
         paginas_no_clasificadas=..., menciones=())
```

- `Catalogo.personas`: solo anclas. `estado` ∈ {`CONFIRMADA`,
  `REVISION_MANUAL`}; la segunda solo por conflicto entre anclas.
- `Persona.adjuntos`: tupla de registros no oficiales pegados, cada uno con su
  nombre, documento y procedencias de origen. `None` si no hay.
- `Catalogo.menciones`: registros sin ancla, deduplicados, estado `SIN_FICHA`.
- Los valores por defecto `None` mantienen iguales a las personas F11/F12 ya
  construidas en pruebas.

## Flujo en `catalogo()`

```text
por página (sin cambio hasta _personas_de_pagina):
    registros = _personas_de_pagina(pagina, tipo)
    tipo ∈ {RENIEC, BIOMETRICA} y nombre y documento → candidatos a ancla
    resto                                            → candidatos a pegar
anclas    = unificar_personas(candidatos a ancla)          # F11/F12 intacto
por cada candidato a pegar, en orden de página:
    documento → ancla única con ese documento     → adjunto
    solo nombre → ancla única con esa clave exacta → adjunto
    si no → mención
    al pegar: ancla.conyuge ← registro.conyuge si el ancla no tiene
menciones = unificar_personas(menciones) con estado SIN_FICHA
```

`Catalogo.__getitem__("NOMBRE"|"DNI")` recorre anclas, sus adjuntos y
menciones (nombre, cónyuge y documento). `PARTIDA` y `MONTO` no cambian.

## Cambios puntuales

- `_personas_de_pagina()`: en `DECLARACION_JURADA`, lee el cónyuge con
  `_linea_etiquetada()`, lo quita de los nombres del bloque y de cada línea, y
  lo guarda en el registro del declarante (o en una mención propia si no hay
  declarante, pendiente de aclaración).
- `unificar_personas()`: no fusiona dos registros con cónyuges distintos, y al
  fusionar conserva `conyuge` del primero o del segundo. Sin más cambios.
- `comparar_personas()`: borrador = anclas + adjuntos + menciones de su
  catálogo; titular de `DOCUMENTO_CRUZADO` solo entre anclas; pertenencia de
  documento contra `fuente["DNI"]` (research D8).
- `revisar_persona_ampliada()`, `revisar()`, `correspondencia()`,
  `diagnostico()`, `revisar_parrafos()`: sin cambio de código.
- `services.py`: `_personas_legibles(personas)` sobre una secuencia; añade
  `conyuge`, `procedencia_conyuge` y `adjuntos` legibles.
  `_resumen_extraccion()` añade `menciones` global y por documento.
  `_ESTADOS_PERSONA["SIN_FICHA"] = "Sin ficha"`.
- Plantilla según [contracts/ui.md](contracts/ui.md).

## Verificación y entrega

1. Fijar antes de tocar código la salida literal de `revisar()`,
   `correspondencia()`, `diagnostico()` y `revisar_parrafos()` sobre los
   fixtures ficticios existentes (SC-005).
2. Pruebas rojas ficticias por regla (tasks.md), luego código.
3. Fixtures, suite con cobertura, Ruff, Django `check`,
   `makemigrations --check`, `git diff --check`, revisión de privacidad.
4. Medición antes/después sobre los 10 expedientes reales y el expediente de
   referencia, fuera del repositorio y a cargo del revisor (tasks T024).
5. Commit local sin push ni PR.

## Complexity Tracking

Ninguna violación. Los tres campos nuevos son datos del dominio (catálogo de
datos: `conyuge` y `procedencias`); `menciones` separa lo que FR-007 pide
mostrar aparte sin crear entidad persistente.
