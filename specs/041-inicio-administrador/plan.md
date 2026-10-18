# Implementation Plan: F53 · Inicio del administrador

**Branch**: `041-inicio-administrador` | **Date**: 2026-10-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/041-inicio-administrador/spec.md`

## Summary

El Inicio del Administrador pasa a mostrar las cifras por tipo (kardex y
transferencias vehiculares, que suman el total), la actividad por semana de las
últimas 12 semanas (kardex distintos confrontados) y las cinco últimas
confrontaciones con la usuaria que la ejecutó. Se retiran «Procesando», «Con
error», «Requieren su atención» y «Control administrativo». En todos los roles,
el panel «Requieren su atención» se sustituye por avisos de documento ilegible
dirigidos a quien subió el documento. Todo se calcula con consultas agregadas
sobre modelos existentes: sin migraciones ni dependencias.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Django (LTS vigente), Alpine.js ya instalado (no se usa aquí), CSS propio `static/css/erp.css`

**Storage**: PostgreSQL; sin cambios de esquema

**Testing**: pytest + pytest-django con datos ficticios

**Target Platform**: servidor on-premise en la LAN de la notaría

**Project Type**: monolito Django (web, plantillas del servidor)

**Performance Goals**: Inicio < 2 s con miles de kardex y ≤ 10 usuarias (SC-004)

**Constraints**: sin CDN, sin dependencias nuevas, sin IA; textos en español notarial

**Scale/Scope**: 1 vista, 1 plantilla + 1 parcial, 4 funciones de servicio, CSS del gráfico

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| I. Determinismo, sin IA | Solo conteos y consultas; ninguna llamada a modelos ni import de `experimental/` | ✅ |
| II. Núcleo puro, vistas delgadas | La lógica de consulta va en `expedientes/services.py`; `home` solo llama y renderiza. No toca `nucleo/` | ✅ |
| III. Pruebas primero | Cada FR empieza con un test que falla en `tests/test_inicio.py`; se adaptan los tests de `test_shell.py` que afirmaban el diseño anterior | ✅ |
| IV. Privacidad | Solo códigos de kardex, tipos, nombres de usuarias del sistema, fechas y cifras; ni nombres de archivo ni datos de comparecientes. No se persiste nada nuevo | ✅ |
| V. Simplicidad | Sin modelos, migraciones, apps ni bibliotecas nuevas; gráfico en HTML+CSS | ✅ |
| VI. Seguridad y roles | Cifras globales, actividad y confrontaciones ajenas solo para Administrador (`es_administrador`); avisos filtrados por `subido_por`; `home` sigue exigiendo login y rol | ✅ |
| VII. DevSecOps | Mismo pipeline: ruff, pytest con cobertura, Sonar, pip-audit, gitleaks | ✅ |
| VIII. Usabilidad | Cifras enlazadas a su lista, estados vacíos, mensajes con qué pasó y qué hacer, gráfico con cifras en texto y `aria-label` | ✅ |

**Re-check post-design**: sin cambios; ninguna violación. Complexity Tracking vacío.

## Project Structure

### Documentation (this feature)

```text
specs/041-inicio-administrador/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/ui.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
expedientes/services.py           # + cifras_por_tipo, actividad_semanal,
                                  #   ultimas_confrontaciones, avisos_documentos_ilegibles
core/views.py                     # home: rama Administrador / Usuario
templates/core/home.html          # dos ramas; sin paneles retirados
templates/core/_avisos_ilegibles.html   # nuevo parcial (los dos roles)
static/css/erp.css                # barras del gráfico semanal
tests/test_inicio.py              # nuevo: FR-001…FR-011
tests/test_shell.py               # ajustar tests del Inicio anterior
specs/023-interfaz-marca/spec.md, specs/009-rediseno-ui/spec.md  # nota de que F53 los reemplaza en Inicio
docs/roadmap.md                   # F53 en «Terminadas» y «Continuación autorizada»
```

**Structure Decision**: monolito Django existente. La consulta va en la app
`expedientes`, dueña de los modelos; la presentación, en `core`, dueña de
Inicio.

## Notas de implementación

- Tests de `test_shell.py` que cambian: `test_inicio_de_administrador_ofrece_control_administrativo`
  (pasa a afirmar la ausencia) y `test_inicio_calcula_metricas_con_la_visibilidad_de_la_lista`
  (su parte de administrador pasa a `cifras`). El resto del Inicio del Usuario
  se conserva.
- `TruncWeek` y `Max`/`Subquery` funcionan en PostgreSQL, la base de los tests y
  del CI.
- El aviso `ponytail` de `core/views.py` (resumen por kardex) queda solo en la
  rama Usuario, que ve únicamente sus kardex.

## Complexity Tracking

Sin violaciones.
