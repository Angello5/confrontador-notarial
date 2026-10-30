# Feature Specification: F65 · Lista de observaciones compacta

**Feature Branch**: `feat/f65-lista-compacta`

**Created**: 2026-10-30

**Status**: Draft

**Input**: User description: "Borrar el cuadro de la derecha (detalle de la observación), porque repite lo que ya dice la lista; alargar la lista y que cada fila muestre, en pequeño, el error y lo que debe decir. Además: la sugerencia en su propia línea, resaltar solo la parte que cambia, que los contadores de severidad no se corten y que el logo tenga alternativa si no carga."

## Origen

En la pantalla de resultado (F56, F60), cada observación aparece dos veces: en la lista y, al elegirla, en el panel de detalle de la derecha, con letras grandes («Dice», «Debe decir») y la casilla «Incluir en las correcciones». El 2026-10-30 el usuario pidió quitar ese panel y que la lista diga lo mismo en pequeño. Pidió también cuatro mejoras de la revisión de interfaz de F64:

1. la sugerencia («Se sugiere …») en su propia línea, en verde;
3. resaltar solo la parte que cambia entre lo hallado y lo correcto;
4. los contadores de severidad no se cortan en pantallas medianas;
6. si el logo no carga, se ve el sello con las iniciales.

## Clarifications

### Session 2026-10-30

- Q: ¿Qué pasa con la casilla «Incluir en las correcciones» que estaba en el panel? → A: pasa a la fila de la lista, compacta (si no, se pierde la elección de correcciones).
- Q: ¿Qué pasa con el fragmento del borrador del panel? → A: la vista del documento (F32) ya marca la observación en la página; la fila dice la línea. Sin vista del documento, la fila elegida muestra la línea del borrador en pequeño.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Revisar sin panel de detalle (Priority: P1)

La usuaria ve la lista a lo ancho. Cada fila dice la severidad, la capa, la línea, el título y, en dos líneas pequeñas, lo que dice el borrador y lo que debe decir, con la parte distinta resaltada. No necesita abrir nada más.

**Independent Test**: confrontar un kardex ficticio con una corrección de nombre, un aviso con sugerencia y un aviso sin sugerencia; la pantalla no tiene panel de detalle y cada fila trae su información.

**Acceptance Scenarios**:

1. **Given** una corrección «ALBA LUMARIA ZAFIRA» → «ALBA LUMARIA ZAFIRO», **When** se ve la lista, **Then** la fila dice «Dice: ALBA LUMARIA ZAFIRA» y «Debe decir: ALBA LUMARIA ZAFIRO», con «ZAFIRA» y «ZAFIRO» resaltadas.
2. **Given** un aviso con sugerencia de F64, **When** se ve la lista, **Then** la fila dice lo hallado, qué verificar y, en su propia línea verde, «Se sugiere: …», con la parte distinta resaltada.
3. **Given** un aviso sin sugerencia, **When** se ve la lista, **Then** la fila dice lo hallado y qué verificar, como hoy.
4. **Given** una observación con corrección automática, **When** la usuaria desmarca la casilla de la fila, **Then** sale de «Aplicar correcciones», igual que antes con la casilla del panel.
5. **Given** la pantalla, **When** se buscan los rótulos «Detalle de la observación», **Then** no existen.

### User Story 2 - Contadores y logo (Priority: P2)

**Acceptance Scenarios**:

1. **Given** una pantalla de 1 024 px de ancho, **When** se ve el resumen, **Then** los tres contadores muestran su rótulo completo sin cortarse.
2. **Given** un logo configurado que no carga, **When** se ve el menú o el ingreso, **Then** aparece el sello con las iniciales y el nombre, no una imagen rota.

### Edge Cases

- Lo hallado y lo correcto sin palabras en común: se resalta todo.
- Sin «Debe decir» (aviso sin sugerencia): no se resalta nada.
- Observaciones lingüísticas: «Texto» y «Sugerencia», con el mismo resaltado.
- Pantalla angosta: la lista sigue a lo ancho debajo de la vista del documento.

## Requirements *(mandatory)*

- **FR-001**: La pantalla de resultado no tiene panel de detalle.
- **FR-002**: Cada fila muestra lo hallado y lo correcto (o qué verificar) en texto pequeño, sin cortar el texto.
- **FR-003**: Entre lo hallado y lo correcto se resaltan solo las palabras distintas.
- **FR-004**: La sugerencia de un aviso va en su propia línea, en verde, con el rótulo «Se sugiere».
- **FR-005**: La casilla de corrección está en la fila y marca o desmarca la misma corrección que «Aplicar correcciones».
- **FR-006**: Los contadores de severidad no se cortan en ningún ancho.
- **FR-007**: Si el logo no carga, se ve el sello con las iniciales y el nombre.
- **FR-008**: Las flechas ↑ y ↓ siguen recorriendo la lista; elegir una fila sigue llevando a su marca en la vista del documento.

### UX Requirements (principio VIII)

- **Minimalismo (8):** una sola vista de cada observación.
- **Reconocer antes que recordar (6):** la parte que cambia se ve sin comparar a ojo.
- **Consistencia (4):** rojo para lo hallado, verde para lo correcto, como en el resto del ERP.

## Success Criteria *(mandatory)*

- **SC-001**: Cada observación se lee y se decide desde su fila, sin otro panel.
- **SC-002**: En las observaciones de prueba, la parte resaltada es exactamente la que cambia.
- **SC-003**: Ningún rótulo de severidad se corta a 1 024 px ni a 1 440 px.

## Assumptions

- El informe Word, PDF y Excel no cambian.
- El cambio es solo de presentación: ni la corrida ni el núcleo cambian.
- Depende de F64 (rama `feat/f64-sugerencias-cifras`) para la sugerencia de los avisos.
