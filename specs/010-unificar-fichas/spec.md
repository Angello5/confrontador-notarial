# Feature Specification: F15 · Una persona por DNI entre fichas oficiales

**Feature Branch**: `feature/f15-unificar-fichas`

**Created**: 2026-09-27

**Status**: Draft

**Input**: Tras F13, cada ficha RENIEC o biométrica es un ancla. En los 10 expedientes medidos, 28 documentos distintos producen 32 anclas: **4 personas aparecen dos veces** porque el OCR leyó el nombre de su ficha biométrica con una diferencia mínima frente a la RENIEC (un espacio leído como «I», una «M» leída como «V», un espacio perdido) o truncado. Hoy quedan como dos anclas del mismo DNI en revisión manual, y el propietario ve personas duplicadas. Caso reportado: expediente 71856, una persona con dos fichas y un carácter de diferencia.

## Principio

**El DNI es único: dos fichas oficiales con el mismo DNI son la misma persona.** Decidido por el propietario el 2026-09-27.

## Clarifications

### Session 2026-09-27

- Q: ¿Qué hacer cuando dos fichas oficiales tienen exactamente el mismo DNI y el nombre difiere? → A: Una sola persona. Nombre de la ficha RENIEC; la variante de la otra ficha queda como dato adjunto con su procedencia. Revisión manual solo si los nombres difieren mucho: más de 2 letras de diferencia o un nombre truncado.
- Q: ¿Y si las dos fichas son del mismo tipo (dos RENIEC o dos biométricas)? → A: Manda la de `FECHA DE EMISION` más reciente, como en F12; si no hay fecha legible, la primera por orden de página. [Regla derivada de F12, sin decisión nueva.]
- Q: ¿Cambia algo si el DNI difiere? → A: No. Documento distinto nunca se unifica (F13 FR-005 sigue igual).

## Requirements *(mandatory)*

- **FR-001**: Dos anclas con el **mismo documento exacto** DEBEN unificarse en una sola persona, cualquiera sea la diferencia de nombre.
- **FR-002**: El nombre de la persona unificada DEBE ser el de la ficha RENIEC. Entre fichas del mismo tipo, el de emisión más reciente (F12); sin fecha, el primero por orden de página.
- **FR-003**: El nombre distinto de la otra ficha DEBE conservarse como **adjunto** de la persona, con su procedencia (archivo y página), igual que los adjuntos de F13. Así sigue llegando a la proyección `NOMBRE` y la capa de campos no cambia.
- **FR-004**: La persona unificada DEBE quedar `CONFIRMADA` cuando las claves de nombre (`_nombre_clave`, sin espacios) difieren en **2 ediciones o menos** (distancia de Levenshtein). DEBE quedar en `REVISION_MANUAL` cuando difieren en más de 2 o cuando una clave está contenida en la otra y es más corta (nombre truncado).
- **FR-005**: Los conflictos de campos F12 entre fichas (estado civil, fecha de nacimiento, domicilio) conservan su regla actual: emisión más reciente y revisión manual.
- **FR-006**: Procedencias: la persona unificada lleva las procedencias de todas sus fichas.
- **FR-007**: Núcleo puro y determinista; la distancia se calcula con `rapidfuzz`, ya presente. Sin dependencias, migraciones ni cambios del sondeo JSON.
- **FR-008**: Solo datos ficticios en tests (DNI `9000xxxx`, nombres inventados).

## Success Criteria *(mandatory)*

Medidos por el revisor con el mismo guion privado sobre los 10 expedientes, solo recuentos:

- **SC-001**: Anclas = documentos distintos con ficha completa: **28 anclas para 28 documentos** (hoy 32).
- **SC-002**: Revisión manual solo para el caso de nombre truncado: **1 persona** (hoy 4 pares, 8 marcas).
- **SC-003**: El expediente 71856 muestra **1 persona con ficha**, confirmada (hoy 2 en revisión).
- **SC-004**: La salida literal de `revisar()`, `correspondencia()`, `diagnostico()` y `revisar_parrafos()` sobre los fixtures ficticios es idéntica antes y después.
- **SC-005**: Menciones sin ficha, adjuntos de fuentes no oficiales y reglas F12/F13 sin cambios fuera de lo descrito.

## Assumptions

- La unificación ocurre dentro de `unificar_personas()` para anclas, antes del pegado de adjuntos de F13.
- «Más de 2 letras» se mide sobre la clave sin espacios para que un espacio perdido o leído como letra cuente como una sola edición.
- Deuda: corregir el OCR del nombre en origen; nombre truncado en la RENIEC (y completo en la biométrica) se resuelve igual que el caso inverso, con revisión manual.
- Implementación: entre dos RENIEC del mismo documento, una con `FECHA DE EMISION` legible manda sobre otra sin fecha (misma regla que F12 para los campos).
- Implementación: un registro no oficial sin documento se pega también por la clave exacta de la variante adjunta, como antes se pegaba al ancla duplicada; si esa clave coincide con más de un ancla, sigue siendo mención.
- Consecuencia de FR-001: un documento suelto que antes quedaba como mención por pertenecer a dos anclas del mismo DNI ahora se adjunta a la persona unificada.
