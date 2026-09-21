# Implementation Plan: F5 · Confrontación

**Branch**: `feature/f5-confrontacion` | **Date**: 2026-09-20 | **Spec**: [spec.md](spec.md)

**Input**: `specs/005-confrontacion/spec.md`, aprobado y no modificable en esta etapa.

## Summary

Conectar los textos extraídos de F4 con las capas deterministas de regla y
ortografía, calcular un resultado en memoria por borrador y mostrarlo agrupado
en la pantalla del expediente. La orquestación se mantiene en
`expedientes/services.py`; la vista solo autoriza, valida, llama al servicio y
renderiza. F5 no ejecuta léxico, no persiste observaciones, no cambia el núcleo
y no importa `app.py`, `app_ortografia.py` ni `experimental/`.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.13.

**Primary Dependencies**: Django 5.2.17, pytest/pytest-django/pytest-cov,
`rapidfuzz`, `spylls`, `pymupdf` y los adaptadores ya fijados. No se añade
ninguna dependencia.

**Storage**: PostgreSQL como origen de `Expediente`, `Documento` y
`TextoExtraido` de F4. F5 añade una migración reversible de roles (`FUENTE` a
`CLIENTE`); no crea filas de resultados, que viven en memoria durante la
respuesta.

**Testing**: pytest con PostgreSQL del proyecto, datos ficticios, pruebas de
servicios y de integración de vistas/permisos/UI. Se ejecutan primero pruebas
rojas para la orquestación y el adaptador de observaciones; la medición
`local_reference` sigue siendo privada y explícita.

**Target Platform**: servidor Django on-premise en la LAN, sin dependencias de
internet en tiempo de ejecución.

**Project Type**: aplicación web Django monolítica con plantillas AdminLTE 4,
Bootstrap 5 y Alpine.js locales.

**Performance Goals**: la confrontación se calcula bajo demanda; no se define
una latencia nueva. Si tarda más de un segundo, la pantalla muestra estado de
trabajo y no un porcentaje inventado.

**Constraints**: consumir el núcleo sin cambiar su comportamiento; pasar
`CLIENTE` y `MINUTA` con el nombre original como clave; separar minutas por rol,
no por extensión; usar umbral 88 oculto; pasar nombres propios aceptados a
ortografía; no importar IA/`experimental/`; no persistir resultados; no añadir
entidades, dependencias, API pública, SPA, HTMX, Redis o cola nueva; no mostrar
datos personales en logs/mensajes.

**Scale/Scope**: máximo aproximado de 10 usuarios del ERP. Un expediente puede
tener varias fuentes y varios borradores; cada borrador listo se confronta por
separado. F5 cubre regla y ortografía en pantalla; léxico es F10, persistencia
es F6 e informe exportable es F7.

## Constitution Check

*GATE: compatible antes de investigación; se reevalúa después del diseño.*

| Principio | Comprobación del diseño | Resultado |
|---|---|---|
| I. Determinismo y sin IA | Se llaman únicamente funciones puras de `nucleo` y adaptadores locales. La entrada se ordena por consultas estables, el umbral es 88 fijo y no se importa `experimental/` ni se llama a modelos. | PASS |
| II. Núcleo de dominio puro | `nucleo/verificar.py` y `nucleo/ortografia.py` no se modifican. `services.py` orquesta y la vista solo valida, autoriza y renderiza; el texto ya extraído llega desde F4. | PASS |
| III. Pruebas primero | Las pruebas de servicio, parser, precondiciones, diagnóstico, ortografía, permisos y UI se escriben y verifican en rojo antes de implementar. Solo se usan datos ficticios. | PASS, sujeto al orden TDD de `tasks.md` |
| IV. Privacidad | No se guardan observaciones, no se crean archivos y no se muestran rutas, hashes ni texto completo. El fragmento mínimo solo se renderiza al usuario autorizado y no entra en logs/mensajes de error. | PASS |
| V. Simplicidad | Se reutiliza la app `expedientes`, servicios y modelos de F4; se usan dicts/listas existentes y no se añade una capa, API, entidad o dependencia de un solo uso. | PASS |
| VI. Seguridad y control de acceso | La acción POST exige login, rol y pertenencia mediante `usuario_puede_ver_expediente`; se valida que el documento sea un borrador del expediente y que el estado/texto permita procesar. | PASS |
| VII. DevSecOps | Se mantienen Ruff, pytest/cobertura, Sonar, `pip-audit`, gitleaks y locks; la nueva ruta queda cubierta por tests y no se relajan gates. | PASS |
| VIII. Usabilidad | Contrato en español con advertencia de correspondencia, estados, recuentos por capa, estado vacío, ubicación, mensajes seguros, teclado, foco, etiquetas y contraste; revisión Nielsen separada. | PASS |

**Resultado previo a investigación**: PASS. La única decisión abierta es el
límite ya reportado en `research.md` para ubicar un párrafo alterado cuando no
existe coincidencia literal; no bloquea la implementación prevista y no se
inventará una regla de negocio.

## Project Structure

### Documentation (this feature)

```text
specs/005-confrontacion/
├── spec.md                         # aprobado; no se modifica
├── research.md                     # decisiones y alternativas
├── plan.md                         # este plan
├── contracts/ui.md                 # pantalla, estados y mensajes
├── tasks.md                        # orden ejecutable de implementación
└── checklists/
    ├── requirements.md             # trazabilidad y calidad de requisitos
    └── ux.md                       # Nielsen y accesibilidad
```

No se crea `data-model.md`: F5 modifica roles existentes, pero no añade
entidades. La migración reversible se incluye en `expedientes/migrations/`.
Tampoco se
crea `quickstart.md` en esta etapa porque el entregable aprobado enumera los
seis artefactos anteriores; la validación operativa se describe en las tareas
y en el contrato UI.

### Source Code (repository root)
<!--
  Concrete source layout for the implementation stage:
  Paths below are the only intended implementation files for F5.
-->

```text
expedientes/
├── services.py                    # añadir orquestación y adaptación de resultado
├── urls.py                        # añadir ruta POST de confrontación
└── views.py                       # añadir validación/autorización/renderizado del resultado

templates/expedientes/
├── detalle.html                   # añadir acción/estado por borrador
└── confrontacion.html             # pantalla de resultados en español

tests/
├── test_expedientes_confrontacion.py      # servicios, parser y determinismo
└── test_expedientes_confrontacion_ui.py   # rutas, permisos, estados y mensajes

specs/005-confrontacion/
├── contracts/ui.md
├── research.md
├── plan.md
├── tasks.md
└── checklists/
```

**Structure Decision**: mantener la app F4 como borde de persistencia y
añadir solo el servicio y la plantilla necesarios para F5. No se modifican
`nucleo/`, `app.py` ni `app_ortografia.py`; los tests se separan por servicio y
UI para poder demostrar pruebas rojas y permisos sin crear otro módulo.

## Phase 0: Research

`research.md` resuelve la frontera F4/F5, el consumo del núcleo, las fuentes
por nombre original, la separación de minutas, el diagnóstico previo, el
parser de observaciones de regla, la adaptación de ortografía y las decisiones
de UI/privacidad. No quedan decisiones de negocio inventadas.

## Phase 1: Design and Validation

- `contracts/ui.md` define la acción por borrador, estados de precondición,
  advertencia de correspondencia, agrupación, campos, ubicación y mensajes.
- `tasks.md` ordena tests rojos, migración de roles, servicio, vista/URL,
  plantilla y gates sin crear entidades nuevas.
- Los checklists revisan trazabilidad de requisitos y las 10 heurísticas de
  Nielsen; ningún ítem se marca como evidencia de implementación en esta fase.

## Constitution Check después del diseño

I–VIII permanecen en PASS: no se toca el núcleo, no se añaden dependencias ni
persistencia, el resultado es determinista y la acción queda protegida por el
control de acceso ya probado en F4. La ubicación se calcula en aplicación,
porque es presentación. El parser es un adaptador local necesario para
consumir la API actual `list[str]`; no cambia sus salidas.

## Complexity Tracking

| Elemento | Motivo | Alternativa más simple considerada y razón para descartarla |
|---|---|---|
| Parser de observaciones en `services.py` | El núcleo ya expone strings y la UI necesita campos separados; permite conservar el comportamiento medido y centralizar la adaptación. | Cambiar el núcleo a tuplas/dicts altera API y medición; usar regex dispersas en la plantilla es frágil y viola vista delgada. |
| Cálculo de ubicación en aplicación | Número de línea y fragmento son presentación, no regla de negocio; el núcleo no debe conocer expedientes ni UI. | Añadir ubicación al núcleo mezcla capas y cambia su contrato; usar el contexto normalizado que ya trae la string no da línea fiable. |

No hay violaciones de la constitución ni dependencias nuevas que justificar.
