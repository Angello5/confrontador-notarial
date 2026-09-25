# Implementation Plan: F12 · Persona ampliada

**Branch**: `feature/f12-persona-ampliada` | **Date**: 2026-09-25 | **Spec**:
[spec.md](spec.md)

**Input**: `spec.md` aprobado, [research.md](research.md),
`docs/catalogo-datos.md`, `docs/catalogo-fuentes.md` y F11.

## Summary

Extender la estructura `Persona` en memoria con cuatro valores opcionales y
su procedencia por campo. Extraerlos solo de formularios reconocidos y
asociados a la persona de la página. Incorporar las tres reglas a
`comparar_personas()` como observaciones estructuradas de regla, manteniendo
la salida histórica de `revisar()` y la salida previa de identidad. Mostrar
campos y observaciones en la vista de confrontación existente, sin migración,
persistencia ni cambio del sondeo JSON.

La implementación de edad, equivalencias de domicilio y alcance civil queda
condicionada a las preguntas de [research.md](research.md). Los rótulos no
documentados deben añadirse al catálogo con decisión del propietario antes
de codificar su captura; el plan no los presupone.

## Technical Context

**Language/Version**: Python 3.13.

**Dependencies**: biblioteca estándar y dependencias ya instaladas; no se
añaden paquetes. `date` representa nacimiento y referencia; `norm()` y
`_linea_etiquetada()` se reutilizan.

**Storage**: `Persona` y `Catalogo` viven durante la confrontación. Texto F4
continúa en `TextoExtraido` conforme a la constitución 1.6.0; no hay esquema,
entidad ORM, migración ni nueva copia persistida de estos campos.

**Testing**: pruebas rojas con datos ficticios para extracción, normalización,
procedencias, prioridad de fuente, reglas, paridad exacta de observaciones
anteriores, UI/autorización y ausencia en sondeo/logs. La medición privada
`local_reference` es solo del propietario y no se ejecuta en CI.

**Project Type**: monolito Django con núcleo puro y adaptadores existentes.

**Constraints**: determinismo, una persona por página oficial reconocida,
sin extrapolación de etiquetas no catalogadas, sin fuzzy matching de identidad,
sin modelos/red, y cambio mínimo.

## Constitution Check

| Principio | Comprobación del diseño | Estado |
|---|---|---|
| I. Determinismo | Normalización cerrada y fecha de referencia inyectada; no reloj dentro del núcleo ni IA. | PASS sujeto a aclaración de edad |
| II. Núcleo puro | `Persona`, lectura y reglas solo reciben texto/estructuras; Django adapta presentación. | PASS |
| III. Tests primero | Cada rama nueva se abre con prueba roja ficticia y paridad de F11/F5. | Pendiente de implementación |
| IV. Privacidad | Valores en UI autorizada; sin datos en logs, error o sondeo; texto F4 sigue su política. | PASS de diseño |
| V. Simplicidad | Se reutilizan `_linea_etiquetada()`, `comparar_personas()` y la tabla; no se crea una tercera ruta. | PASS |
| VI. Seguridad | Se conserva POST, CSRF, permisos por rol y expediente visible. | PASS de diseño |
| VII. DevSecOps | Gates locales y remotos existentes; sin dependencia ni migración. | Pendiente de ejecución |
| VIII. Usabilidad | Procedencia por campo, observaciones claras, estado de conflicto y tabla accesible. | PASS de diseño |

**Gate de diseño**: no se implementan las reglas indeterminadas ni las
etiquetas ausentes hasta que el propietario cierre lo indicado en research;
no se sustituye esa decisión con heurísticas del agente.

## Contract and compatibility design

```text
Persona(nombre, documento, procedencias, estado="CONFIRMADA",
        estado_civil=None, fecha_nacimiento=None, domicilio=None, distrito=None,
        procedencia_estado_civil=None, procedencia_fecha_nacimiento=None,
        procedencia_domicilio=None, procedencia_distrito=None)
```

Los cuatro primeros campos y sus posiciones se conservan. El constructor
admite todas las llamadas posicionales existentes. Cada procedencia de campo
incluye fuente, página y tipo de formulario para decidir la prioridad sin
depender del orden de archivos. `Procedencia` histórica de F11 no cambia.
`unificar_personas()` conserva cada par valor/procedencia y usa RENIEC para
estado civil en conflicto con BIOMETRICA; la persona queda marcada para
revisión manual mediante `estado="REVISION_MANUAL_ESTADO_CIVIL"`, sin perder su
documento/nombre. Se prueba que ambos caminos que reconstruyen `Persona` no
pierden campos ni el estado de conflicto.

`comparar_personas()` conserva la firma de dos argumentos y el mismo prefijo
de observaciones de documento cruzado/sin titular. Parámetros con nombre
aportarán el contexto adicional que el propietario apruebe (texto de minuta
si corresponde y fecha explícita). Las observaciones nuevas son diccionarios
con `tipo`, persona, valor en fuente, valor hallado o ausencia, procedencia
del campo y un valor para ubicar en borrador; no contienen HTML ni ruta del
servidor. Solo se producen para una asociación inequívoca. Edad se calcula
por cumpleaños transcurrido, sin aproximar días/365, una vez definida la fecha
de referencia. Falta de lectura o ambigüedad da ausencia de observación, no
un valor inventado.

La proyección `Catalogo["NOMBRE"|"DNI"|"PARTIDA"|"MONTO"]`, `revisar()`,
`revisar_parrafos()`, `diagnostico()` y las observaciones F11 ya emitidas
mantienen valores y orden con las mismas entradas ficticias. En
`confrontar_borrador()`, las nuevas observaciones pasan por un adaptador
estructurado pequeño de aplicación y se añaden a `resultado["regla"]` tras
`adaptar_observaciones_regla()`; no se cambia el parser de cadenas históricas.
Las observaciones nuevas incluyen procedencia visible solo en HTML autorizado.

## Project Structure

### Documentación de F12

```text
specs/007-persona-ampliada/
├── spec.md                 # aprobado; intacto
├── research.md
├── plan.md
├── contracts/ui.md
├── tasks.md
└── checklists/
    ├── requirements.md
    └── ux.md
```

### Archivos previstos para implementación posterior

```text
nucleo/verificar.py                  # Persona, extracción, unificación y regla
expedientes/services.py              # adaptación segura y resumen de extracción
templates/expedientes/confrontacion.html  # tabla y observaciones
tests/test_personas.py               # contrato puro, normalización, reglas, paridad
tests/test_expedientes_confrontacion.py     # servicio y privacidad
tests/test_expedientes_confrontacion_ui.py  # autorización y presentación
```

No se prevén cambios en `views.py`, modelos, migraciones, adaptador OCR,
dependencias ni endpoint de sondeo. Si las pruebas demuestran que el contrato
vigente necesita uno, se documenta antes de ampliar el alcance.

## Implementation phases

1. **Cierre documental**: el propietario aclara fecha, abreviaturas, alcance
   minuta/borrador y rótulos ausentes; se corrige el catálogo/spec por el
   cauce correspondiente. Esta planificación deja las preguntas abiertas.
2. **Pruebas rojas del núcleo**: compatibilidad posicional, captura etiquetada,
   rechazo OCR dudoso, procedencias, conflicto RENIEC/biométrica, reglas y
   paridad exacta F11/F5.
3. **Núcleo mínimo**: ampliar la tupla, conservar pares campo/procedencia en
   extracción y unificación; ampliar `comparar_personas()` sin tocar `revisar()`.
4. **Aplicación y UI**: adaptar observaciones estructuradas a Regla; ampliar
   `_personas_legibles()`/`_resumen_extraccion()` y tabla de extracción con
   procedencia por campo; mantener `resumen_documento()`/`expediente_estado()`.
5. **Gates**: tests, cobertura, Ruff, Django checks, migraciones sin cambios,
   auditoría y revisión de diff por privacidad. Separar Quality Gate remoto y
   medición privada de la evidencia local; commit local, sin push/PR.

## Risks and rollback

- Si un rótulo o una columna es ambiguo, dejar el campo vacío y mostrar
  revisión manual cuando corresponda; no tomar una celda próxima por intuición.
- Si la unificación pierde procedencia o cruza personas, mantener las
  apariciones separadas y volver al contrato F11 hasta corregir la regla.
- Si una nueva regla altera una observación previa, revertir esa rama y
  conservar el resultado histórico; no actualizar la prueba para aceptar
  regresión.
- Si falta respuesta del propietario, la fase permanece planificada. No se
  interpreta «hoy», «sin cónyuge» ni abreviaturas por defecto.

## Complexity Tracking

| Elemento | Motivo | Límite |
|---|---|
| Procedencia por valor con tipo de fuente | FR-001 y prioridad RENIEC ante conflicto biométrico necesitan saber de qué página salió el valor. | Solo cuatro pares nuevos, sin registro genérico de campos. |
| Observaciones estructuradas nuevas en `comparar_personas()` | Mantienen las cadenas de `revisar()` y la comparación ligada F11 en un único camino. | Un adaptador de presentación; sin tercer comparador. |

No se añade abstracción para cónyuge, normalizador libre de domicilios,
persistencia, segmentador de OCR ni dependencia nueva.
