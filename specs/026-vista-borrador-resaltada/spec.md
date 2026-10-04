# Feature Specification: F32 · Vista del borrador con errores resaltados

**Feature Branch**: `026-vista-borrador-resaltada`

**Created**: 2026-10-02

**Status**: Tramo A (US1 `.docx` y US3) implementado y verificado localmente el 2026-10-02 con datos ficticios. US2 (escaneados y demás formatos) bloqueado hasta aprobar la constitución 1.8.0. Integración por PR, CI y SonarQube pendiente.

**Input**: User description: "Al ejecutar la confrontación, el digitador ve en pantalla la imagen real de cada página del borrador (.docx renderizado a página, PDF con texto o PDF/imagen escaneada leída por OCR) y sobre ella cada observación resaltada en su posición exacta, sin imprimir el reporte. Color por severidad: alta en rojo, media en amarillo, baja (incluida la capa lingüística) en un tono neutro. Al elegir una observación en la lista, la vista salta a la página y al recuadro; al hacer clic en un recuadro, se selecciona la observación. Si una observación no se puede ubicar en la página, se indica claramente. Requisito previo: enmienda de la constitución (principio IV, hoy 1.7.0) para conservar el borrador escaneado además del .docx."

## Requisito previo: enmienda constitucional

La constitución 1.7.0 (principio IV) solo permite conservar el borrador `.docx`. Los demás archivos subidos son temporales y se borran al terminar la extracción. Para ver la página real de un borrador que llegó como PDF o imagen escaneada, hay que conservar ese archivo. Eso exige enmendar la constitución (versión MINOR, 1.8.0) por Pull Request y con la aprobación de la notaría (Ley 29733).

- Mientras la enmienda no esté aprobada, la vista de página solo se ofrece para borradores `.docx`. Para los demás formatos se muestra el aviso de FR-011 y la lista de observaciones sigue funcionando como hoy.
- Los documentos del cliente y la minuta **siguen siendo temporales**. Esta funcionalidad no los muestra ni los conserva.
- Formatos que se conservan tras la enmienda (decisión del 2026-10-02): **todo formato de borrador**, es decir, `.docx`, `.doc`, `.rtf`, `.odt`, PDF con texto, PDF escaneado e imágenes. Se aplican las mismas condiciones que al `.docx` de F21.

## Clarifications

### Session 2026-10-02

- Q: ¿Qué borradores, además del `.docx`, se conservan tras la enmienda? → A: todos los formatos de borrador (PDF e imágenes escaneadas, y también `.doc`, `.rtf`, `.odt` y PDF con texto).
- Q: Si el OCR leyó el error, ¿no debería poder ubicarse en la página? → A: sí. El texto OCR del borrador se arma con los segmentos que el OCR lee en la página, y cada segmento guarda su posición. Todo valor observado que aparece en ese texto tiene, por tanto, un sitio en la imagen. "No ubicada" queda solo para las observaciones de algo que **falta** en el borrador, o cuyo valor no aparece escrito en él.
- Q: ¿Basta con guardar el reporte en la base de datos? → A: las observaciones de cada corrida ya se guardan. Lo que exige la enmienda es conservar el archivo del borrador, que hace falta para dibujar la página. Que se guarde en la base de datos o en disco local se decide en el plan; la obligación legal es la misma.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver el borrador `.docx` con los errores marcados en su página (Priority: P1)

El digitador termina la confrontación de un expediente cuyo borrador es `.docx`. En la pantalla de resultado aparece, junto a la lista de observaciones, la página del borrador tal como se imprime. Cada observación ubicada se ve sobre el texto con un recuadro de color: rojo para severidad alta, amarillo para media y neutro para baja. El digitador corrige en su Word sin imprimir el reporte.

**Why this priority**: es el caso más común y no depende de la enmienda constitucional. Por sí sola ya elimina la impresión del reporte para ubicar errores.

**Independent Test**: confrontar un expediente ficticio con un borrador `.docx` que tenga un DNI incorrecto (alta), una discrepancia de severidad media y una falta ortográfica (baja). Comprobar que las tres aparecen marcadas en su página y con su color.

**Acceptance Scenarios**:

1. **Given** una confrontación terminada con un borrador `.docx` y observaciones ubicadas, **When** el digitador abre el resultado, **Then** ve la primera página del borrador con los recuadros de esa página coloreados por severidad.
2. **Given** una observación de severidad alta en la página 3, **When** el digitador la elige en la lista, **Then** la vista muestra la página 3, centra el recuadro y lo destaca como seleccionado.
3. **Given** un recuadro visible en la página, **When** el digitador hace clic sobre él, **Then** se selecciona en la lista la observación correspondiente y se muestra su detalle (hallado, esperado, procedencia).
4. **Given** el filtro de severidad o de capa activo en la lista, **When** el digitador lo cambia, **Then** la página muestra solo los recuadros de las observaciones visibles en la lista.

---

### User Story 2 - Ver el borrador escaneado con los errores marcados (Priority: P2)

El borrador llegó como PDF escaneado o como imagen y se leyó por OCR. Tras la enmienda, el digitador ve la imagen escaneada de cada página con los recuadros sobre las palabras que el OCR leyó en la posición del error.

**Why this priority**: es lo que pidió el usuario explícitamente ("por más que sea del OCR"), pero depende de la enmienda constitucional.

**Independent Test**: confrontar un expediente ficticio con un borrador PDF escaneado que contenga un monto distinto del de la minuta. Comprobar que el recuadro cae sobre el monto en la imagen.

**Acceptance Scenarios**:

1. **Given** la enmienda aprobada y un borrador escaneado confrontado, **When** el digitador abre el resultado, **Then** ve la imagen de cada página con los recuadros sobre las palabras observadas.
2. **Given** una observación cuyo texto el OCR repartió en varias líneas, **When** se muestra, **Then** cada tramo lleva su propio recuadro y todos responden como una sola observación.
3. **Given** una página con lectura dudosa (aviso de F31), **When** se muestra, **Then** el aviso de calidad aparece junto a la página y los recuadros se ven igual.

---

### User Story 3 - Saber qué observaciones no están en la página (Priority: P3)

Toda observación cuyo valor está escrito en el borrador se marca en la página, también si vino del OCR. Quedan sin marcar solo las observaciones de algo que **falta** en el borrador; por ejemplo, un párrafo de la minuta que no se trasladó. El digitador las ve indicadas en la observación y en un contador, para que no las pase por alto.

**Why this priority**: evita que el digitador crea que revisó todo solo porque recorrió las páginas.

**Independent Test**: confrontar un expediente ficticio con un párrafo de la minuta ausente del borrador y comprobar que la observación indica "No ubicada en el borrador" y cuenta en el resumen de no ubicadas.

**Acceptance Scenarios**:

1. **Given** una observación sin ubicación, **When** el digitador la elige, **Then** la vista no cambia de página y la observación muestra "No ubicada en el borrador".
2. **Given** observaciones sin ubicación en el resultado, **When** se abre la vista, **Then** un contador visible indica cuántas no están marcadas en las páginas.

---

### Edge Cases

- Un mismo valor erróneo aparece varias veces en el borrador: se marcan todas las apariciones y se asocian a la misma observación.
- Dos observaciones se solapan sobre el mismo texto: se ven las dos, prima el color de la mayor severidad y el clic ofrece elegir entre ellas.
- En un borrador escaneado, un segmento del OCR suele abarcar varias palabras. La posición del segmento es exacta; la del valor dentro del segmento se estima por la proporción de caracteres. Por eso el recuadro puede sobrar o faltar unos milímetros a los lados, pero siempre cae dentro de la línea correcta.
- En un `.docx` o un PDF con texto, la página dibujada puede cortar líneas o palabras de otro modo que el texto extraído (saltos de línea, guiones de corte, tablas): la observación se ubica sobre las palabras equivalentes de la página. Si aun así no se encuentra, cuenta como no ubicada (FR-007) y se indica el motivo.
- Corridas anteriores a esta funcionalidad, o borradores cuyo archivo ya se borró: se muestra el aviso de FR-011 y la lista de observaciones sigue disponible.
- El documento se suprimió a solicitud (Ley 29733): la vista de página deja de estar disponible.
- Borrador con muchas páginas (por ejemplo, 60): las páginas se cargan conforme se navega, sin esperar a todo el documento.
- El archivo conservado no coincide con su SHA-256 registrado: no se muestra la página y se avisa que el original no se pudo verificar.
- Página girada o inclinada en el escaneo: los recuadros siguen la orientación con la que se muestra la imagen.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La pantalla de resultado de la confrontación MUST mostrar las páginas del borrador como se imprimen (imagen de página), junto a la lista de observaciones existente.
- **FR-002**: Cada observación ubicada MUST verse como un recuadro sobre el texto observado, con color por severidad: **alta en rojo, media en amarillo, baja en tono neutro**. La capa lingüística se trata como baja. Además del color, cada recuadro MUST llevar una marca no cromática (ícono o patrón) que distinga la severidad.
- **FR-003**: Elegir una observación en la lista MUST llevar la vista a su página, centrar su recuadro y destacarlo como seleccionado. Si tiene varias apariciones, se puede pasar de una a otra.
- **FR-004**: Hacer clic (o pulsar Enter con el foco) en un recuadro MUST seleccionar su observación en la lista y mostrar su detalle.
- **FR-005**: Los filtros de severidad y de capa existentes MUST aplicarse también a los recuadros visibles.
- **FR-006**: La ubicación de cada observación MUST ser determinista: la misma corrida produce siempre los mismos recuadros en las mismas posiciones.
- **FR-007**: Toda observación cuyo valor aparece en el texto del borrador MUST marcarse en la página, también cuando el texto vino del OCR. Solo las observaciones de algo ausente del borrador, o cuyo valor no está escrito en él, MUST indicarse como "No ubicada en el borrador" y contarse en un indicador visible. Nunca se dibuja un recuadro en una línea distinta de la que contiene el valor.
- **FR-008**: Para borradores `.docx`, la página MUST generarse a partir del original conservado, tras verificar su SHA-256 como exige F21.
- **FR-009**: Para borradores escaneados (solo tras la enmienda), la posición MUST salir de los segmentos que el OCR ya registra por página (F31, FR-004), con su texto y su posición, sin una lectura OCR adicional. Dentro de un segmento, la posición del valor se estima por la proporción de caracteres.
- **FR-010**: Las páginas MUST cargarse bajo demanda; la lista de observaciones se puede usar mientras cargan, con un estado visible ("Preparando la vista del borrador…", "Cargando página 4 de 12"). La primera vez, la vista la prepara el proceso en segundo plano y la pantalla se actualiza sola cuando está lista.
- **FR-011**: Si la vista de página no está disponible (formato no conservado, corrida antigua, archivo borrado o suprimido, verificación fallida), la pantalla MUST mostrarlo con un mensaje claro que diga por qué y qué hacer, y la lista de observaciones MUST seguir funcionando como hoy.
- **FR-012**: El reporte (Word, PDF, Excel) no cambia en esta fase.

### Requisitos de seguridad

- **Quién**: solo los usuarios con permiso sobre el expediente (roles Administrador y Usuario, como en la confrontación). Toda página se sirve por una vista con login y permiso; nunca como estático público.
- **Qué datos toca**: el borrador conservado y, tras la enmienda, el borrador escaneado conservado. Mismas condiciones que el `.docx` de F21: almacenamiento local fuera del repositorio y de `static/`, permisos restrictivos, ruta nunca mostrada ni registrada.
- **Imágenes de página**: se generan para mostrarlas y no se guardan como archivos nuevos. Si se guardaran temporalmente, se incluirían en la supresión y en la limpieza de huérfanos.
- **Supresión**: la supresión a solicitud borra también el borrador escaneado conservado. Después de ella, la vista de página deja de estar disponible.
- **Logs y errores**: sin rutas, nombres, DNI ni contenido de páginas.
- **Auditoría**: abrir la vista de página no crea un registro nuevo, igual que la consulta del resultado, que hoy tampoco se registra. Lo auditado sigue siendo la corrida: quién confrontó qué, cuándo y con qué hash.

### Requisitos de UX (principio VIII)

- Estado visible al cargar cada página; la vista no bloquea la lista.
- Textos en vocabulario de la notaría ("borrador", "página", "no ubicada"), sin términos técnicos.
- Navegación con teclado: ↑/↓ en la lista (ya existe), Avance/Retroceso de página para cambiar de página y foco visible en el recuadro seleccionado.
- Contraste suficiente de los tres colores sobre papel blanco y sobre escaneos grises; la severidad no depende solo del color (FR-002).
- Zoom de página (ajustar a ancho y ampliar) para leer escaneos pequeños.
- Leyenda breve de colores junto a la página.

### Key Entities

- **Borrador conservado**: el archivo original del borrador (`.docx` y, tras la enmienda, cualquier formato de borrador), con su SHA-256, ligado al documento del expediente.
- **Página del borrador**: número, tamaño y la imagen que se muestra al usuario; se genera desde el borrador conservado.
- **Ubicación en página**: para una observación, la lista de recuadros (página y posición relativa) donde aparece su texto, o la marca "no ubicada".

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En el conjunto de expedientes ficticios de prueba, al menos el 95 % de las observaciones que hoy tienen línea en el borrador aparecen marcadas sobre la página correcta y sobre las palabras correctas.
- **SC-002**: Ninguna observación aparece marcada sobre un texto que no le corresponde (0 recuadros falsos en el conjunto de prueba).
- **SC-003**: Desde la lista, el digitador llega al error en su página con un solo clic o tecla, y la página se muestra en menos de 2 segundos en la red de la notaría.
- **SC-004**: Dos aperturas de la misma corrida producen recuadros idénticos.
- **SC-005**: El digitador revisa un expediente completo sin imprimir ni descargar el reporte (verificado en la revisión con la notaría).

## Assumptions

- Los colores por severidad los eligió el usuario el 2026-10-02: alta roja, media amarilla, baja neutra.
- La severidad que se usa es la que ya tiene cada observación; esta fase no cambia severidades ni reglas.
- El `.docx` se convierte a páginas con LibreOffice, que ya está en el despliegue. La paginación puede diferir en detalles mínimos de la de Word del digitador; se acepta, porque la ubicación se hace sobre el texto de la página mostrada.
- Esta fase solo muestra el borrador; los documentos del cliente y la minuta no se muestran.
- Las corridas anteriores no se reconstruyen: necesitan volver a confrontar si el borrador ya no está conservado.
- No se añaden dependencias nuevas: PyMuPDF, LibreOffice y las posiciones OCR de F31 ya existen.
