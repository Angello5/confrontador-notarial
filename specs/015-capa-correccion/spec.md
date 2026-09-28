# Feature Specification: F21 · Capa de corrección, confirmación única y documento corregido

**Feature Branch**: `Angello5/capa-de-corrección-y-documento-corregido-f21-correccion`

**Created**: 2026-09-28

**Status**: Draft

**Input**: Anexo A.3 del contrato (fase CONSTRUCCIÓN): «EL SOFTWARE conserva la capa de corrección sobre el documento, la cual identifica aquellas correcciones cuyo valor correcto difiere del valor erróneo, respetando los límites de palabra y descartando los reemplazos que truncarían un texto a uno de sus propios prefijos. Concluida la corrida, EL SOFTWARE presenta al usuario, en una única vista consolidada, la relación de correcciones propuestas, indicando respecto de cada una el valor erróneo detectado, el valor correcto propuesto y el documento fuente del que este último fue construido. La aplicación de las correcciones se produce mediante una sola acción de confirmación del usuario respecto de la totalidad de la relación, sin perjuicio de que este pueda excluir individualmente cualquier corrección antes de confirmar. EL SOFTWARE conserva el documento original en versión inalterable y genera el documento corregido como archivo distinto. El manifiesto de auditoría registra, respecto de cada corrida, la identidad del usuario que confirmó la aplicación, la fecha y la hora, y las correcciones que hubieran sido excluidas.» Anexo B: P-03, P-04, P-10.

## Principio

**Solo se corrige lo que el núcleo ya señaló con un «debe decir» trazable a una fuente, en su ocurrencia y con una confirmación explícita.** Nada más del documento cambia.

## Requirements *(mandatory)*

### Capa de corrección (núcleo puro)

- **FR-001**: `nucleo/correccion.py::correcciones(salidas, fuentes)` recibe las salidas textuales de la regla (`[CAMPO] «erróneo» debe decir «correcto»…`) y los textos de las fuentes (`{nombre: texto}`, páginas separadas por `\f`) y devuelve la carga útil: lista de `{id, campo, erroneo, correcto, fuente: {archivo, pagina}, ocurrencia}`.
- **FR-002 (P-03)**: Se descarta la corrección cuyo correcto normalizado es igual al erróneo normalizado.
- **FR-003 (truncado)**: Se descarta la corrección cuyo correcto es prefijo propio del erróneo.
- **FR-004 (sin valor correcto)**: `FALTA`, «no coincide con ninguna fuente», `[PARRAFO]` y las observaciones de persona (F11, F12) no son correcciones: siguen siendo solo hallazgos.
- **FR-005**: `[NUMERO_EN_LETRAS]` no es corrección: su «debe decir» es la cifra, no el texto en letras. [NEEDS CLARIFICATION: ¿se genera el número en letras a partir de la cifra? Por defecto no; queda como hallazgo.]
- **FR-006 (fuente)**: La fuente es la primera página (en el orden de las fuentes) cuyo texto normalizado contiene el valor correcto como secuencia de palabras completas (letras y dígitos). Sin fuente localizable no hay corrección, solo hallazgo.
- **FR-007 (límites de palabra)**: El erróneo se ubica en el texto con límites de palabra (ni letra ni dígito a los lados), sin distinguir mayúsculas ni tildes.
- **FR-008 (ocurrencia)**: La corrección k-ésima (desde 0) con el mismo erróneo apunta a su k-ésima ocurrencia en el borrador. [NEEDS CLARIFICATION: el núcleo no da la posición exacta; por defecto se toma el orden de aparición, que es el orden en que la regla recorre el texto. Las ocurrencias repetidas de un nombre mal escrito que la regla reporta una sola vez no se corrigen.]
- **FR-009**: El `id` es estable: SHA-256 de `campo|erróneo|correcto|ocurrencia`, 12 caracteres. Misma entrada, misma salida.

### Documento corregido

- **FR-010**: Se aplica sobre el `.docx` original con la biblioteca estándar (`zipfile` + expresiones regulares sobre `word/document.xml`), el mismo enfoque que ya usa la extracción. Los demás miembros del paquete se copian sin cambios. [Nota: python-docx no está en `requirements.txt`; no se añade dependencia.]
- **FR-011 (P-04)**: Solo cambia el texto de las correcciones aplicadas; el resto del XML queda idéntico byte a byte. Una corrección cuyo erróneo no se ubica en su ocurrencia o que se solapa con otra ya aplicada no se aplica y se informa como «no aplicada».
- **FR-012**: El reemplazo se escribe en el primer fragmento de texto (`w:t`) que abarca el erróneo, conservando su formato; los fragmentos siguientes pierden solo los caracteres corregidos. El valor correcto se escribe tal como lo da la fuente normalizada (mayúsculas, sin tildes). [NEEDS CLARIFICATION: ¿conservar mayúsculas/tildes del original? Por defecto se escribe el valor normalizado.]
- **FR-013**: El corregido es un archivo nuevo «<nombre>-corregido.docx»; el original no se modifica y su SHA-256 se verifica contra el registrado antes de aplicar.

### Vista y confirmación

- **FR-014**: En la pantalla de resultado, una tabla «Correcciones propuestas» con valor erróneo, valor correcto, documento fuente (archivo y página) y una casilla por fila, marcada por defecto; UN botón «Aplicar correcciones» con confirmación.
- **FR-015 (P-10)**: El POST exige CSRF, rol, permiso sobre el expediente y el campo `confirmado`; sin él no se aplica nada. La casilla desmarcada = corrección excluida.
- **FR-016**: El servidor vuelve a confrontar y compara la huella de la corrida (SHA-256 de los hashes del borrador y de las fuentes y de los ids propuestos) con la enviada; si difiere, no aplica nada y pide volver a confrontar.
- **FR-017**: Tras aplicar se muestra el resumen (aplicadas, excluidas, no aplicadas) y la descarga del corregido, servida por una vista con los mismos permisos (nunca como estático).
- **FR-018**: Sin original conservado (borrador que no es `.docx`, o subido antes de F21) la tabla se muestra sin botón y con el aviso de que el borrador no admite corrección automática.

### Registro

- **FR-019**: `AplicacionCorreccion` (inmutable) guarda borrador, huella de la corrida, usuario confirmante, fecha y hora, ids aplicados, excluidos y no aplicados, y el SHA-256 del corregido.

### Conservación del original (enmienda de la constitución 1.7.0)

- **FR-020**: Solo el archivo del BORRADOR `.docx` se conserva como original inalterable (permisos `0400`, directorio `0700`) en `EXPEDIENTES_ORIGINALES_DIR`, fuera del repositorio y de `static/`. Los documentos del cliente y la minuta siguen borrándose tras la extracción.
- **FR-021**: La ruta nunca se muestra ni se registra. Eliminar el documento borra su original y sus corregidos; `suprimir_texto_expediente` también borra los originales y corregidos del expediente.

## Requisitos de seguridad

- Quién: roles Administrador y Usuario, con permiso sobre el expediente (creador o Administrador). Aplicar y descargar exigen login, rol y permiso; aplicar exige POST con CSRF.
- Qué datos: el `.docx` del borrador (datos personales) queda en disco del servidor, fuera de `static/`, con permisos restrictivos y supresión a solicitud.
- Qué se valida: huella de la corrida, ids contra la carga útil recalculada (un id ajeno se ignora), hash del original.

## Requisitos de UX (principio VIII)

- Casillas con etiqueta accesible por fila; confirmación antes de aplicar (acción irreversible sobre el archivo nuevo).
- Mensajes claros: «Las fuentes o el borrador cambiaron. Vuelva a confrontar antes de aplicar.», «Confirme la aplicación de las correcciones para continuar.»
- Sin términos técnicos: no se muestra la huella ni rutas.

## Success Criteria *(mandatory)*

- **SC-001 (P-03)**: Cero correcciones con valor propuesto idéntico al erróneo.
- **SC-002 (P-04)**: En la prueba de conteo, las palabras del documento antes y después difieren solo en las palabras corregidas.
- **SC-003 (P-10)**: Sin `confirmado` no se genera archivo ni registro.
- **SC-004**: El original conserva su SHA-256 tras aplicar.

## Assumptions

- La vinculación de `AplicacionCorreccion` con la `Corrida` de F20 se hace al integrar (ver plan.md).
- Solo se corrige `word/document.xml`; encabezados, pies y notas no.
