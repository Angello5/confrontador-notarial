# Implementation Plan: F4 · Expedientes

**Branch**: `feature/f4-expedientes` | **Date**: 2026-09-20 | **Spec**: [spec.md](spec.md)

**Input**: `specs/004-expedientes/spec.md` y `specs/004-expedientes/data-model.md`,
ambos aprobados y no modificables en esta etapa.

## Summary

Crear la aplicación Django `expedientes` para registrar expedientes y
documentos, conservar texto extraído con caché por hash y versión del
extractor, y procesar la cola `PENDIENTE` mediante comandos programados. Las
vistas serán delgadas; `services.py` y los comandos coordinarán validación,
extracción, persistencia y borrado temporal. No se ejecutan las capas de
confrontación de F5 ni se importa `experimental/`.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: Django 5.2.17, PostgreSQL mediante `psycopg`,
pytest/pytest-django/pytest-cov y los adaptadores de extracción ya fijados.
No se añade ninguna dependencia. AdminLTE 4, Bootstrap 5 y Alpine.js ya están
vendorizados en `static/vendor/`.

**Storage**: PostgreSQL para las tres entidades nuevas, migraciones Django y
un directorio temporal fuera de las rutas servidas. El archivo binario no se
persiste; permanecen hash, metadatos y texto extraído según la especificación.

**Testing**: pytest con PostgreSQL en el job `tests`, datos ficticios,
pruebas unitarias de servicios y pruebas Django de integración para permisos,
unicidad, concurrencia, estados, caché y limpieza temporal. La medición
`local_reference` permanece fuera de CI.

**Target Platform**: servidor on-premise en la LAN, con el mismo entorno
Python/Django del F2 y los recursos OCR locales ya aprovisionados.

**Project Type**: aplicación web Django monolítica con plantillas y comandos
de gestión programables por el sistema operativo.

**Performance Goals**: el procesamiento pesado no ocurre en la petición; no se
define una latencia de OCR nueva. El sondeo de estado usa el intervalo indicado
en `contracts/ui.md`. El umbral de recuperación de un worker queda
`[NEEDS CLARIFICATION]`.

**Constraints**: sin IA, `experimental/`, Celery, Redis, RabbitMQ, HTMX,
React, API pública, CDN o dependencias nuevas. `accounts/`, `core/`, `nucleo/`
y el comportamiento del adaptador no se reestructuran. Todos los temporales se
borran en `finally`; los mensajes y logs excluyen datos personales y contenido.

**Scale/Scope**: hasta 10 usuarios del ERP y expedientes con documentos de los
formatos ya admitidos por el adaptador. F4 cubre alta, subida, extracción,
reutilización, estados, reintento, supresión por comando y huérfanos; la
confrontación es F5 y la auditoría completa es F6.

## Constitution Check

| Principio | Comprobación del diseño | Resultado |
|---|---|---|
| I. Determinismo y sin IA | `expedientes` no importa `experimental/` ni llama modelos. La identidad del extractor se deriva de `_OCR_FILES` y `_OCR_USE_CLS` de forma ordenada; la misma entrada y versión produce la misma clave de caché. | PASS |
| II. Núcleo puro | No se modifica el comportamiento de `nucleo/` ni de `adaptadores/extraccion.py`. La aplicación usa el adaptador como borde; vistas delgadas, servicios para coordinación y comando para la cola. | PASS |
| III. Pruebas primero | Cada regla funcional y de seguridad tiene una prueba sintética que se escribe y se comprueba en rojo antes de la implementación correspondiente. PostgreSQL valida concurrencia. | PASS, sujeto al orden TDD de `tasks.md` |
| IV. Privacidad | No se versionan expedientes ni archivos. El temporal queda fuera del árbol servido y se borra en `finally`; texto, hash y supresión siguen la constitución. Los logs/mensajes son agregados y seguros. | PASS, con semántica compartida pendiente |
| V. Simplicidad | Una app nueva, ORM Django, servicios mínimos y dos comandos. No se agregan repositorios genéricos, colas externas, SPA, API ni dependencias. | PASS |
| VI. Seguridad y control de acceso | Login y grupos existentes, autorización por creador/Administrador en cada operación, validación server-side de rol/tamaño/contenido y nombres no confiables sin uso en rutas. | PASS |
| VII. DevSecOps | Se conserva el job y los gates existentes: Ruff, pytest/cobertura, SAST/Sonar, SCA y secretos. Locks y assets no cambian. | PASS |
| VIII. Usabilidad | Contrato de UI en español con estados `PENDIENTE`/`PROCESANDO`/`LISTO`/`ERROR`, mensajes de recuperación, polling Alpine, teclado, foco, etiquetas y contraste; checklist separado para revisión. | PASS, con eliminación/cierre pendientes |

**Resultado previo a investigación**: compatible. Las cinco decisiones
pendientes no autorizan inventar reglas de negocio; las tareas afectadas deben
detenerse hasta resolverlas.

## Project Structure

### Documentation (this feature)

```text
specs/004-expedientes/
├── spec.md                         # aprobado; no se modifica
├── data-model.md                   # aprobado; no se modifica
├── research.md                     # decisiones y pendientes
├── plan.md                         # este plan
├── contracts/ui.md                 # pantallas, estados y mensajes
├── tasks.md                        # orden ejecutable de implementación
└── checklists/
    ├── requirements.md             # calidad de requisitos
    └── ux.md                       # Nielsen y accesibilidad
```

No se crea `quickstart.md` en esta etapa porque no forma parte del entregable
solicitado; deberá añadirse antes de cerrar la implementación si el flujo de
Spec Kit lo requiere.

### Source Code (repository root, for the implementation phase)

```text
expedientes/
├── apps.py                         # configuración y límites de la app
├── forms.py                        # alta y subida, validación server-side
├── models.py                        # Expediente, Documento, TextoExtraido
├── services.py                      # hash, caché, estados y borrado temporal
├── urls.py                          # rutas HTML y JSON del módulo
├── views.py                         # validación, servicios y renderizado
├── migrations/                      # migraciones de las tres entidades
└── management/commands/
    ├── procesar_documentos.py       # consumidor de Documento=PENDIENTE
    ├── limpiar_temporales.py        # huérfanos con más de 24 h
    └── suprimir_texto_expediente.py # derecho de supresión

adaptadores/extraccion.py             # solo identidad pública mínima, sin cambio de conducta
config/settings.py                    # app y directorio temporal seguro
config/urls.py                        # include de expedientes
templates/expedientes/                # list/detail/form/estado en español
tests/test_expedientes_*.py           # pruebas ficticias primero
tests/test_extractor_identity.py     # caracterización de version_extractor
tests/conftest.py                     # cobertura de módulos nuevos, si procede
pyproject.toml                         # cobertura/markers solo si son necesarios
```

**Structure Decision**: mantener el monolito Django de F2 y añadir una única
app de dominio para F4. `nucleo/` sigue siendo puro; `services.py` recibe
rutas temporales controladas y llama al adaptador; no se crea una capa de
repositorio ni una abstracción con una sola implementación.

## Phase 0: Research

`research.md` resuelve decisiones de estructura, cola, caché, identidad OCR,
validación, temporales, autorización, UI y calidad. Las decisiones de negocio
que faltan se conservan literalmente como `[NEEDS CLARIFICATION]`.

## Phase 1: Design and Validation

- `data-model.md` se reutiliza sin reescritura.
- `contracts/ui.md` define rutas HTML, endpoint de estado, estados, mensajes,
  permisos y accesibilidad sin datos personales.
- `tasks.md` ordena pruebas rojas, implementación mínima y checkpoints.
- Los checklists revisan calidad de requisitos y UX; no declaran implementación
  terminada y se entregan con todos sus ítems sin marcar.

## Constitution Check después del diseño

I–VIII siguen en PASS bajo las mismas condiciones del chequeo previo. El único
cambio previsto fuera de la app es el helper mínimo de identidad del extractor;
su prueba debe demostrar que no altera OCR, lectura, caché de disco ni el
núcleo. Los puntos ambiguos se mantienen bloqueados y se reportan al
coordinador; no hay excepción constitucional solicitada.

## Complexity Tracking

| Elemento | Motivo | Alternativa más simple considerada y razón para descartarla |
|---|---|---|
| Aplicación Django `expedientes` | Aísla modelos, permisos y flujo de la funcionalidad F4 sin reestructurar `accounts/` ni `core/`. | Añadir modelos a `core/` mezcla el shell con el dominio y contradice el alcance explícito. |
| Cola en PostgreSQL con estados y bloqueos | Es la cola exigida y sobrevive reinicios; permite evitar dos consumidores del mismo documento. | Cola en memoria o worker externo pierde estado o añade dependencias prohibidas. |
| `services.py` | Centraliza hash, reutilización, transición y `finally` para que vistas y comandos compartan una sola ruta de seguridad. | Duplicar la lógica en vistas/comandos deja caminos sin limpieza y contradice el principio II. |
| Helper `version_extractor()` | Evita duplicar hashes/modelos y permite formar la clave requerida por la constitución. | Leer variables privadas desde varias capas o copiar valores es más frágil y no reutiliza la fuente existente. |

No hay violaciones de la constitución ni dependencias nuevas que justificar.
