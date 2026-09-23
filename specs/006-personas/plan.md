# Implementation Plan: F11 · Extracción por personas

**Branch**: `feature/f11-personas` | **Date**: 2026-09-22 | **Spec**:
[spec.md](spec.md)

**Input**: `specs/006-personas/spec.md`, `research.md`,
`docs/catalogo-fuentes.md` y el contrato actual de F5.

## Summary

Cambiar el resultado de `nucleo.verificar.catalogo()` a un `Catalogo` puro que
conserve personas ligadas a su documento y sus procedencias, manteniendo una
proyección compatible con `NOMBRE`, `DNI`, `PARTIDA` y `MONTO`. Añadir una
entrada por página en el adaptador, sin romper `leer()`, y consumir las páginas
para clasificar, descartar con reglas estructurales y comparar identidades por
bloque. La confrontación de partidas, montos y párrafos permanece en sus
funciones y algoritmos actuales.

Las cinco aclaraciones del propietario están resueltas en `spec.md`. Esta
entrega implementa el separador de páginas, la clasificación conservadora y el
contrato puro de personas; documento cruzado y unificación quedan para otra
ronda.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: biblioteca estándar, `rapidfuzz` ya instalada para
las reglas históricas, PyMuPDF/RapidOCR ya instalados en los adaptadores. No se
añade ninguna dependencia.

**Storage**: F4 conserva `TextoExtraido.texto` como cadena. Las páginas se
separan con `\f` dentro de esa cadena; no se añade campo ni migración. Las filas
históricas sin separador se procesan como un único bloque. No se guardan
archivos originales, bloques completos ni texto de páginas descartadas.

**Testing**: pytest con datos ficticios. Las pruebas rojas cubren el contrato
de `Catalogo`, clasificación, límites de asociación, errata `D.N.1,`,
unificación conservadora, compatibilidad de `leer()`, migración/cache y paridad
de partidas, montos y párrafos. La medición `local_reference` sigue fuera de
CI y solo se ejecuta con selección explícita.

**Target Platform**: ERP Django on-premise en LAN, con extracción local y sin
servicios externos durante la petición.

**Project Type**: monolito Django con núcleo puro y adaptadores locales.

**Performance Goals**: una sola pasada determinista por página; no se
introduce paralelismo, índice ni caché nueva en el núcleo. El OCR conserva su
caché actual.

**Constraints**: no importar `experimental/`, no modelos de lenguaje, no datos
reales, no dependencias nuevas, no decidir reglas de negocio no aclaradas y no
alterar el resultado de partidas, montos o párrafos.

## Constitution Check

*GATE: compatible; las cinco decisiones del propietario están incorporadas en
`spec.md`.*

| Principio | Comprobación del diseño | Resultado |
|---|---|---|
| I. Determinismo y sin IA | Clasificación, asociación y tolerancia de etiquetas son reglas puras; la similitud aproximada nunca aprueba ni unifica. | PASS |
| II. Núcleo de dominio puro | `Catalogo`, `Persona`, clasificación y comparación reciben texto/estructuras; la página y procedencia son datos, no acceso a Django/OCR/FS. | PASS |
| III. Pruebas primero | Cada regla nueva tiene una prueba roja ficticia antes de implementarse; se añade prueba de paridad de la salida histórica. | PASS sujeto a tasks.md |
| IV. Privacidad | No se versionan expedientes; se conserva la cadena plana con su separador y solo metadatos de procedencia; no se escriben datos en logs. | PASS |
| V. Simplicidad | Una página es un bloque; `leer()` se conserva como wrapper; no se crea un segmentador visual ni una dependencia. | PASS |
| VI. Seguridad y acceso | Las personas y procedencias solo se muestran después de la autorización existente de F5; el núcleo no decide permisos. | PASS |
| VII. DevSecOps | Se mantienen Ruff, pytest/cobertura, pip-audit, gitleaks y Quality Gate; F11 no añade migraciones. | PASS |
| VIII. Usabilidad | El contrato muestra procedencia, recuentos de páginas descartadas y estados seguros para revisión manual y documento sin titular. | PASS |

**Resultado**: se puede implementar la primera parte. Documento cruzado,
unificación y consumo de UI quedan fuera de esta ronda.

## Contract and compatibility design

```text
Pagina(fuente, numero, texto)
Procedencia(fuente, pagina)
Persona(nombre | None, documento | None, procedencias, estado)
Catalogo(personas, partidas, montos, paginas_descartadas, paginas_no_clasificadas)
```

`Catalogo` ofrece la vista por campos de solo lectura. `catalogo()` acepta la
entrada histórica de fuentes y la nueva secuencia de páginas durante la
transición; con un diccionario legado cada valor se trata como una página
lógica. `revisar()`, `correspondencia()` y `diagnostico()` leen la vista por
campos, de modo que sus cadenas, umbrales y diagnósticos existentes no cambian.

La nueva comparación persona-documento devuelve observaciones estructuradas,
no altera las cadenas de `revisar()`. El servicio F5 las combina con los grupos
`Regla` y `Ortografía`; nunca usa fuzzy matching para aprobar una identidad.

Para FR-013, `PARTIDA` y `MONTO` se extraen con las expresiones actuales sobre
todo el texto de las páginas, incluso cuando una página se descarta para
identidades. `revisar_parrafos()` sigue recibiendo la cadena plana de la
minuta. La prueba de paridad debe comparar exactamente las observaciones
históricas sobre fixtures ficticios.

## Project Structure

### Documentation (this feature)

```text
specs/006-personas/
├── spec.md                 # aprobado; no se modifica
├── research.md             # decisiones, contradicciones y deuda
├── plan.md                 # este plan
├── contracts/ui.md         # contrato de extracción, resultados y estados
├── tasks.md                # orden TDD ejecutable
└── checklists/
    ├── requirements.md     # trazabilidad y límites
    └── ux.md               # Nielsen, accesibilidad y privacidad visible
```

### Source Code (future implementation)

```text
nucleo/verificar.py                 # Catalogo, clasificación y comparación pura
adaptadores/extraccion.py           # leer_paginas y wrapper leer
expedientes/services.py             # consumo posterior de páginas
tests/test_personas.py              # núcleo y reglas ficticias
tests/test_extraccion_paginas.py    # adapter y compatibilidad leer/cache
tests/test_expedientes_personas.py  # servicio, estados, permisos y UI
```

No se modifica `spec.md`, no se importan módulos de `experimental/` y no se
crea una entidad Django `Persona`: la persona es una estructura de resultado
del núcleo en F11.

## Implementation phases

### Phase 0 — decisiones cerradas

Las cinco aclaraciones están resueltas y escritas en `spec.md`; no se añade
migración. Las respuestas no cambian FR-001–FR-015.

### Phase 1 — pruebas rojas y contrato puro

Crear fixtures ficticios para una página por documento, dos personas en una
declaración, operador/notario, separador, SISGEN, jurídica, errata de etiqueta,
nombres invertidos, nombres parecidos y documentos cruzados. Probar primero el
contrato de `Catalogo`, su proyección compatible y la comprobación ligada.

### Phase 2 — extracción por páginas y cache

Extraer páginas sin duplicar OCR, unirlas con `\f` y mantener `leer()` para los
consumidores anteriores. No convertir filas antiguas sin separador en una
frontera inventada; se procesan como un bloque.

### Phase 3 — clasificación y asociación

Implementar la precedencia de tipos, exclusión de metadatos y bloques de
coincidencias, captura de etiquetas cerradas, asociación dentro de página y
unificación exacta. Toda página dudosa se conserva como no clasificada o
revisión manual; nunca se elimina por una heurística amplia.

### Phase 4 — consumo F5 y UI

Pasar la salida nueva al servicio de confrontación, conservar las llamadas de
regla existentes y añadir observaciones de documento cruzado/sin titular.
Mostrar personas una vez con todas sus procedencias, recuentos de descartes y
estados de re-subida o revisión manual, sin texto completo ni datos en logs.

### Phase 5 — gates

Ejecutar tests, Django checks, migración aplicada/revertida si existe, Ruff,
`pip-audit --strict`, `gitleaks`, `git diff --check` y revisión de privacidad.
La medición privada y Quality Gate remoto se reportan como evidencia separada.

## Risks and rollback

- Si cambia la salida de partidas, montos o párrafos, revertir el consumo de la
  proyección nueva y conservar el adaptador legado; no ajustar tests para
  aceptar la regresión.
- Si una regla de descarte clasifica una página válida, quitarla y degradar a
  `revision_manual`; no ampliar la regla sin fixture que demuestre su límite.
- Si el texto histórico no tiene separador, mantener F5 con texto plano y
  tratarlo como un solo bloque; la revisión de procedencia queda degradada.
- Si una persona se unifica de más, conservar candidatos separados y registrar
  observación manual; nunca corregir escogiendo el nombre más parecido.

## Complexity Tracking

| Elemento | Motivo | Alternativa simple descartada |
|---|---|---|
| `Catalogo` con proyección Mapping | Permite introducir asociaciones sin romper `cat["DNI"]` ni las funciones medidas. | Cambiar todos los consumidores en una sola edición rompe compatibilidad y aumenta el diff. |
| Clasificador de página | SISGEN y separadores deben descartarse antes de extraer personas. | Una regex global sobre el legajo mezcla operador, terceros y comparecientes. |
| Comparación persona-documento separada | El contrato `list[str]` histórico no puede expresar una relación segura. | Cambiar el formato de todas las observaciones altera F5 y su medición. |

No se añade segmentador visual, fuzzy matching de identidades, servicio
externo, modelo de lenguaje, entidad ORM ni dependencia nueva.
