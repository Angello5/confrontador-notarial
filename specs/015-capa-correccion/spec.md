# Feature Specification: F21 · Capa de corrección, confirmación única y documento corregido

**Feature Branch**: `Angello5/capa-de-corrección-y-documento-corregido-f21-correccion`

**Created**: 2026-09-28

**Status**: Implementado e integrado (PR #54)

**Input**: Anexo A.3 del contrato (fase CONSTRUCCIÓN): «EL SOFTWARE conserva la capa de corrección sobre el documento, la cual identifica aquellas correcciones cuyo valor correcto difiere del valor erróneo, respetando los límites de palabra y descartando los reemplazos que truncarían un texto a uno de sus propios prefijos. Concluida la corrida, EL SOFTWARE presenta al usuario, en una única vista consolidada, la relación de correcciones propuestas, indicando respecto de cada una el valor erróneo detectado, el valor correcto propuesto y el documento fuente del que este último fue construido. La aplicación de las correcciones se produce mediante una sola acción de confirmación del usuario respecto de la totalidad de la relación, sin perjuicio de que este pueda excluir individualmente cualquier corrección antes de confirmar. EL SOFTWARE conserva el documento original en versión inalterable y genera el documento corregido como archivo distinto. El manifiesto de auditoría registra, respecto de cada corrida, la identidad del usuario que confirmó la aplicación, la fecha y la hora, y las correcciones que hubieran sido excluidas.» Anexo B: P-03, P-04, P-10.

## Principio

**Solo se corrige lo que el núcleo ya señaló con un «debe decir» trazable a una fuente, en cada aparición del valor erróneo y con una confirmación explícita.** Nada más del documento cambia.

## Requirements *(mandatory)*

### Capa de corrección (núcleo puro)

- **FR-001**: `nucleo/correccion.py::correcciones(salidas, fuentes)` recibe las salidas textuales de la regla (`[CAMPO] «erróneo» debe decir «correcto»…`) y los textos de las fuentes (`{nombre: texto}`, páginas separadas por `\f`) y devuelve la carga útil: lista de `{id, campo, erroneo, correcto, fuente: {archivo, pagina}}`. Un mismo par erróneo → correcto (normalizado) da una sola corrección aunque la regla lo reporte varias veces.
- **FR-002 (P-03)**: Se descarta la corrección cuyo correcto normalizado es igual al erróneo normalizado.
- **FR-003 (truncado)**: Se descarta la corrección cuyo correcto es prefijo propio del erróneo.
- **FR-004 (sin valor correcto)**: `FALTA`, «no coincide con ninguna fuente», `[PARRAFO]` y las observaciones de persona (F11, F12) no son correcciones: siguen siendo solo hallazgos.
- **FR-005**: `[NUMERO_EN_LETRAS]` no es corrección: su «debe decir» es la cifra, no el texto en letras. [NEEDS CLARIFICATION: ¿se genera el número en letras a partir de la cifra? Por defecto no; queda como hallazgo.]
- **FR-006 (fuente)**: La fuente es la primera página (en el orden de las fuentes) cuyo texto normalizado contiene el valor correcto como secuencia de palabras completas (letras y dígitos). Sin fuente localizable no hay corrección, solo hallazgo.
- **FR-007 (límites de palabra)**: El erróneo se ubica en el texto con límites de palabra (ni letra ni dígito a los lados), sin distinguir mayúsculas ni tildes.
- **FR-008 (todas las apariciones, A.3 · ronda 2)**: Cada corrección se aplica a TODAS las apariciones del erróneo en el borrador, con límites de palabra (FR-007): «9000011» no toca «90000111». La exclusión sigue siendo por fila y excluye todas sus apariciones.
- **FR-008a (competencia)**: Si apariciones de dos correcciones distintas se solapan en un tramo, no se aplica ninguna de las dos en ese tramo y ambas se listan como «no aplicadas»; sus demás apariciones sí se aplican. [NEEDS CLARIFICATION: una corrección aplicada en unas apariciones y en competencia en otras figura a la vez en aplicadas y en no aplicadas. Por defecto así, sin adivinar cuál gana.]
- **FR-009**: El `id` es estable: SHA-256 de `campo|erróneo|correcto` (del primer reporte del par), 12 caracteres. Misma entrada, misma salida.

### Documento corregido

- **FR-010**: Se aplica sobre el `.docx` original con la biblioteca estándar (`zipfile` + expresiones regulares sobre `word/document.xml`), el mismo enfoque que ya usa la extracción. Los demás miembros del paquete se copian sin cambios. [Nota: python-docx no está en `requirements.txt`; no se añade dependencia.]
- **FR-011 (P-04)**: Solo cambia el texto de las correcciones aplicadas; el resto del XML queda idéntico byte a byte. Una corrección cuyo erróneo no aparece en el borrador, o que compite con otra en algún tramo (FR-008a), se informa como «no aplicada».
- **FR-012**: El reemplazo se escribe en el primer fragmento de texto (`w:t`) que abarca el erróneo, conservando su formato; los fragmentos siguientes pierden solo los caracteres corregidos. El valor correcto se escribe tal como lo da la fuente normalizada (mayúsculas, sin tildes). [NEEDS CLARIFICATION: ¿conservar mayúsculas/tildes del original? Por defecto se escribe el valor normalizado.]
- **FR-013**: El corregido es un archivo nuevo «<nombre>-corregido.docx»; el original no se modifica y su SHA-256 se verifica contra el registrado antes de aplicar.

### Vista y confirmación

- **FR-014**: En la pantalla de resultado, una tabla «Correcciones propuestas» con valor erróneo, valor correcto, documento fuente (archivo y página), cuántas apariciones corrige en el borrador («3 apariciones», contadas sobre el `.docx` original con todas las filas marcadas) y una casilla por fila, marcada por defecto; UN botón «Aplicar correcciones» con confirmación. [F48: la confirmación muestra una fila por observación, con las que no tienen corrección propuesta bloqueadas; ver `specs/040-resumen-errores/`.]
- **FR-015 (P-10)**: El POST exige CSRF, rol, permiso sobre el expediente y el campo `confirmado`; sin él no se aplica nada. La casilla desmarcada = corrección excluida.
- **FR-016**: El formulario envía la `Corrida` (F20) registrada al confrontar. El servidor exige que sea de este borrador y con estado RESULTADO, que las entradas actuales (hashes de archivo y de texto, extractor, estado) sean las registradas y que los hallazgos recalculados con su fecha de referencia den la misma `huella`; si no, no aplica nada y pide volver a confrontar.
- **FR-017**: Tras aplicar se muestra el resumen (aplicadas, excluidas, no aplicadas) y la descarga del corregido, servida por una vista con los mismos permisos (nunca como estático).
- **FR-018**: Sin original conservado (borrador que no es `.docx`, o subido antes de F21) la tabla se muestra sin botón y con el aviso de que el borrador no admite corrección automática.

### Registro

- **FR-019**: El registro oficial es la `DecisionCorreccion` de F20 (inmutable, FK a la `Corrida`): usuario confirmante, fecha y hora, `correcciones_excluidas`, `apariciones` (`{id: n}`; sus claves son los ids aplicados), `correcciones_no_aplicadas` y `hash_corregido` (SHA-256 del corregido); migración 0004. El detalle de la corrida (historial) muestra quién confirmó, cuándo y cuántas correcciones se aplicaron y excluyeron, con la descarga del corregido.

### Conservación del original (enmienda de la constitución 1.7.0)

- **FR-020**: Solo el archivo del BORRADOR `.docx` se conserva como original inalterable (permisos `0400`, directorio `0700`) en `EXPEDIENTES_ORIGINALES_DIR`, fuera del repositorio y de `static/`. Los documentos del cliente y la minuta siguen borrándose tras la extracción.
- **FR-021**: La ruta nunca se muestra ni se registra. Eliminar el documento borra su original y sus corregidos; `suprimir_texto_expediente` también borra los originales y corregidos del expediente.

## Requisitos de seguridad

- Quién: roles Administrador y Usuario, con permiso sobre el expediente (creador o Administrador). Aplicar y descargar exigen login, rol y permiso; aplicar exige POST con CSRF.
- Qué datos: el `.docx` del borrador (datos personales) queda en disco del servidor, fuera de `static/`, con permisos restrictivos y supresión a solicitud.
- Qué se valida: corrida (entradas y huella de hallazgos), ids contra la carga útil recalculada (un id ajeno se ignora), hash del original.

## Requisitos de UX (principio VIII)

- Casillas con etiqueta accesible por fila; confirmación antes de aplicar (acción irreversible sobre el archivo nuevo).
- Mensajes claros: «Las fuentes o el borrador cambiaron. Vuelva a confrontar antes de aplicar.», «Confirme la aplicación de las correcciones para continuar.»
- Sin términos técnicos: no se muestran rutas.

## Success Criteria *(mandatory)*

- **SC-001 (P-03)**: Cero correcciones con valor propuesto idéntico al erróneo.
- **SC-002 (P-04)**: En la prueba de conteo, las palabras del documento antes y después difieren solo en las palabras corregidas.
- **SC-003 (P-10)**: Sin `confirmado` no se genera archivo ni registro.
- **SC-004**: El original conserva su SHA-256 tras aplicar.
- **SC-005 (A.3)**: Un erróneo repetido 3 veces queda corregido las 3 veces y el resto de palabras no cambia; «9000011» junto a «90000111» solo se corrige donde hay límite de palabra.

## Assumptions

- Integrada con F20: la decisión se enlaza a la `Corrida` de la confrontación (ver plan.md).
- Solo se corrige `word/document.xml`; encabezados, pies y notas no.
