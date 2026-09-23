# Feature Specification: F11 · Extracción por personas

**Feature Branch**: `feature/f11-personas`

**Created**: 2026-09-22

**Status**: Draft

**Input**: El notario detectó que el sistema asigna un documento de identidad a la persona equivocada. La causa no es la expresión regular: el catálogo guarda nombres y documentos en conjuntos separados, sin ningún vínculo entre persona y documento, y además incorpora identidades que no son parte del acto.

## El problema, demostrado

Con dos comparecientes y sus documentos intercambiados en el borrador:

```
catálogo:  NOMBRE: ['LUIS ALBERTO TORRES VARGAS', 'ROSA ELENA QUISPE MAMANI']
           DNI:    ['90000011', '90000022']

borrador con los DNI intercambiados entre las dos personas
  observaciones: NINGUNA
```

La comprobación actual es "¿este documento aparece en algún sitio de las
fuentes?", y la respuesta es sí aunque pertenezca a otra persona.

A eso se suma lo que documenta `docs/catalogo-fuentes.md`: los documentos
oficiales traen, en la misma hoja, al ciudadano, al empleado que hizo la
consulta y al notario; y el tipo de página más numeroso del corpus lista
personas de listas restrictivas que no son parte del acto.

## Clarifications

### Session 2026-09-22

- Q: ¿Por qué no basta con mejorar las expresiones regulares? → A: Porque el problema es el modelo de datos, no la búsqueda. Mientras el catálogo sean conjuntos sueltos, ninguna regex puede detectar un documento cruzado.
- Q: ¿Se extrae una persona por archivo? → A: No. Un legajo reúne varios documentos y varias personas en un solo PDF; una declaración jurada trae al declarante y a su cónyuge. Hay que segmentar antes de asociar.
- Q: ¿Qué se hace con las páginas que no aportan identidades del acto? → A: Se descartan enteras. Son las consultas de coincidencias y los separadores en blanco: 100 de las 435 páginas del corpus.
- Q: ¿Se puede confiar en las etiquetas? → A: No del todo. El OCR las corrompe: `D.N.I.` se leyó como `D.N.1,`. El reconocimiento debe tolerar erratas en la etiqueta, no solo variedad de etiquetas.
- Q: ¿Qué se hace con el documento que aparece en una consulta de coincidencias, sin nombre al lado? → A: Se descarta la página entera. Un documento sin titular es justo lo que causaba el cruce de identidades, y ese número aparece con su nombre en la ficha RENIEC y en la biométrica del mismo legajo. Corrige una contradicción entre `spec.md` y el catálogo de fuentes.
- Q: ¿Y el cónyuge, que aparece con nombre pero sin documento? → A: Entra al catálogo como persona sin documento. Su nombre se verifica; no se genera observación sobre su documento, porque no se tiene.
- Q: ¿Cómo se entrega el texto por página sin migrar la caché de F4? → A: El adaptador separa las páginas con un salto de página al unirlas. El texto se sigue guardando como una sola cadena y el núcleo la divide al usarla. El texto guardado antes de este cambio no lleva separador y se trata como un solo bloque: degrada sin romperse.
- Q: ¿Se unen los grupos de un documento manuscrito separados por espacios? → A: No. Unir `0605 12 37` en un solo número es fabricar un dato. Queda como deuda: se prefiere no detectarlo a inventarlo.
- Q: ¿Cómo se presenta una página que no se pudo clasificar? → A: Solo se cuenta y lista por archivo y página si conserva alguna identidad posible; una página de prosa o anexo sin nombres ni documentos se ignora porque no puede aportar a la confrontación.
- Q: ¿Entran las personas jurídicas en esta fase? → A: No. Se reconocen para poder descartarlas sin ruido, pero modelarlas como parte del acto queda fuera.
- Q: ¿Cuándo se unifican dos apariciones de una persona? → A: Solo con el
  mismo documento exacto y nombre completo compatible, admitiendo el orden
  explícito `APELLIDOS, NOMBRES`; o con el mismo nombre completo exacto cuando
  ambos bloques carecen de documento. Los nombres parecidos no se unifican y
  un mismo documento con nombres incompatibles queda separado para revisión:
  se prefiere perder una unificación legítima antes que atribuir un documento
  a la persona equivocada.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - No confundir a las personas entre sí (Priority: P1)

Como notario, quiero que el sistema avise cuando un documento de identidad se asigna a la persona equivocada, para no autorizar una escritura con identidades cruzadas.

**Why this priority**: Es el defecto que originó la fase. Una escritura firmada con el documento de otra persona es un error que el confrontador existe para impedir.

**Independent Test**: Con dos comparecientes ficticios, intercambiar sus documentos en el borrador y comprobar que se generan observaciones.

**Acceptance Scenarios**:

1. **Given** dos comparecientes con su documento en las fuentes, **When** el borrador intercambia los documentos entre ellos, **Then** el sistema lo señala indicando qué persona tiene qué documento según las fuentes.
2. **Given** un compareciente cuyo documento coincide con el de las fuentes, **When** se confronta, **Then** no se genera observación.
3. **Given** un borrador que menciona un documento que no pertenece a ninguna persona de las fuentes, **When** se confronta, **Then** se señala como documento sin titular conocido.

### User Story 2 - No mezclar a quien no es parte del acto (Priority: P1)

Como notario, quiero que el sistema ignore al personal de la notaría y a las coincidencias de listas restrictivas, para que el catálogo contenga solo a los comparecientes.

**Why this priority**: Es la causa concreta de que se asignara un documento ajeno. El personal de la notaría aparece en casi todas las páginas oficiales con un número de ocho dígitos indistinguible de un documento de identidad.

**Independent Test**: Una página ficticia con la disposición de una consulta oficial, con su marca de agua y su pie de consulta, debe aportar solo la identidad del ciudadano.

**Acceptance Scenarios**:

1. **Given** una fuente con bloques de metadatos de consulta, **When** se extrae, **Then** el usuario, la entidad y el número de transacción no aparecen como personas ni como documentos.
2. **Given** una consulta de coincidencias con resultados, **When** se extrae, **Then** ninguna de las entidades listadas entra en el catálogo.
3. **Given** una página en blanco o separador, **When** se procesa, **Then** no aporta nada y no genera error.

### User Story 3 - Ver de dónde salió cada persona (Priority: P2)

Como notario, quiero saber en qué documento y en qué página se encontró cada persona, para verificar una identidad dudosa sin releerlo todo.

**Why this priority**: La confianza en el resultado depende de poder comprobarlo. Es la continuación de la tabla de extracción que ya existe.

**Acceptance Scenarios**:

1. **Given** un catálogo construido, **When** el usuario lo consulta, **Then** cada persona indica de qué archivo y página procede.
2. **Given** una persona que aparece en varios documentos, **When** se muestra, **Then** se ve una sola vez, con todas sus procedencias.

### Edge Cases

- Una persona aparece con el nombre en distinto orden en dos documentos: es la misma persona, no dos.
- Un bloque tiene nombre pero no documento, como el cónyuge de una declaración jurada.
- Un bloque tiene documento pero no nombre legible, porque el OCR falló.
- La etiqueta del documento viene corrompida por el OCR.
- Una página contiene dos personas.
- Un documento de identidad aparece dos veces con distinto número por errores de lectura en páginas distintas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El núcleo DEBE extraer **personas** como unidad, con su nombre y su documento de identidad asociados, en lugar de conjuntos separados por campo.
- **FR-002**: La asociación entre nombre y documento DEBE establecerse dentro de un mismo **bloque** del documento. Nunca entre bloques distintos.
- **FR-003**: El adaptador de extracción DEBE entregar el texto **por página**, no como una sola cadena, para que el núcleo pueda segmentar.
- **FR-004**: El sistema DEBE clasificar cada página por tipo, según `docs/catalogo-fuentes.md`, y descartar entera la que no aporte identidades del acto.
- **FR-005**: El sistema DEBE descartar los bloques de metadatos de consulta: marca de agua, cabecera del notario y pie con usuario, entidad y transacción.
- **FR-006**: El sistema DEBE descartar **entera** la página de consulta de coincidencias, incluidos su documento consultado y las entidades listadas.
- **FR-014**: Una persona con nombre y sin documento DEBE entrar al catálogo. Su nombre se verifica; NO se genera observación sobre su documento.
- **FR-015**: El adaptador DEBE separar las páginas con un salto de página al unir el texto. El texto extraído antes de este cambio se trata como un solo bloque.
- **FR-007**: El reconocimiento de la etiqueta del documento DEBE tolerar erratas de OCR.
- **FR-008**: El sistema DEBE señalar cuando el borrador asigna a una persona un documento que, según las fuentes, es de otra.
- **FR-009**: El sistema DEBE señalar un documento que no pertenezca a ninguna persona conocida.
- **FR-010**: El sistema DEBE conservar, por cada persona, de qué archivo y página procede.
- **FR-011**: El sistema DEBE unificar a la misma persona cuando aparece en varios documentos, sin duplicarla.
- **FR-012**: El sistema NO DEBE modelar personas jurídicas como parte del acto en esta fase; solo reconocerlas para descartarlas sin ruido.
- **FR-013**: La confrontación existente de partidas, montos y párrafos NO DEBE cambiar de comportamiento.

### Requisitos de seguridad y privacidad (Constitución I, II y IV)

- El núcleo sigue siendo puro: recibe texto y estructuras, y devuelve estructuras. No conoce Django, la base de datos ni el sistema de archivos.
- La clasificación por tipo es determinista: sin modelos de lenguaje, sin servicios externos.
- Las personas extraídas se muestran al usuario autorizado, nunca en logs ni en mensajes de error.
- Ningún dato real entra en pruebas, fixtures, commits ni documentación.

### Requisitos de usabilidad (Constitución VIII)

- Una observación de documento cruzado explica qué persona y qué documento, y qué dice la fuente.
- La tabla de extracción muestra personas, no listas de campos sueltos.
- Cuando un bloque se descarta, el usuario puede saber cuántas páginas se descartaron y por qué, sin que eso llene la pantalla.

### Key Entities *(include if feature involves data)*

- **Persona**: nombre normalizado, documento de identidad cuando lo hay, y de qué archivo y página procede. Es la unidad que sustituye a los conjuntos sueltos.
- **Bloque**: fragmento de una fuente que corresponde a un documento y del que puede salir una o más personas. Su tipo decide si aporta o se descarta.

F11 no añade entidades de base de datos ni migraciones: cambia lo que el núcleo
devuelve y cómo lo consume la capa de aplicación.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Con dos comparecientes y sus documentos intercambiados, el sistema genera observación. Hoy no genera ninguna.
- **SC-002**: Sobre una página ficticia con la disposición de una consulta oficial, el catálogo contiene una sola persona: el ciudadano.
- **SC-003**: Una consulta de coincidencias con resultados no aporta ninguna persona.
- **SC-004**: Las páginas en blanco no aportan nada ni provocan error.
- **SC-005**: La confrontación de partidas, montos y párrafos da el mismo resultado que antes de la fase.
- **SC-006**: Ninguna prueba ni fixture usa datos reales.

## Assumptions

- `docs/catalogo-fuentes.md` es la referencia de tipos y etiquetas, y se amplía cuando aparezca una variante nueva.
- El único caso con errores conocidos disponible es un expediente; la medición contra el expediente de referencia sigue siendo el gate de la constitución.
- El documento de identidad manuscrito partido en grupos, el cónyuge sin documento y las partidas registrales de predios quedan fuera y se anotan como deuda.
