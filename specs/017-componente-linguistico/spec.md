# Feature Specification: F23 · Componente lingüístico

**Feature Branch**: `Angello5/componente-lingüístico-f23-linguistico`

**Created**: 2026-09-28

**Status**: Implementado e integrado (PR #50)

**Input**: Anexo A.4 del contrato (literal): «La revisión ortográfica, de tildes, gramatical y de redacción se resuelve mediante componente de ejecución local. Dicho componente carece de autoridad sobre los datos de validación obligatoria del punto A.3 y carece de permiso de escritura directa sobre el documento.» La ortografía (`nucleo/ortografia.py`) existe pero su llamada quedó comentada y su sección oculta a pedido del propietario (2026-09-27, `044b5ef`). El contrato la exige.

## Principio

**La capa lingüística solo informa.** Sus hallazgos se muestran en su propia sección; nunca tocan, contradicen ni sustituyen lo que deciden las capas de regla y personas (datos del A.3), y nunca se escriben en el documento.

## Requirements *(mandatory)*

- **FR-001 (reactivación)**: `confrontar_borrador` vuelve a ejecutar `ortografia.revisar` (ortografía y tildes, hunspell `es_PE` + lista de la casa) sobre el borrador. Sus filas van en `resultado["ortografia"]` (clave histórica que se conserva para no romper a los consumidores), con el formato del adaptador existente (`palabra`, `motivo`, `sugerencia`, `ubicacion`).
- **FR-002 (sin autoridad sobre el A.3)**: No se reporta ninguna palabra que forme parte de un dato del A.3: nombres y cónyuges del catálogo (anclas, adjuntos, menciones), domicilio y distrito de las personas, y los valores hallados que la regla o personas ya observaron. DNI, RUC, partidas y montos son numéricos y el revisor solo examina palabras de letras. En gramática y redacción (FR-004) se descarta todo hallazgo cuyo tramo se solape con la aparición en el borrador de uno de esos valores o de un DNI, partida o monto del catálogo.
- **FR-002b (vocabulario del expediente)**: Toda palabra de 3 o más letras que aparezca literalmente (sin distinguir mayúsculas) en el texto de cualquier fuente del expediente (documentos del cliente y minuta) se da por conocida y no se reporta por ortografía ni tildes: se pasa a `ortografia.revisar` junto con las palabras propias del A.3. La lógica de tildes y de «no existe en castellano» no cambia para las palabras ausentes de las fuentes.
- **FR-003 (no disponible)**: Si el diccionario no está aprovisionado, la confrontación NO se bloquea: `resultado["linguistico_aviso"]` = «Ortografía y tildes no disponibles: falta aprovisionar el diccionario es_PE.»; la ortografía queda vacía y las demás capas, incluida FR-004, siguen. Sin aviso, la clave vale `""`.
- **FR-004 (gramática y redacción)**: Reglas deterministas locales en `nucleo/ortografia.py::redaccion(texto, protegidos)`, que devuelve tuplas `(fragmento, motivo, sugerencia)` como `revisar`:
  - palabra repetida consecutiva de 2 o más letras, sin distinguir mayúsculas («DE DE») → «palabra repetida», sugerencia la palabra una vez;
  - espacio entre una palabra y `,` `;` `:` o `.` (salvo puntos suspensivos o de relleno `...`) → «espacio antes de signo»;
  - paréntesis, comillas dobles `"`, `«»` o `“”` sin cerrar en una cláusula (cláusula = línea no vacía del borrador) → «paréntesis sin cerrar» / «comillas sin cerrar» (desde F58, motivo y fragmento concretos: ver `specs/033-linguistico-tipeo/spec.md`);
  - concordancia de artículo `EL`/`DEL`/`AL`/`LA` con una lista cerrada de sustantivos frecuentes en escrituras: femeninos `CLAUSULA`, `PARTIDA`, `ESCRITURA`, `MINUTA`, `VENDEDORA`, `COMPRADORA`, `PROPIEDAD`, `SOCIEDAD`; masculinos `CONTRATO`, `INMUEBLE`, `PRECIO`, `PREDIO`, `VENDEDOR`, `COMPRADOR` (sin distinguir tildes) → «concordancia de artículo».
  Sus filas se añaden a `resultado["ortografia"]` tras las de ortografía, en orden de aparición.
- **FR-005 (separación)**: Las filas lingüísticas nunca entran en `resultado["regla"]` ni en `resultado["personas"]`, ni en ninguna carga útil de corrección que se aplique al documento (F21): solo se muestran. La salida de regla y personas es idéntica con o sin capa lingüística (paridad).
- **FR-006 (pantalla)**: La pantalla de resultado muestra la tarjeta de métrica «Lingüístico» (valor = número de filas) y la sección «Lingüístico» con la tabla Texto / Motivo / Sugerencia / Ubicación y, si hay aviso, un aviso informativo. El resumen cuenta las filas lingüísticas como observaciones para revisar. Estilo F14 (`core/_metrica.html`, `core/_chip.html`).
- **FR-007**: Núcleo puro y determinista; sin dependencias, migraciones ni llamadas a modelos. Tests con datos ficticios.

## Fuera de alcance

La gramática y la redacción completas (concordancia general, tiempos verbales, estilo) requieren un motor lingüístico que no está en el alcance local actual; F23 cubre solo las reglas cerradas de FR-004.

## [NEEDS CLARIFICATION]

- **Alcance de FR-004**: se implementan por defecto las cuatro reglas listadas. ¿Añadir o quitar reglas?
- **`PARTE` fuera de la lista de concordancia**: «EL PARTE» es correcto en la práctica notarial (parte notarial al registro), así que `PARTE` no se evalúa. ¿Confirmar?
- **Cláusula = línea**: los párrafos del borrador llegan como líneas del texto extraído; un paréntesis abierto en una línea y cerrado en la siguiente se reporta. ¿Aceptable?

## Clarifications

### Session 2026-09-28

- Q: ¿Se marcan por ortografía las palabras que ya figuran en las fuentes del legajo? → A: No. En la medición del revisor sobre 9 borradores reales, 327 de 406 avisos de ortografía eran palabras presentes literalmente en alguna fuente (nombres, lugares, razones sociales, términos del expediente). Anexo B P-05 exige cero observaciones sobre datos correctos (FR-002b).
- Q: ¿Es «doble espacio» un error de redacción? → A: No. Aparece en todos los borradores por la justificación de Word; la regla se retira de FR-004.

## Success Criteria *(mandatory)*

- **SC-001**: Con diccionario, un borrador ficticio con «CLAÚSULA», «DE DE», «LA CONTRATO» y un paréntesis sin cerrar muestra las cuatro filas en «Lingüístico» y ninguna en regla.
- **SC-002**: Sin diccionario, la confrontación devuelve `RESULTADO` con el aviso y las filas de FR-004.
- **SC-004**: Una palabra rara presente en una fuente no se reporta; la misma palabra ausente de las fuentes sí. Un doble espacio no se reporta.
- **SC-003**: Ningún hallazgo lingüístico sobre nombres, domicilios ni valores ya observados por la regla (tests ficticios); salida de regla y personas idéntica (paridad F13/F15 existentes).

## Assumptions

- Se reutiliza `lista_notarial.txt` sin cambios.
- La clave `ortografia` se conserva por compatibilidad; en la pantalla se titula «Lingüístico».
