# Research: F53 · Inicio del administrador

No quedan `[NEEDS CLARIFICATION]` en la spec. Estas son las decisiones técnicas
tomadas a partir del código existente.

## R1. Dónde se calcula cada dato

- **Decision**: cuatro funciones nuevas en `expedientes/services.py`, junto a
  `expedientes_visibles`: `cifras_por_tipo`, `actividad_semanal`,
  `ultimas_confrontaciones` y `avisos_documentos_ilegibles`. `core/views.home`
  solo las llama y renderiza.
- **Rationale**: principio II (vistas delgadas, la consulta en `services.py`);
  los modelos y la regla de visibilidad ya viven en `expedientes`.
- **Alternatives considered**: calcularlo en la vista (rompe II); una app
  `inicio` nueva (abstracción sin necesidad, principio V).

## R2. Cifras por tipo

- **Decision**: `expedientes_visibles(usuario)` agrupado por `tipo` con
  `Count`, en una consulta. Total = suma de las dos cifras.
- **Rationale**: reutiliza la regla de visibilidad (el administrador ve todo) y
  el filtro de archivados; el total cuadra por construcción (FR-001).
- **Alternatives considered**: reutilizar `expedientes_con_resumen`, que calcula
  un resumen por kardex (una consulta por kardex): innecesario aquí.

## R3. Actividad semanal: kardex distintos por semana

- **Decision**: `Corrida` filtrada desde el lunes de hace 11 semanas, agrupada
  con `TruncWeek("creado_el")` y `Count("expediente", distinct=True)`. Se
  completan en Python las semanas sin corridas con 0. Incluye corridas de
  kardex archivados (registro histórico, spec «Edge Cases»).
- **Rationale**: `TruncWeek` corta en lunes y respeta `TIME_ZONE =
  "America/Lima"` con `USE_TZ`; el `distinct` aplica la decisión del usuario
  (un kardex cuenta una vez por semana).
- **Alternatives considered**: contar en Python todas las corridas (más datos
  en memoria); contar corridas sin `distinct` (descartado por el usuario).

## R4. Últimas confrontaciones: un kardex por fila

- **Decision**: `Expediente` activos con `ultima=Max("corridas__creado_el")`,
  ordenados por `-ultima`, primeros 5; la usuaria y la fecha salen de la última
  corrida de cada uno con un `Subquery`. Solo kardex activos, porque el detalle
  de un archivado no se puede abrir (`_expediente_visible`).
- **Rationale**: una consulta, sin depender de `DISTINCT ON` de PostgreSQL.
- **Alternatives considered**: últimas 5 corridas sin agrupar (repetiría el
  mismo kardex, contra la decisión del usuario).

## R5. Usuaria de una confrontación automática

- **Decision**: se muestra `Corrida.usuario` tal cual.
- **Rationale**: en la confrontación automática ya se registra quien subió el
  borrador (`expedientes/solicitudes.py`, `usuario=borrador.subido_por`). No
  hace falta cambiar el registro inmutable.
- **Nombre mostrado**: `get_full_name()` o, si está vacío, `username`.

## R6. Avisos de documento ilegible

- **Decision**: `Documento` con `estado=ERROR`, `subido_por=usuario` y kardex
  activo, agrupado por kardex (`values` + `distinct`). Sin límite de
  antigüedad. Se calcula al abrir Inicio, así que desaparece cuando el
  documento se elimina o se reemplaza, o el kardex se archiva (FR-010).
- **Rationale**: no necesita estado nuevo ni modelo de notificaciones
  (principio V); sustituye el panel actual, que solo recorría los 5 kardex más
  recientes.
- **Alternatives considered**: un modelo `Notificacion` con leído/no leído
  (complejidad sin pedido del usuario).

## R7. Gráfico semanal sin dependencias

- **Decision**: lista `<ol>` de 12 barras en HTML y CSS. La altura se pasa con
  una variable CSS inline (`style="--alto: 40%"`), y cada barra lleva su cifra
  y la fecha de inicio de semana en texto. Encima, un `aria-label` resume el
  gráfico.
- **Rationale**: sin CDN ni bibliotecas (constitución). La cifra en texto
  cumple FR-006 y la accesibilidad. No hay CSP que impida `style` inline, que ya
  se usa en otras plantillas.
- **Alternatives considered**: Chart.js en `static/vendor` (dependencia nueva
  para 12 barras); SVG generado (más código para el mismo resultado).

## R8. Una plantilla o dos

- **Decision**: se mantiene `templates/core/home.html` con dos ramas
  (`es_administrador` / resto). Los avisos van en un parcial nuevo
  `core/_avisos_ilegibles.html`, que usan las dos ramas.
- **Rationale**: un solo punto de entrada (`home`), como hoy; el parcial evita
  duplicar los avisos.

## R9. Rendimiento

- **Decision**: el Inicio del administrador deja de llamar a
  `expedientes_con_resumen`, que hace una consulta por kardex. Usa 4 consultas
  agregadas. El Inicio del Usuario no cambia su cálculo.
- **Rationale**: SC-004 (< 2 s con miles de kardex). Resuelve el aviso
  `ponytail` de `core/views.py` para el administrador, que ve todos los kardex.
