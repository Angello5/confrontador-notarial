# Tasks: F53 · Inicio del administrador

**Input**: Design documents from `specs/041-inicio-administrador/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ui.md, quickstart.md

**Tests**: obligatorios (constitución III y AGENTS.md: «Tests primero»). Cada
test se escribe antes que su implementación y debe fallar primero. Solo datos
ficticios.

**Organization**: por historia de usuario de spec.md (US1 cifras, US2 actividad
y confrontaciones, US3 avisos).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (otro archivo, sin dependencias pendientes)
- **[Story]**: historia de usuario (US1, US2, US3)

## Phase 1: Setup

**Purpose**: preparar el archivo de pruebas común.

- [X] T001 Crear `tests/test_inicio.py` con los ayudantes ficticios `_expediente(codigo, usuario, tipo="NOTARIAL", archivado=False)`, `_documento(expediente, usuario, estado)` (como `_crear_expediente` de `tests/test_shell.py`, con `nombre_original="ficticio-N.txt"`) y `_corrida(expediente, usuario, cuando)`. Este último crea la `Corrida` con los mismos campos que `_corrida` de `tests/test_codigo_y_marca.py`, dentro de `unittest.mock.patch("django.utils.timezone.now", return_value=cuando)`, porque `creado_el` es `auto_now_add` y `Corrida` es inmutable (no admite `update`). Usar las fixtures `usuario_ficticio` y `administrador_ficticio` de `tests/conftest.py`.

---

## Phase 2: Foundational

**Purpose**: separar en la vista el Inicio del administrador del de la usuaria, sin cambiar todavía lo que muestran.

- [X] T002 En `core/views.py`, dividir `home` en dos ramas según `es_administrador` (una cuenta en los dos grupos va por la rama Administrador; spec, Edge Cases). La rama Usuario conserva exactamente el cálculo actual (`expedientes_con_resumen`, `metricas`, `ultimos`) y su comentario `ponytail`. La rama Administrador queda preparada para recibir `cifras`, `actividad`, `confrontaciones` y `avisos`. Comprobar que `python -m pytest tests/test_shell.py` sigue en verde.

**Checkpoint**: las dos ramas existen y nada visible ha cambiado.

---

## Phase 3: User Story 1 - Resumen con cifras que cuadran (Priority: P1) 🎯 MVP

**Goal**: el administrador ve «Total», «Kardex» y «Transferencias vehiculares», que suman el total, sin «Procesando», «Con error», «Requieren su atención» ni «Control administrativo».

**Independent Test**: con kardex ficticios de los dos tipos, estados variados y uno archivado, abrir Inicio como administrador; notariales + vehiculares = total, el archivado no cuenta y los elementos retirados no aparecen.

### Tests for User Story 1 ⚠️ (deben fallar primero)

- [X] T003 [P] [US1] Test de servicio en `tests/test_inicio.py`. Con 2 kardex `NOTARIAL` de la usuaria (uno sin documentos y otro con un documento `PROCESANDO` y otro `ERROR`), 1 `NOTARIAL` del administrador, 2 `VEHICULAR` y 1 `NOTARIAL` archivado, `cifras_por_tipo(administrador)` devuelve `{"notariales": 3, "vehiculares": 2, "total": 5}` y `cifras_por_tipo(usuaria)` solo cuenta los suyos. Afirmar que `total == notariales + vehiculares` y que el estado de los documentos no cambia el conteo (FR-001, US1 escenario 2).
- [X] T004 [P] [US1] Test de vista en `tests/test_inicio.py`. En el Inicio del administrador, `respuesta.context["cifras"]` coincide con T003, y el HTML contiene `href="/expedientes/"` y `href="/expedientes/vehicular/"` (FR-003). No contiene «Procesando», «Con error», «Requieren su atención», «Acceso rápido», «Control administrativo» ni «Administrar usuarios» (FR-002). Además (SC-004), medir con `django_assert_max_num_queries` las consultas del Inicio del administrador con 3 kardex, y repetir con 30 kardex con documentos y corridas: el número de consultas no debe crecer con el número de kardex (fijar el límite al valor medido con 3).

### Implementation for User Story 1

- [X] T005 [US1] Implementar `cifras_por_tipo(usuario)` en `expedientes/services.py`, junto a `expedientes_visibles`. Contar en una sola consulta `expedientes_visibles(usuario)` agrupado por `tipo` con `Count`, y devolver `{"notariales", "vehiculares", "total"}` con `total` = suma (research R2).
- [X] T006 [US1] En la rama Administrador de `core/views.py`, pasar `cifras=cifras_por_tipo(request.user)` y dejar de llamar a `expedientes_con_resumen`.
- [X] T007 [US1] En `templates/core/home.html`, rama `es_administrador`, poner tres métricas con `core/_metrica.html`. «Total» sin `enlace`, con apoyo «Kardex y transferencias activos». «Kardex» con enlace a `{% url 'expediente_lista' %}`. «Transferencias vehiculares» con enlace a `{% url 'vehicular_lista' %}`. Quitar de esa rama el panel «Requieren su atención» y el `panel-oscuro` «Control administrativo». La rama Usuario queda intacta.
- [X] T008 [US1] En `tests/test_shell.py`, actualizar `test_inicio_de_administrador_ofrece_control_administrativo` para que afirme la ausencia de «Control administrativo» (y renombrarlo en consecuencia). En `test_inicio_calcula_metricas_con_la_visibilidad_de_la_lista`, sustituir la comprobación final del administrador (`metricas["total"] == 5`) por `cifras["total"] == 5`.

**Checkpoint**: US1 funciona y se prueba sola; `pytest tests/test_inicio.py tests/test_shell.py` en verde.

---

## Phase 4: User Story 2 - Actividad por semana y últimas confrontaciones (Priority: P2)

**Goal**: el administrador ve 12 barras semanales (kardex distintos confrontados) y las cinco últimas confrontaciones, una por kardex, con la usuaria y la fecha.

**Independent Test**: con corridas ficticias en varias semanas y de dos usuarias, comprobar cifras por semana, semanas en 0, repeticiones contadas una vez y el orden y contenido de la lista.

### Tests for User Story 2 ⚠️ (deben fallar primero)

- [X] T009 [P] [US2] Test de servicio en `tests/test_inicio.py` para `actividad_semanal(hoy=date(2026, 10, 14))` (miércoles). Devuelve 12 elementos `{"inicio", "kardex"}`, el último con `inicio == date(2026, 10, 12)` (lunes) y todos con `inicio` en lunes. Un kardex con 3 corridas en la misma semana suma 1, y dos kardex distintos en la misma semana suman 2. Una semana sin corridas vale 0, y una corrida de hace 13 semanas no aparece. Una corrida de un kardex archivado sí cuenta. Usar `cuando` con zona `America/Lima`, incluido un caso de domingo 23:30 hora de Lima que debe caer en su semana (FR-004).
- [X] T010 [P] [US2] Test de servicio en `tests/test_inicio.py` para `ultimas_confrontaciones()`. Con 7 kardex confrontados (uno de ellos dos veces, por dos usuarias distintas) y uno archivado con la corrida más reciente, devuelve 5 filas sin repetir kardex, sin el archivado y ordenadas por fecha descendente. El kardex repetido muestra la usuaria y la fecha de su última corrida. `usuario` es `get_full_name()` o `username` si está vacío (FR-005).
- [X] T011 [P] [US2] Test de vista en `tests/test_inicio.py`. El Inicio del administrador contiene `aria-label="Kardex confrontados por semana, últimas 12 semanas"` con 12 `<li>`, `aria-label="Últimas confrontaciones"`, el nombre de la usuaria y enlaces a `expediente_detalle`. Sin corridas, muestra «Aún no hay confrontaciones». El HTML no contiene «ficticio-» (nombres de archivo) ni «hash» (FR-006, seguridad).

### Implementation for User Story 2

- [X] T012 [US2] Implementar `actividad_semanal(hoy=None, semanas=12)` en `expedientes/services.py`. `hoy` vale por defecto `timezone.localdate()`; el lunes inicial es el lunes de `hoy` menos 11 semanas. Filtrar `Corrida.objects.filter(creado_el__gte=<inicio local>)`, agrupar con `TruncWeek("creado_el")` y `Count("expediente", distinct=True)`, y completar con 0 las semanas sin datos. Devolver `[{"inicio": date, "kardex": int}]`, de la más antigua a la actual (research R3, data-model).
- [X] T013 [US2] Implementar `ultimas_confrontaciones(limite=5)` en `expedientes/services.py`. Tomar `Expediente.objects.filter(archivado_el__isnull=True)` y anotar `ultima=Max("corridas__creado_el")`. Anotar también `first_name`, `last_name` y `username` del usuario de la última corrida, con un `Subquery` por campo sobre `Corrida` ordenado por `-creado_el, -pk`, y armar el nombre en Python (`get_full_name()` no se puede calcular en SQL). Filtrar `ultima__isnull=False`, ordenar por `-ultima` y cortar en `limite`. Devolver `[{"expediente", "usuario", "fecha"}]`, con `usuario` = nombre completo o `username` (research R4, R5).
- [X] T014 [US2] En la rama Administrador de `core/views.py`, pasar `actividad=actividad_semanal()` y `confrontaciones=ultimas_confrontaciones()`.
- [X] T015 [US2] En `templates/core/home.html`, rama Administrador, añadir dos paneles según `contracts/ui.md`.
  - «Actividad por semana»: `<ol class="semanas" aria-label="Kardex confrontados por semana, últimas 12 semanas">`. Cada `<li>` lleva `style="--alto: N%"`, con el porcentaje respecto al máximo de las 12 semanas (0 % si todo es 0), su cifra en texto y la fecha `d/m` del lunes.
  - «Últimas confrontaciones»: `<ul class="filas" aria-label="Últimas confrontaciones">`. Cada fila enlaza a `expediente_detalle` y muestra código, chip de tipo («Kardex» / «Transferencia vehicular»), usuaria y `d/m/Y H:i`. Si no hay filas, estado vacío `.vacio` con «Aún no hay confrontaciones».
  - El porcentaje se calcula en la vista o en el servicio, no en la plantilla.
- [X] T016 [P] [US2] En `static/css/erp.css`, añadir los estilos de `.semanas` (no `.barra`, que ya es la cabecera): 12 columnas con `display: grid`, una barra de altura `var(--alto)` sobre una base fija, con colores de los tokens `--ne-*` ya existentes, la cifra encima y la fecha debajo, legible a 375 px de ancho. No usar recursos externos.

**Checkpoint**: US1 y US2 funcionan juntas y cada una se prueba sola.

---

## Phase 5: User Story 3 - Aviso de documento ilegible para quien lo subió (Priority: P2)

**Goal**: quien sube un documento que no se pudo leer ve el aviso en su Inicio (cualquier rol); nadie más lo ve; desaparece al resolverse.

**Independent Test**: la usuaria A sube un documento `ERROR` en un kardex antiguo; A ve el aviso; el administrador y la usuaria B no; al archivar el kardex o eliminar el documento, el aviso desaparece.

### Tests for User Story 3 ⚠️ (deben fallar primero)

- [X] T017 [P] [US3] Test de servicio en `tests/test_inicio.py` para `avisos_documentos_ilegibles(usuario)`. Devuelve los kardex activos con algún documento `ERROR` cuyo `subido_por` es `usuario`, sin repetir aunque haya dos documentos `ERROR` en el mismo kardex y ordenados por código. Excluye los documentos `ERROR` de otra persona en un kardex visible para el administrador, los kardex archivados y los documentos `LISTO`. Incluye un kardex con `actualizado_el` más antiguo que otros 6 (sin límite de antigüedad) (FR-007, FR-009, FR-010).
- [X] T018 [P] [US3] Test de vista en `tests/test_inicio.py`. La usuaria ve en su Inicio «Un documento que usted subió no se pudo leer», el código del kardex y un enlace a su detalle, sin el nombre del archivo (FR-008). El administrador no lo ve si no lo subió él, y sí lo ve cuando el documento es suyo. Tras borrar el `Documento`, el aviso desaparece. Ningún rol ve ya «Requieren su atención» (FR-011). Con kardex y corridas de otra persona, el Inicio de la usuaria no contiene «Últimas confrontaciones», «Actividad por semana» ni «Transferencias vehiculares», ni las claves de contexto `cifras`, `actividad` o `confrontaciones` (spec, Security Requirements).

### Implementation for User Story 3

- [X] T019 [US3] Implementar `avisos_documentos_ilegibles(usuario)` en `expedientes/services.py`: `Expediente.objects.filter(archivado_el__isnull=True, documentos__estado=Documento.ERROR, documentos__subido_por=usuario).distinct().order_by("codigo")` (research R6).
- [X] T020 [US3] Crear `templates/core/_avisos_ilegibles.html`. Por cada kardex de `avisos`, mostrar un bloque `.atencion` con el icono `#i-circle-alert`, `<strong>{{ codigo }}</strong>`, el texto «Un documento que usted subió no se pudo leer. Elimínelo y vuelva a subirlo.» y el botón «Abrir kardex» hacia `expediente_detalle`. Envolverlo en `<section aria-labelledby>` con el título «Documentos por revisar». Si `avisos` está vacío, no renderiza nada.
- [X] T021 [US3] En `core/views.py`, pasar `avisos=avisos_documentos_ilegibles(request.user)` en las dos ramas.
- [X] T022 [US3] En `templates/core/home.html`, incluir `core/_avisos_ilegibles.html` arriba del contenido en las dos ramas. En la rama Usuario, eliminar el panel «Requieren su atención» (líneas del bloque `atencion-titulo`), sin tocar sus métricas, «Últimos kardex» ni «Nueva confrontación».

**Checkpoint**: las tres historias funcionan; `pytest tests/test_inicio.py tests/test_shell.py` en verde.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T023 [P] Añadir a `specs/023-interfaz-marca/spec.md` y `specs/009-rediseno-ui/spec.md` una nota en la parte de Inicio: «Reemplazado por F53 (`specs/041-inicio-administrador/`) en el Inicio del administrador y en el aviso de documentos ilegibles».
- [X] T024 [P] Actualizar `docs/roadmap.md`: añadir F53 a «Terminadas» (resultado visible, decisiones «sin pendientes de confrontar» y «kardex distintos por semana», spec 041) y una entrada «Continuación autorizada · 2026-10-18» con lo que pidió el usuario.
- [X] T025 Ejecutar `python -m ruff check .`, `python -m ruff format --check .` y `python -m pytest --cov --cov-report=term` hasta tenerlos en verde. Revisar que el diff no contiene datos reales ni secretos.
- [X] T026 Validación manual según `specs/041-inicio-administrador/quickstart.md`: ERP local, Inicio como administrador y como usuaria, aviso de un documento ilegible ficticio, ancho de 375 px y revisión de las 10 heurísticas de Nielsen (`/speckit-checklist`).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (T001)** → **Foundational (T002)** → US1, US2 y US3.
- US1, US2 y US3 tocan los mismos archivos (`core/views.py`, `templates/core/home.html`, `expedientes/services.py`), así que se integran **en secuencia**: US1 → US2 → US3. Los tests de cada historia son independientes entre sí.
- **Polish** después de las tres historias.

### Within Each User Story

- Tests primero (deben fallar) → servicio → vista → plantilla/CSS.

### Parallel Opportunities

- T003 ∥ T004; T009 ∥ T010 ∥ T011; T017 ∥ T018. Son tests en el mismo archivo pero en funciones distintas, así que pueden escribirse en paralelo si se fusiona con cuidado.
- T016 (CSS) ∥ T012–T015.
- T023 ∥ T024.

## Parallel Example: User Story 2

```text
T009 actividad_semanal (test) ∥ T010 ultimas_confrontaciones (test) ∥ T011 vista (test)
luego T012 → T013 → T014 → T015, con T016 (CSS) en paralelo
```

## Implementation Strategy

### MVP First (User Story 1)

1. T001–T002.
2. T003–T008: cifras que cuadran y paneles retirados.
3. **Parar y validar**: ya resuelve la queja principal (8 ≠ 6).

### Incremental Delivery

1. + US2 (actividad y últimas confrontaciones) → validar.
2. + US3 (avisos para quien subió el documento) → validar.
3. Polish: specs relacionadas, roadmap, lint, cobertura y revisión manual.
