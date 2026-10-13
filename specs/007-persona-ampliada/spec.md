# Feature Specification: F12 · Persona ampliada

**Feature Branch**: `feature/f12-persona-ampliada`

**Created**: 2026-09-25

**Status**: Implementado e integrado (PR #40). Pendiente: medición privada T027, gate del propietario

**Input**: `docs/catalogo-datos.md` midió sobre 435 páginas que solo la consulta RENIEC aporta estado civil, fecha de nacimiento, domicilio y distrito de domicilio con las coberturas documentadas, y que el ERP los descarta. Decisión del propietario: incorporarlos a la persona y usarlos en la confrontación.

## Clarifications

### Session 2026-09-25

- Q: ¿Qué campos entran? → A: `estado_civil`, `fecha_nacimiento`, `domicilio` y `distrito`. El cónyuge de la declaración jurada queda para otra fase.
- Q: ¿De qué documentos se leen? → A: Solo de la **consulta RENIEC**. La ficha biométrica no trae estos campos: el "estado civil" que se le atribuía venía del pie "Registro Nacional de Identificación y Estado Civil", detectado al revisar el plan. La declaración jurada (manuscrita) y el DNI escaneado no aportan estos campos en esta fase.
- Q: ¿Qué gana la confrontación? → A: Tres reglas nuevas, en la capa de regla: (1) compareciente casado según la fuente que la minuta presenta como soltero o sin cónyuge; (2) compareciente menor de edad; (3) domicilio de la fuente que no aparece en el borrador.
- Q: US1, ¿se compara contra la minuta, el borrador o ambos? → A: Contra el **borrador**, que es lo que se confronta; la minuta es una fuente más. "Sin mención de cónyuge" significa: en el borrador, la cláusula donde aparece el nombre de la persona (desde el nombre hasta el siguiente punto y seguido o salto de línea, ampliada a la anterior si el nombre abre la cláusula) no contiene ningún marcador de estado civil (`CASAD[AO] CON`, `SOLTER[AO]`, `VIUD[AO]`, `DIVORCIAD[AO]`, `CONVIVIENTE`). Un cónyuge mencionado en otra cláusula no cuenta: la observación es por persona, no por documento.
- Corrección (2026-09-27): la primera aparición del nombre solía ser la carátula o el encabezado, no la comparecencia. La cláusula de la persona pasa a ser, en este orden: (1) la primera línea con su DNI exacto (no dentro de otro número) y un marcador de estado civil; (2) la primera línea con su nombre exacto y un marcador; (3) la primera línea con su DNI exacto; (4) la regla anterior. Aplica a las reglas de estado civil y cónyuge; el domicilio sigue la regla de F16.
- Q: ¿Cambia la persistencia? → A: No en esta fase. La persona ampliada se calcula al confrontar, como el resto del catálogo; la persistencia es F6.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Estado civil que no cuadra (Priority: P1)

Como notario, quiero que el sistema avise cuando la fuente oficial dice que un compareciente es casado y el borrador lo presenta como soltero, o al revés, para no autorizar un acto de disposición sin el cónyuge.

**Why this priority**: Es el error de fondo más caro de una escritura: un bien social vendido por uno solo de los cónyuges.

**Independent Test**: Una consulta RENIEC ficticia con `Estado Civil: CASADO` y un borrador ficticio que lo llama soltero producen una observación; si el borrador dice "casado con …", no.

**Acceptance Scenarios**:

1. **Given** una persona con `estado_civil = CASADO` en la fuente, **When** el borrador la presenta como soltera o sin mención de cónyuge, **Then** se genera una observación que nombra a la persona y el estado civil de la fuente.
2. **Given** una persona casada en la fuente, **When** el borrador dice "casado con", **Then** no hay observación.
3. **Given** una persona con `estado_civil = SOLTERO` en la fuente, **When** el borrador la presenta como casada, **Then** se genera observación.
4. **Given** una fuente sin estado civil legible, **When** se confronta, **Then** no se genera ninguna observación de estado civil para esa persona.

### User Story 2 - Menor de edad (Priority: P1)

Como notario, quiero que el sistema señale a un compareciente menor de edad según su fecha de nacimiento, para no dejarlo pasar entre decenas de páginas.

**Acceptance Scenarios**:

1. **Given** una persona con fecha de nacimiento que implica menos de 18 años, **When** se confronta, **Then** se genera una observación con la edad calculada.
2. **Given** una fecha ilegible o ausente, **Then** no se genera observación ni error.

Decisión del propietario (2026-09-25): la edad se calcula **a la fecha de hoy**; la observación muestra la fecha usada. Extraer la fecha del acto queda como deuda.

### User Story 3 - Domicilio que no aparece (Priority: P2)

Como notario, quiero saber cuándo el domicilio de la fuente oficial no aparece en el borrador, para revisar si se copió mal.

**Acceptance Scenarios**:

1. **Given** una persona con domicilio en la fuente, **When** el borrador no lo contiene tras normalizar, **Then** se genera una observación con el domicilio esperado.
2. **Given** el domicilio presente con diferencias solo de tildes, mayúsculas o abreviaturas comunes (AV./AVENIDA, JR./JIRÓN, MZ./MANZANA, LT./LOTE), **Then** no hay observación.

Decisión del propietario (2026-09-25): equivalencias de vía peruanas habituales: AV/AVENIDA, JR/JIRÓN, CA/CALLE, PSJ/PASAJE, MZ/MANZANA, LT/LOTE, URB/URBANIZACIÓN, AAHH/ASENTAMIENTO HUMANO, DPTO/DEPARTAMENTO, INT/INTERIOR, N°/NÚMERO, S/N. Se comparan sin puntos, tildes ni orden del número.

Ampliación (2026-10-03, a pedido del propietario tras revisar expedientes reales): `ASENT.H.`, `ASENT. H.` y `AA.HH.` se leen como AAHH; `ASENT`/ASENTAMIENTO y `ASOC`/ASOCIACIÓN; el número pegado a su abreviatura se separa (`LT6` = `LT 6`) y los ceros a la izquierda no cuentan (`LOTE 05` = `LT.5`). Omitir el tipo de zona («Manzana G Lote 5 Luna» frente a «AAHH Luna Mz G Lt 5») es un error y se señala (decisión del propietario, 2026-10-03).

Representante (decisión del propietario, 2026-10-03): si la línea de la persona dice que procede en representación (`REPRESENTACION`, `REPRESENTANTE`, `APODERADO/A`), su domicilio se coteja con las direcciones de los recaudos y no con su domicilio RENIEC; sin respaldo en los recaudos se sigue señalando `DOMICILIO_NO_ENCONTRADO`. Los domicilios RENIEC de otras personas no cuentan como respaldo. [NEEDS CLARIFICATION] una persona que procede por derecho propio con el domicilio que la minuta fija «para efectos de este contrato» se sigue señalando.

### User Story 4 - Ver los campos nuevos (Priority: P2)

Como notario, quiero ver estado civil, fecha de nacimiento, domicilio y distrito de cada persona en la tabla de extracción, con su procedencia, para verificar una observación sin releer el legajo.

### Edge Cases

- La misma persona aparece en dos consultas RENIEC con estado civil distinto: se conserva la de fecha de emisión más reciente y se marca conflicto para revisión manual.
- El estado civil viene con género (CASADA/CASADO) o en minúsculas: se normaliza.
- La fecha viene en formato `dd/mm/aaaa` con separadores mal leídos por OCR (`03/07/1976`, `03-07-1976`, `03/07/197б`): se acepta lo claro y se descarta lo dudoso sin inventar.
- Persona sin documento pero con estado civil: no participa en la regla de cónyuge, porque no está confirmada.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `Persona` DEBE incorporar `estado_civil`, `fecha_nacimiento`, `domicilio` y `distrito`, todos opcionales, con la procedencia de cada uno.
- **FR-002**: Los campos DEBEN leerse solo de páginas clasificadas como RENIEC, por etiqueta al inicio de línea y valor en su columna: `ESTADO CIVIL`, `FECHA DE NACIMIENTO`, `DIRECCIÓN` y `DISTRITO DE DOMICILIO`. `DISTRITO DE NACIMIENTO` NO es el distrito de domicilio. El pie "IDENTIFICACIÓN Y ESTADO CIVIL" no es un campo.
- **FR-003**: `estado_civil` DEBE normalizarse a SOLTERO / CASADO / VIUDO / DIVORCIADO sin género; el género se conserva aparte si hace falta mostrarlo.
- **FR-004**: `fecha_nacimiento` DEBE normalizarse a fecha; una fecha no interpretable con certeza se descarta.
- **FR-005**: La capa de regla DEBE emitir observación cuando el estado civil de la fuente contradiga al del borrador (US1).
- **FR-006**: La capa de regla DEBE emitir observación cuando la fecha de nacimiento implique minoría de edad (US2).
- **FR-007**: La capa de regla DEBE emitir observación cuando el domicilio de la fuente no aparezca en el borrador tras normalizar (US3).
- **FR-008**: La tabla de extracción DEBE mostrar los campos nuevos con su procedencia.
- **FR-009**: La confrontación existente (nombres, documentos, partidas, montos, párrafos, documento cruzado) NO DEBE cambiar de comportamiento.
- **FR-010**: Ninguna migración ni entidad nueva: la persona ampliada vive en memoria, como el catálogo.

### Requisitos de seguridad y privacidad (Constitución I, II y IV)

- Núcleo puro y determinista; sin modelos ni red.
- Estado civil, fecha de nacimiento y domicilio son datos personales: se muestran al usuario autorizado, nunca en logs ni en mensajes de error, y nunca viajan por el endpoint JSON de sondeo.
- Solo datos ficticios en pruebas, fixtures, commits y documentación.

### Requisitos de usabilidad (Constitución VIII)

- Cada observación nueva dice qué persona, qué dice la fuente, qué dice el borrador y de qué archivo y página sale el dato.
- Una observación de menor de edad muestra la edad calculada y la fecha usada.

## Success Criteria *(mandatory)*

- **SC-001**: Ficha RENIEC ficticia → persona con los cuatro campos y su procedencia.
- **SC-002**: Casado en fuente + soltero en borrador → una observación; casado con cónyuge → ninguna.
- **SC-003**: Fecha que implica 17 años → observación con la edad.
- **SC-004**: Domicilio con abreviaturas equivalentes → ninguna observación; ausente → una.
- **SC-005**: Sobre las mismas entradas ficticias, todas las observaciones previas a la fase son idénticas.
- **SC-006**: Ningún dato real en el diff.

## Assumptions

- `docs/catalogo-datos.md` y `docs/catalogo-fuentes.md` son la referencia de etiquetas y fiabilidad.
- El cónyuge de la declaración jurada, las personas jurídicas y la fecha del acto quedan fuera y se anotan como deuda.
- La medición privada contra el expediente de referencia sigue siendo el gate.
