# Feature Specification: F4 · Expedientes

**Feature Branch**: `feature/f4-expedientes`

**Created**: 2026-09-20

**Status**: Draft

**Input**: User description: "Un usuario crea un expediente y sube desde su PC las fuentes (documentos del cliente, minuta) y el borrador. El servidor extrae el texto en segundo plano, muestra el avance y borra los archivos al terminar, conservando solo el hash de cada uno."

## Clarifications

### Session 2026-09-20

- Q: ¿Se conserva el texto extraído? → A: Sí, de forma indefinida. Resuelve TODO(RETENCION_TEXTO); la constitución se enmienda a 1.6.0 en esta misma rama. Debe existir un comando de administración que borre el texto de un expediente a solicitud.
- Q: ¿Cómo se evita repetir el OCR del mismo archivo? → A: El texto se guarda indexado por `(hash SHA-256 del archivo, versión del extractor)`. Si ya existe una entrada con esa llave, se reutiliza y no se ejecuta el OCR.
- Q: ¿De dónde sale el código del expediente? → A: Lo digita el usuario al crear el expediente. Es único en todo el sistema; el sistema no lo genera ni lo autocompleta.
- Q: ¿Qué roles de documento existen? → A: Dos, `FUENTE` y `BORRADOR`. La minuta y los documentos del cliente son ambos `FUENTE`, porque el núcleo (`nucleo.verificar.catalogo`) ya los trata como un único conjunto de fuentes frente a un destino.
- Q: ¿Qué pasa al suprimir el texto de un expediente si ese texto es compartido con otro? → A: Se vacía para todos. El dato personal desaparece de verdad; los demás expedientes conservan hash y fechas, y si vuelven a necesitar el texto el archivo se reprocesa.
- Q: ¿F4 incluye cerrar el expediente? → A: No, y el estado `CERRADO` se retira del modelo. La notaría no sabe cuándo se cierra un expediente: puede pasar un mes o un año. El expediente no tiene estado propio almacenado; se deriva del estado de sus documentos.
- Q: ¿F4 incluye eliminar un documento del expediente? → A: Sí. El usuario puede quitar, con confirmación, un archivo que subió por error.
- Q: ¿Cuál es el tamaño máximo de archivo? → A: 25 MB, configurable en `settings`. Es un límite técnico, no una regla de la notaría.
- Q: ¿Cuándo se considera caído un documento en `PROCESANDO`? → A: A los 15 minutos sin terminar vuelve a `PENDIENTE`. Configurable.
- Q: Si la extracción falla, ¿se puede reintentar? → A: No. El archivo ya se borró al fallar, así que no hay nada que reprocesar: un reintento volvería a fallar siempre. La recuperación es eliminar el documento y volver a subirlo. No se conserva el archivo para habilitar un reintento, porque dejar datos personales en disco por un botón de valor marginal contradice el principio de minimización.
- Q: ¿Cómo se ejecuta la extracción en segundo plano? → A: La cola es la propia base de datos (`Documento.estado = PENDIENTE`) y la consume un comando de administración ejecutado como tarea programada. No se añaden Celery, Redis ni ningún servicio nuevo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Crear un expediente y subir sus documentos (Priority: P1)

Como usuario de la notaría, quiero crear un expediente con su código y subir desde mi PC la minuta, los documentos del cliente y el borrador, para que el sistema pueda confrontarlos después.

**Why this priority**: Sin expediente ni documentos cargados no existe nada que confrontar; es la entrada de todo el flujo.

**Independent Test**: Crear un expediente ficticio, subirle un archivo como fuente y otro como borrador, y comprobar que ambos quedan registrados y encolados.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado, **When** crea un expediente con un código no usado, **Then** el expediente queda registrado a su nombre y sin documentos.
2. **Given** un usuario autenticado, **When** intenta crear un expediente con un código ya existente, **Then** se rechaza con un mensaje claro y no se crea nada.
3. **Given** un expediente abierto, **When** el usuario sube un archivo de un formato admitido indicando su rol (`FUENTE` o `BORRADOR`), **Then** el documento queda registrado con su nombre original, su hash y estado `PENDIENTE`.
4. **Given** un expediente abierto, **When** el usuario sube un archivo de formato no admitido o que excede el tamaño máximo, **Then** se rechaza antes de guardarlo y se explica el motivo.
5. **Given** un expediente ajeno, **When** un usuario que no es su creador ni Administrador intenta abrirlo o subirle documentos, **Then** se deniega el acceso.

### User Story 2 - Ver el avance de la extracción (Priority: P1)

Como usuario, quiero ver en pantalla en qué estado va la extracción de cada documento, para saber cuándo el expediente está listo para confrontar.

**Why this priority**: La extracción tarda; sin retroalimentación el usuario no sabe si el sistema trabaja o se colgó (heurística 1 de Nielsen).

**Independent Test**: Subir un documento y observar la transición `PENDIENTE` → `PROCESANDO` → `LISTO` sin recargar la página a mano.

**Acceptance Scenarios**:

1. **Given** un documento recién subido, **When** el usuario permanece en la pantalla del expediente, **Then** el estado se actualiza solo hasta llegar a `LISTO` o `ERROR`.
2. **Given** todos los documentos de un expediente en `LISTO`, **When** el usuario mira el expediente, **Then** el expediente aparece como listo para confrontar.
3. **Given** un documento que falló, **When** el usuario mira su estado, **Then** ve `ERROR` con un motivo entendible, sin datos personales ni trazas internas, y la pantalla le indica que elimine el documento y vuelva a subirlo.
4. **Given** una extracción en curso, **When** el usuario recarga o vuelve más tarde, **Then** el estado mostrado es el real, porque vive en la base de datos y no en la sesión.

### User Story 3 - Reutilizar el texto ya extraído (Priority: P2)

Como usuario, quiero que un archivo que ya pasó por el sistema no vuelva a pasar por el OCR, para no esperar de nuevo.

**Why this priority**: El OCR es la operación más cara del flujo; el mismo documento de identidad se repite entre expedientes del mismo cliente.

**Independent Test**: Subir el mismo archivo ficticio a dos expedientes distintos y comprobar que el segundo queda `LISTO` sin ejecutar el OCR.

**Acceptance Scenarios**:

1. **Given** un archivo cuyo hash y versión de extractor ya tienen texto guardado, **When** se sube de nuevo, **Then** el documento queda `LISTO` reutilizando ese texto, sin ejecutar la extracción.
2. **Given** un archivo ya procesado, **When** cambia la versión del extractor, **Then** la entrada anterior deja de coincidir y el archivo se vuelve a extraer.
3. **Given** un texto reutilizado, **When** se registra el uso, **Then** queda constancia de la última vez que se usó.

### User Story 4 - Quitar un documento subido por error (Priority: P2)

Como usuario, quiero eliminar de un expediente un archivo que subí por equivocación, para que no se confronte contra él.

**Why this priority**: Subir el archivo equivocado es un error común y sin marcha atrás el expediente queda inservible.

**Independent Test**: Subir dos documentos ficticios, eliminar uno y comprobar que el otro y el expediente siguen intactos.

**Acceptance Scenarios**:

1. **Given** un documento de un expediente propio, **When** el usuario pide eliminarlo, **Then** se le pide confirmación antes de hacer nada.
2. **Given** la confirmación dada, **When** se elimina el documento, **Then** desaparece del expediente junto con su archivo temporal si lo tuviera, y el texto compartido en `TextoExtraido` permanece para otros documentos que lo usen.
3. **Given** un documento de un expediente ajeno, **When** alguien que no es su creador ni Administrador intenta eliminarlo, **Then** se deniega.

### User Story 5 - Borrar a solicitud el texto de un expediente (Priority: P2)

Como administrador del servidor, quiero poder borrar el texto extraído de un expediente concreto, para atender una solicitud de supresión.

**Why this priority**: Es la condición bajo la cual la constitución 1.6.0 autoriza la retención indefinida.

**Independent Test**: Ejecutar el comando sobre un expediente ficticio y comprobar que el texto desaparece y el resto del registro permanece.

**Acceptance Scenarios**:

1. **Given** un expediente con documentos procesados, **When** se ejecuta el comando de supresión sobre él, **Then** el texto queda borrado y el hash, las fechas y el autor permanecen intactos.
2. **Given** un texto compartido con otro expediente, **When** se ejecuta la supresión, **Then** el texto se vacía también para ese otro expediente y el comando informa cuántos expedientes quedaron afectados, sin nombrar su contenido. Los hashes, fechas y autores de todos ellos permanecen intactos.

### Edge Cases

- Dos usuarios suben el mismo archivo a la vez: la llave `(hash, versión)` es única y la segunda escritura reutiliza la primera sin fallar.
- El worker muere a mitad de un documento: como el proceso murió, su archivo temporal sigue en disco, así que el documento vuelve a `PENDIENTE` y se extrae de nuevo. No queda atrapado en `PROCESANDO` para siempre. Esto es distinto de un fallo de extracción, donde el archivo sí se borró y no hay reintento.
- Archivo vacío, corrupto o sin capa de texto ni contenido legible: estado `ERROR` con motivo, no una excepción sin manejar.
- Archivo temporal huérfano porque el proceso se interrumpió: la tarea diaria lo elimina pasadas 24 h.
- El mismo archivo subido dos veces al mismo expediente: se avisa al usuario en lugar de duplicar en silencio.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE permitir crear un expediente con un código digitado por el usuario, único en todo el sistema.
- **FR-002**: El sistema DEBE permitir subir archivos a un expediente indicando su rol: `FUENTE` o `BORRADOR`.
- **FR-003**: El sistema DEBE calcular el hash SHA-256 de cada archivo subido y registrarlo junto al nombre original y el tamaño.
- **FR-004**: El sistema DEBE guardar el archivo subido únicamente en un directorio temporal, y borrarlo al terminar el procesamiento, tanto si terminó bien como si falló.
- **FR-005**: El sistema DEBE extraer el texto fuera del ciclo de la petición, tomando los documentos en estado `PENDIENTE` desde la base de datos.
- **FR-006**: El sistema DEBE guardar el texto extraído indexado por `(hash del archivo, versión del extractor)` y reutilizarlo cuando esa llave ya exista.
- **FR-007**: El sistema DEBE mostrar el estado de cada documento y actualizarlo en pantalla sin intervención del usuario.
- **FR-008**: El sistema DEBE indicar, ante un documento en `ERROR`, que la forma de recuperarse es eliminarlo y volver a subirlo. NO existe una acción de reintento: el archivo se borró al fallar y no hay nada que reprocesar.
- **FR-009**: El sistema DEBE ofrecer un comando de administración que borre el texto extraído asociado a un expediente.
- **FR-010**: El sistema DEBE ofrecer una tarea que elimine los archivos temporales huérfanos con más de 24 horas.
- **FR-011**: El sistema DEBE rechazar formatos no admitidos y archivos que superen el tamaño máximo configurado, antes de almacenarlos. El máximo por defecto es 25 MB.
- **FR-012**: El sistema NO DEBE guardar el archivo original ni su contenido binario más allá del procesamiento.
- **FR-013**: El sistema DEBE permitir eliminar un documento de un expediente, previa confirmación, sin afectar al texto que otros documentos compartan.
- **FR-014**: El sistema DEBE devolver a `PENDIENTE` un documento que lleve más de 15 minutos en `PROCESANDO`, para que la caída del worker no lo deje atrapado. El umbral es configurable.
- **FR-015**: La supresión del texto de un expediente DEBE vaciar también las entradas compartidas con otros expedientes, e informar cuántos quedaron afectados.

### Requisitos de seguridad y privacidad (Constitución IV y VI)

- Solo usuarios autenticados con rol `Usuario` o `Administrador` acceden a expedientes.
- Un usuario ve y modifica los expedientes que creó; un Administrador ve todos.
- La validación de formato, tamaño y rol se hace en el servidor; no basta el control del navegador.
- El nombre del archivo subido se trata como dato no confiable: no se usa para construir rutas.
- El directorio temporal está fuera de cualquier ruta servida por el servidor web.
- Ni el texto extraído, ni el nombre del archivo, ni fragmentos del documento aparecen en logs ni en mensajes de error.
- El texto extraído se conserva indefinidamente según la constitución 1.6.0, y se suprime a solicitud con el comando de FR-009.

### Requisitos de usabilidad y accesibilidad (Constitución VIII)

- Estado visible del sistema: cada documento muestra su estado y el expediente resume cuántos faltan.
- Prevención de errores: los formatos admitidos y el tamaño máximo se indican antes de subir.
- Recuperación: un error de extracción explica qué pasó y dice qué hacer: eliminar el documento y subirlo de nuevo.
- Estado vacío comprensible en un expediente recién creado, sin aparentar un fallo.
- Confirmación explícita antes de eliminar un documento de un expediente.

### Key Entities *(include if feature involves data)*

- **Expediente**: código único digitado, estado, quién lo creó y cuándo.
- **Documento**: un archivo subido a un expediente; rol, nombre original, hash, tamaño, estado de extracción, motivo del error y ruta temporal mientras se procesa.
- **TextoExtraido**: el texto de un archivo, identificado por `(hash del archivo, versión del extractor)`; se comparte entre los documentos que apunten al mismo archivo.

El detalle de campos y restricciones está en `data-model.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario crea un expediente y sube sus documentos sin salir de una sola pantalla.
- **SC-002**: Subir de nuevo un archivo ya procesado deja el documento en `LISTO` sin ejecutar el OCR, de forma comprobable en una prueba automatizada.
- **SC-003**: Al terminar el procesamiento de un documento no queda ningún archivo en el directorio temporal, comprobado en una prueba automatizada.
- **SC-004**: Ninguna prueba ni fixture usa datos reales; todo el material es ficticio.
- **SC-005**: El estado mostrado en pantalla coincide con el de la base de datos tras recargar.

## Assumptions

- El núcleo (`nucleo/`) y el adaptador de extracción (`adaptadores/extraccion.py`) ya existen desde F3 y no cambian su comportamiento en esta fase.
- F4 no ejecuta las capas de regla, léxico ni ortografía: eso es F5. Aquí solo se obtiene y conserva el texto.
- El worker corre en el mismo servidor que la aplicación, en la LAN de la notaría.
- El tipo de acto del expediente se define en F9; en F4 no existe.
- Consecuencia para F5: un documento puede quedar en `LISTO` con el texto
  vacío si alguien ejecutó la supresión. F5 DEBE tratar ese caso como "sin
  texto disponible" y pedir que se vuelva a subir el archivo, en lugar de
  confrontar contra una cadena vacía y reportar que falta todo.
- El expediente no se cierra: la notaría no sabe cuándo termina un trámite, puede pasar un mes o un año. No existe el estado `CERRADO`.
