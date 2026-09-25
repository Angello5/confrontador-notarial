# Implementation Plan: F12 · Persona ampliada

**Branch**: `feature/f12-persona-ampliada` | **Date**: 2026-09-25 |
**Sources**: [spec.md](spec.md), [research.md](research.md),
`docs/catalogo-datos.md`, `docs/catalogo-fuentes.md`.

## Summary and scope

F12 amplía `Persona` en memoria, extrae los cuatro campos solo de RENIEC,
resuelve discrepancias por fecha de emisión y añade US1–US3 a la confrontación.
No hay migración, dependencia nueva, red ni cambio del sondeo JSON.

## Technical context

Python 3.13, Django existente, núcleo puro. `date` representa nacimiento,
`norm()` normaliza rótulos y enum civil, y la frontera de dos espacios de OCR
separa columnas. Se conserva el texto de dirección y distrito. La fecha solo
acepta `dd/mm/aaaa` y `dd-mm-aaaa` con dígitos ASCII y calendario válido.

## Constitution Check

| Principio | Comprobación |
|---|---|
| I. Determinismo | Parser cerrado; sin reloj en el núcleo. La fecha de hoy entra desde el servicio cuando se haga US2. |
| II. Núcleo puro | Captura y unificación solo usan texto y estructuras; Django solo presenta. |
| III. Tests primero | Regresiones rojas ficticias antes de modificar núcleo y UI. |
| IV. Privacidad | Valores solo en HTML autorizado; el sondeo, errores y logs no los reciben. |
| V. Simplicidad | Mismo `Persona`, `Catalogo`, `Procedencia` y tabla; sin abstracción de campos ni dependencia. |
| VI. Seguridad | Se mantienen control de acceso, POST y CSRF de la vista actual. |
| VII. DevSecOps | Suite, Ruff, comprobación de migraciones y revisión del diff local; Quality Gate remoto pendiente sin push. |
| VIII. Usabilidad | Valor y archivo/página juntos, ausencia explícita y encabezados accesibles. |

## Contrato y flujo

```text
Persona(nombre, documento, procedencias, estado="CONFIRMADA",
        estado_civil=None, fecha_nacimiento=None, domicilio=None, distrito=None,
        procedencia_estado_civil=None, procedencia_fecha_nacimiento=None,
        procedencia_domicilio=None, procedencia_distrito=None,
        fecha_emision=None, emisiones_campos=None)
```

Las cuatro posiciones iniciales no cambian. Las procedencias nuevas reutilizan
`Procedencia(fuente, pagina)`; el tipo de página queda garantizado por capturar
solo tras `clasificar_pagina() == "RENIEC"`. `_personas_de_pagina()` anota valores
solo si encuentra una persona con nombre y documento inequívocos en esa página.
El lector exige etiqueta completa al comienzo de línea y toma únicamente su
columna: `ESTADO CIVIL`, `FECHA DE NACIMIENTO`, `DIRECCIÓN`, `DISTRITO DE
DOMICILIO`. No busca en biométrica, nacimiento, pie, operador o prosa.

`unificar_personas()` conserva cada par valor/procedencia durante ambas
reconstrucciones. Si dos valores difieren, elige el de fecha de emisión más
reciente cuando es legible y marca `REVISION_MANUAL`; sin fecha fiable,
conserva el primero y también exige revisión. Las fechas de emisión se guardan
por campo para que la selección no dependa del orden de lectura.

`_personas_legibles()` convierte la fecha a ISO y deja solo el nombre del
archivo. La tabla de `templates/expedientes/confrontacion.html` muestra los
cuatro valores con su archivo y página, o ausencia. `expediente_estado()` no
cambia. `comparar_personas()`, `revisar()` y `revisar_parrafos()` mantienen
contenido y orden de sus observaciones para las mismas entradas ficticias.

## Reglas de confrontación

- US1 compara estado civil con la **cláusula de la persona en el borrador**;
  una mención de cónyuge en otra cláusula no cuenta.
- US2 calcula edad cumplida **a la fecha de hoy** y muestra esa fecha. El
  servicio pasa la fecha explícita al núcleo puro.
- US3 compara domicilio con la lista cerrada del spec, sin puntos, tildes ni
  orden del número. No usa emparejamiento difuso.
- Dos consultas RENIEC discordantes se comparan por fecha de emisión y se marca
  conflicto para revisión manual.

## Verificación y entrega

Pruebas directas de RENIEC ficticia a dos columnas, pie biométrico, enum civil,
fecha dudosa, unificación, paridad literal de observaciones previas y HTML/sondeo
se ejecutan antes de la suite completa. Después: fixtures, pytest con
cobertura, Ruff check y format, `makemigrations --check`, `git diff --check` y
revisión de privacidad. Commit local sin push ni PR. Quality Gate remoto y
`local_reference` privado permanecen pendientes.

## Complexity Tracking

No se añade abstracción ni paquete. Los ocho campos visibles y dos metadatos
de emisión pertenecen al contrato de `Persona`; un lector estricto de rótulos
evita heurísticas de OCR.
