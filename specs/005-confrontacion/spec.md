# Feature Specification: F5 · Confrontación

**Feature Branch**: `feature/f5-confrontacion`

**Created**: 2026-09-20

**Status**: Draft

**Input**: User description: "Con el texto extraído, el sistema ejecuta las capas de regla, léxico y ortografía y muestra las observaciones agrupadas por capa, con la ubicación en el borrador y el valor esperado según la fuente."

**Nota sobre el alcance**: el texto anterior es el prompt original del roadmap y
se conserva tal cual. La capa de **léxico queda fuera de F5** y pasa a la fase
F10, según la aclaración de más abajo y FR-012: necesita un corpus de escrituras
firmadas y todavía no está decidido de dónde sale.

## Clarifications

### Session 2026-09-20

- Q: ¿Entra la capa de léxico en F5? → A: No. El léxico necesita un corpus de escrituras ya firmadas y todavía no está decidido de dónde sale. F5 entrega **regla** y **ortografía**, que ya están listas para conectarse. La similitud entre palabras la resuelve `rapidfuzz`, que es lo que ambas capas ya usan por dentro: la de regla para proponer «debe decir X» y la de ortografía para sugerir la palabra correcta.
- Q: ¿Se guardan las observaciones? → A: No en F5. La confrontación se calcula cuando el usuario la pide y se muestra. No hay OCR de por medio, así que rehacerla cuesta segundos. La persistencia es la decisión de F6 (historial y auditoría).
- Q: ¿Qué umbral se usa? → A: 88, el mismo valor ya medido que usa la aplicación actual (`UMBRAL_PARRAFO`). No se inventa un valor nuevo ni se expone al usuario en F5.
- Q: ¿Cómo se distingue la minuta del resto de fuentes, si F4 las guarda todas con rol `FUENTE`? → A (sustituida el 2026-09-20): `CLIENTE`, `MINUTA` y `BORRADOR` son roles reales. `CLIENTE` y `MINUTA` forman el catálogo de fuentes; `revisar_parrafos()` recibe únicamente textos con rol `MINUTA`. Se sustituye la heurística por extensión: un PDF del cliente ya no se interpreta como minuta.
- Q: ¿Qué documentos son obligatorios para confrontar? → A (2026-09-20): al menos un `CLIENTE`, una `MINUTA` y un `BORRADOR`. Si falta uno, la acción no está disponible y el mensaje nombra el rol faltante.
- Q: ¿Qué se hace con un documento cuyo texto fue suprimido? → A: No se confronta. Se avisa de que su texto ya no está disponible y que hay que volver a subir el archivo.
- Q: ¿Qué ocurre mientras termina la extracción? → A: El sondeo del detalle también actualiza la disponibilidad de cada borrador, de modo que la acción aparece sin recargar la página cuando todos los textos están listos.
- Q: ¿Cómo se presenta una observación que el núcleo informa desde ambos lados? → A: Una `FALTA` cuyo valor esperado ya aparece como esperado de una discrepancia del mismo campo se omite en la aplicación; las demás `FALTA` permanecen como hallazgos independientes.
- Q: ¿Cómo puede verificar el usuario si una observación falta por un OCR incompleto? → A: La pantalla de confrontación incluye una sección plegada por defecto con el catálogo agregado, el aporte por fuente y el número de caracteres extraídos; no muestra el texto completo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confrontar el borrador contra las fuentes (Priority: P1)

Como usuario de la notaría, quiero pedir la confrontación de un expediente y ver las diferencias entre el borrador y las fuentes, para corregir la escritura antes de firmarla.

**Why this priority**: Es el objetivo del sistema entero; todo lo anterior existe para llegar aquí.

**Independent Test**: Con un expediente ficticio que tenga al menos un documento `CLIENTE`, una `MINUTA` y un `BORRADOR` ya extraídos, pedir la confrontación y comprobar que aparecen las diferencias sembradas a propósito.

**Acceptance Scenarios**:

1. **Given** un expediente con al menos un `CLIENTE`, una `MINUTA` y un `BORRADOR` en estado `LISTO`, **When** el usuario pide la confrontación, **Then** ve las observaciones encontradas, agrupadas por capa.
2. **Given** un expediente al que le falta `CLIENTE`, `MINUTA` o `BORRADOR`, **When** el usuario lo mira, **Then** la acción de confrontar no está disponible y se explica qué falta.
3. **Given** un expediente con algún documento que no terminó de procesarse, **When** el usuario lo mira, **Then** se le indica que espere a que termine la extracción.
4. **Given** los documentos pasan de pendientes a `LISTO`, **When** el sondeo recibe el nuevo estado, **Then** la acción de cada borrador disponible aparece sin recargar la página.
5. **Given** un expediente ajeno, **When** alguien que no es su creador ni Administrador intenta confrontarlo, **Then** se deniega.
6. **Given** una confrontación sin ninguna diferencia, **When** termina, **Then** se informa claramente de que no se encontraron observaciones, sin parecer un error ni una pantalla rota.

### User Story 2 - Entender cada observación (Priority: P1)

Como usuario, quiero que cada observación me diga qué campo falla, qué dice el borrador, qué debería decir y dónde está, para poder corregirlo sin buscar a ciegas.

**Why this priority**: Una lista de diferencias sin ubicación obliga a releer la escritura entera, que es justo el trabajo que el sistema viene a ahorrar.

**Independent Test**: Sembrar un DNI alterado en un borrador ficticio y comprobar que la observación indica el valor hallado, el esperado y la línea del borrador.

**Acceptance Scenarios**:

1. **Given** una observación de la capa de regla, **When** el usuario la lee, **Then** ve el campo (`NOMBRE`, `DNI`, `PARTIDA`, `MONTO`), el valor que aparece en el borrador y el valor esperado según las fuentes, o el aviso de que no coincide con ninguna.
2. **Given** un dato que está en las fuentes y no aparece en el borrador, **When** el usuario lee las observaciones, **Then** aparece señalado como faltante.
3. **Given** una `FALTA` que duplica el valor esperado de una discrepancia del mismo campo, **When** el usuario lee las observaciones, **Then** solo ve una fila para ese hallazgo; las faltas sin discrepancia equivalente sí aparecen.
4. **Given** una observación cuyo valor aparece en el borrador, **When** el usuario la lee, **Then** ve el número de línea y un fragmento del borrador alrededor del hallazgo.
5. **Given** una observación de la capa de ortografía, **When** el usuario la lee, **Then** ve la palabra, el motivo y la sugerencia cuando la hay.
6. **Given** un párrafo de la minuta que no aparece en el borrador o aparece alterado, **When** el usuario lee las observaciones, **Then** aparece señalado con su porcentaje de coincidencia.

### User Story 3 - Detectar un borrador que no es de este expediente (Priority: P2)

Como usuario, quiero que el sistema me avise si el borrador no parece corresponder a las fuentes del expediente, para no perder tiempo revisando cientos de diferencias sin sentido.

**Why this priority**: Es un error humano frecuente y, sin el aviso, el informe resultante es inservible y desprestigia al sistema.

**Independent Test**: Confrontar un borrador ficticio sin ningún dato en común con las fuentes y comprobar que se avisa en lugar de listar todo.

**Acceptance Scenarios**:

1. **Given** un borrador que no comparte datos con las fuentes y trae identidades propias, **When** se confronta, **Then** se muestra el aviso y NO se lista la comparación campo por campo.
2. **Given** el aviso mostrado, **When** el usuario lo lee, **Then** entiende que debe revisar si el borrador y las fuentes son del mismo expediente.

### User Story 4 - Texto suprimido (Priority: P3)

Como usuario, quiero entender por qué un documento no se puede confrontar cuando su texto fue suprimido, para saber que debo volver a subirlo.

**Why this priority**: Es la consecuencia directa del comando de supresión de F4; sin este aviso el sistema confrontaría contra un texto vacío y reportaría que falta todo.

**Acceptance Scenarios**:

1. **Given** un documento en `LISTO` cuyo texto fue suprimido, **When** el usuario pide la confrontación, **Then** se le indica que ese documento no tiene texto disponible y que vuelva a subirlo, y no se confronta contra una cadena vacía.

### Edge Cases

- Un expediente con varios borradores: cada uno se confronta por separado y sus resultados se presentan por separado.
- Cada zona acepta varios archivos en un envío; la validación es individual y los archivos válidos se registran aunque otro falle.
- Un borrador sin ninguna línea larga: la comparación de párrafos no produce observaciones y eso no es un error.
- Un valor que aparece muchas veces en el borrador: se señala sin repetir la misma observación una vez por aparición.
- Un documento `CLIENTE` que es imagen y otro que es PDF: ambos alimentan el catálogo, pero ninguno se usa para comparar párrafos; solo los documentos `MINUTA` se usan para ello.
- La confrontación tarda: la pantalla indica que está trabajando y no parece colgada.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE permitir pedir la confrontación de un expediente que tenga al menos un `CLIENTE`, una `MINUTA` y un `BORRADOR`, todos con texto disponible.
- **FR-002**: El sistema DEBE ejecutar la capa de **regla** (`nucleo.verificar`) comparando el borrador contra el catálogo construido con todas las fuentes.
- **FR-003**: El sistema DEBE ejecutar la comparación de párrafos entre los documentos con rol `MINUTA` y el borrador. El rol, y no la extensión, identifica las minutas.
- **FR-004**: El sistema DEBE ejecutar la capa de **ortografía** (`nucleo.ortografia`) sobre el borrador, dando por buenos los nombres propios que la capa de regla ya validó contra las fuentes.
- **FR-005**: El sistema DEBE ejecutar primero el diagnóstico de correspondencia y, si indica que el borrador no pertenece al expediente, mostrar el aviso y NO listar la comparación campo por campo.
- **FR-006**: El sistema DEBE mostrar las observaciones agrupadas por capa, con el recuento de cada grupo.
- **FR-007**: El sistema DEBE indicar, para cada observación cuyo valor aparezca en el borrador, el número de línea y un fragmento del borrador alrededor del hallazgo.
- **FR-008**: El sistema DEBE usar el umbral ya medido (88) y NO exponerlo al usuario en esta fase.
- **FR-009**: El sistema DEBE pasar al núcleo un catálogo con `CLIENTE` y `MINUTA`, identificado por `Documento.nombre_original`; la clave conserva la extensión porque el núcleo la usa para decidir si una fuente es imagen al extraer el DNI. Esto no decide qué texto entra a `revisar_parrafos()`.
- **FR-010**: El sistema DEBE avisar, y no confrontar, cuando un documento necesario tenga el texto suprimido o vacío.
- **FR-011**: El sistema NO DEBE guardar las observaciones en esta fase; se calculan cuando se piden.
- **FR-012**: El sistema NO DEBE ejecutar la capa de léxico en esta fase ni importar nada de `experimental/`.
- **FR-013**: El sondeo de estado DEBE devolver por cada borrador su disponibilidad de confrontación y el motivo seguro cuando no esté disponible, sin texto, ruta, hash ni nombre de archivo.
- **FR-014**: La aplicación DEBE consolidar una `FALTA` cuando su valor esperado ya esté presente como valor esperado de una discrepancia del mismo campo, sin modificar la salida del núcleo.
- **FR-015**: La tabla de regla NO DEBE mostrar columnas vacías de motivo o porcentaje; el detalle de coincidencia se muestra en las observaciones donde exista y la tabla de ortografía conserva su motivo.
- **FR-016**: La normalización de la capa de regla DEBE conservar `Ñ`/`ñ` como
  `Ñ`, mientras continúa ignorando las tildes de las vocales, para distinguir
  una eñe omitida en el borrador.
- **FR-017**: La pantalla de confrontación DEBE mostrar, plegada por defecto,
  el catálogo agregado de `NOMBRE`, `DNI`, `PARTIDA` y `MONTO`, ordenado y
  legible, además del catálogo obtenido al pasar cada fuente por separado a
  `nucleo.verificar.catalogo()` y el conteo de caracteres de su texto.
- **FR-018**: La pantalla DEBE señalar de forma visible cada fuente cuyo
  catálogo no aporte ningún campo, sin mostrar su texto completo; este resumen
  solo se entrega en la respuesta HTML autorizada y nunca en el sondeo JSON.

### Requisitos de seguridad y privacidad (Constitución I, IV y VI)

- Solo el creador del expediente y los Administradores pueden confrontarlo.
- La confrontación es determinista: la misma entrada produce siempre la misma salida. No interviene ningún modelo de lenguaje.
- Las observaciones y los fragmentos del borrador se muestran en pantalla al usuario autorizado, pero NUNCA se escriben en logs ni en mensajes de error.
- El resultado no se envía a ningún servicio externo.
- La confrontación no crea archivos nuevos ni reabre los originales: trabaja sobre el texto ya guardado.

### Requisitos de usabilidad y accesibilidad (Constitución VIII)

- Estado visible: mientras la confrontación se calcula, la pantalla lo indica.
- Cada grupo de observaciones muestra cuántas hay, para dimensionar el trabajo de un vistazo.
- Estado vacío comprensible: "no se encontraron observaciones" se distingue de un fallo.
- El aviso de borrador ajeno es visualmente distinto de una observación corriente: es una advertencia, no un error de redacción.
- La acción de confrontar solo está disponible cuando se puede ejecutar, y si no, se explica qué falta.

### Key Entities *(include if feature involves data)*

F5 no añade entidades nuevas, pero modifica los roles de `Documento` con una
migración reversible que convierte `FUENTE` histórico en `CLIENTE`. Consume
`Expediente`, `Documento` y `TextoExtraido`, y produce un resultado en memoria
que se muestra y se descarta.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Sobre el expediente de referencia, la confrontación en el ERP encuentra las mismas observaciones de la capa de regla que la aplicación actual, sin retrocesos.
- **SC-002**: Un borrador ficticio con un DNI alterado, un nombre alterado y un monto alterado produce exactamente esas tres observaciones de regla, con su valor esperado.
- **SC-003**: Un borrador ficticio que no corresponde al expediente produce el aviso y ninguna lista campo por campo.
- **SC-004**: Ninguna prueba ni fixture usa datos reales.
- **SC-005**: Repetir la confrontación sobre el mismo expediente produce un resultado idéntico.

## Assumptions

- `nucleo/verificar.py` conserva su comportamiento medido salvo FR-016, que
  corrige la pérdida silenciosa de la eñe; `nucleo/ortografia.py` no cambia.
  La medición contra el expediente de referencia sigue siendo privada.
- El diccionario `es_PE` y la lista de términos de la casa ya se aprovisionan como en `adaptadores/diccionario.py`.
- La capa de léxico queda fuera de F5 hasta decidir de dónde sale el corpus de escrituras firmadas.
- El informe exportable es F7 y el historial es F6; F5 solo muestra en pantalla.
