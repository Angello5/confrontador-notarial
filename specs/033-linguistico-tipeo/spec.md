# F39 · Errores lingüísticos y anexo omitido

**Fecha**: 2026-10-05  
**Estado**: implementado en el núcleo y en el extractor de .docx; cobertura con datos ficticios.  
**Alcance**: `nucleo/ortografia.py`, `nucleo/verificar.py`, `adaptadores/extraccion.py`, `expedientes/services.py`, `lista_notarial.txt` y catálogo de reglas.

## Origen

El usuario pidió el 2026-10-05 quitar la regla de párrafos y centrar la revisión en los errores lingüísticos.

La capa lingüística (F23, `specs/017-componente-linguistico/`) mostraba 76 filas en los 11 expedientes de prueba. Solo unas 14 eran errores reales; el resto venía de cinco fuentes de ruido:

- las iniciales del digitador en la línea de cierre;
- el nombre del abogado que autoriza la minuta;
- siglas como SAC, EIRL y UIT;
- palabras válidas que faltan en el diccionario, como SUSCRIBIENDOLO y BIOMETRICA;
- topónimos repetidos legítimamente, como «LIMA LIMA».

La regla de párrafos daba 9 alertas: 5 eran ruido (sellos, firmas, «HYPERLINK», viñetas) y 4 correspondían al Anexo 1 de dos expedientes.

Al revisar la primera versión en pantalla, el usuario hizo tres observaciones:

- **«AvENIDA» marcado, pero el documento dice «AVENIDA».** Los borradores usan el formato «Todo mayúsculas» de Word (`w:caps`). El texto tecleado conserva minúsculas que nunca se imprimen, y el extractor leía el texto tecleado, no el impreso.
- **El anexo no se omite: va insertado como Recaudos.pdf.** En los créditos que lo traen así, después de «INSERTO:» el borrador pasa directo a las firmas, y la hoja resumen escaneada (con su importe) está entre los recaudos.
- **Persona sin ficha RENIEC.** Le gusta que no se compare (no hay con qué verificar), pero puede ser contraproducente: el nombre del representante de una empresa estaba mal escrito y solo salía «Sin ficha». Aceptó el término medio: el aviso sigue siendo MEDIA y muestra cómo escribe la minuta el nombre si lo escribe distinto.

## Comportamiento implementado

- **Texto como se imprime**:
  - El extractor de .docx pone en mayúsculas el texto de los runs con «Todo mayúsculas» o versalitas.
  - Ese formato puede venir del run, de su estilo de carácter, del estilo del párrafo (con su herencia) o del defecto del documento.
  - El formato de la marca de párrafo no cuenta, y tampoco el formato anterior de un cambio controlado.
  - Versión del texto extraído: 4.
- **Anexo omitido** (`ANEXO`, MEDIA):
  - El ERP ya no compara la minuta párrafo por párrafo.
  - Para cada anexo de la minuta («ANEXO 1 – HOJA RESUMEN», «ANEXO III CRONOGRAMA…»), si falta la mayoría de sus párrafos, sale una sola alerta «No aparece en el borrador».
  - `revisar_parrafos` se conserva para `app.py`, `app_ortografia.py` y el CLI.
- **Anexo insertado**:
  - Si el borrador tiene «INSERTO:» y un monto del anexo (desde 1,000.00) figura en los recaudos, el anexo va como documento insertado.
  - En ese caso no se observa como omitido y sus montos no se exigen en el texto del borrador.
- **Persona sin ficha** (`SIN_FICHA`, MEDIA, de F38):
  - Si la minuta escribe distinto un nombre que no tiene ficha, el aviso lo muestra: «Sin ficha RENIEC en los recaudos; la minuta dice «…»».
  - El parecido se busca en ventanas del mismo número de palabras de la minuta, con un parecido de al menos 80. Un nombre de menos de 3 palabras no se busca.
  - No hay «debe decir» ni corrección automática.
- **Mayúsculas y minúsculas mezcladas** (capa lingüística):
  - Se reporta una palabra impresa con una minúscula intercalada («lA»), sea cual sea su largo.
  - No se reportan las palabras en mayúsculas, en minúsculas, con mayúscula inicial ni las marcas como «WhatsApp».
  - Con el texto ya leído como se imprime, solo aparece si el documento no usa «Todo mayúsculas».
- **Acento grave** (ortografía y tildes): «SÈTIMA» y «CLÀUSULA» salen con su corrección exacta («SÉTIMA», «CLÁUSULA»), en lugar de «no existe en castellano» con una sugerencia al azar. Como el resto de la ortografía (FR-002b), la palabra que ya trae la minuta no se reporta.
- **Palabra repetida**: solo se reportan palabras gramaticales («EL EL», «DE DE»). Los topónimos homónimos («LIMA LIMA») y los apellidos iguales son correctos.
- **Menos ruido en ortografía**:
  - las iniciales entre barras de la línea de cierre («-/@/ XYZ / -/@/») no se revisan;
  - el nombre del abogado de «AUTORIZA: …, ABOGADO(A)» se da por bueno;
  - «Nº» y «1ª» no forman palabra con la letra que sigue;
  - la lista de la casa suma siglas (SAC, SAA, SRL, EIRL, UIT, JUS, ICAP) y términos que el diccionario no trae.

Catálogo de reglas `2026.10.05-9`. `ANEXO` tiene severidad MEDIA; la capa lingüística sigue en BAJA.

## Medición

Confrontación en memoria de los 11 expedientes de prueba, más un borrador con errores sembrados que subió el usuario. Cada borrador se releyó con el extractor nuevo desde su original conservado.

- **Regla**:
  - desaparecen las 9 alertas de párrafo;
  - en los dos expedientes con la hoja resumen insertada como recaudo, el anexo y su monto ya no se observan;
  - los avisos de persona sin ficha de dos expedientes muestran el nombre que trae la minuta (el representante de la empresa acreedora, con letras cambiadas);
  - el resto de la regla y de personas no cambia;
  - el expediente con errores sembrados sigue con 8 de 8.
- **Lingüístico** (11 expedientes): pasa de 76 a 19 filas, de las cuales 18 son errores reales:
  - 4 acentos graves;
  - 5 «EL EL»;
  - 7 erratas: «CREDITOZ», «CONSTACIA», «RERERIDO», tres en una razón social y una en el nombre de una calle;
  - 1 espacio antes de coma;
  - 1 comilla sin cerrar.

  La fila restante es un anglicismo («PRICING»).
- **Borrador con errores sembrados** (18 cambios frente a su versión buena):
  - Detecta 11: nombres, DNI, partida, número de la dirección, «OCTAO» y «MEIO».
  - No detecta 6 que la minuta también trae:
    - «OCUPACIÒN» y «UIRBANIZACION» (dos veces): por FR-002b se dan por conocidas;
    - «QUÉ» por «CÓMO» (dos veces) y «TIENE» por «TIENEN»: son castellano válido.
  - Tampoco detecta «DECIO» por «DÉCIMO», porque el diccionario acepta «Decio».

## Límites

- El .doc antiguo (Word 97-2003) se convierte a texto plano sin aplicar «Todo mayúsculas».
- No se aplica la regla de Word por la que dos estilos con «Todo mayúsculas» se anulan entre sí (propiedades alternables).
- El anexo insertado se reconoce por un monto desde 1,000.00 presente en los recaudos; una hoja resumen sin montos así sigue contando como omitida (desde F58, con «INSERTO:» en el borrador sale como «No se pudo comprobar el anexo»).
- Un anexo hecho solo de filas cortas (menos de 80 caracteres) no se evalúa.
- La repetición de una palabra que no es gramatical («CONTRATO CONTRATO») ya no se reporta.
- La concordancia de género con la ficha RENIEC («QUEDANDO ADVERTIDA» para un otorgante varón) queda fuera.

## Verificación

- `tests/test_docx_tablas.py`: «Todo mayúsculas» directo, desactivado, heredado del estilo de párrafo, en la marca de párrafo y versalitas por estilo de carácter.
- `tests/test_linguistico.py`: minúscula intercalada, acento grave, palabra repetida y formas válidas (siglas, «Nº», marcas, abreviaturas, topónimos y apellidos repetidos), todo con datos ficticios.
- `tests/test_anexo_omitido.py`: anexo ausente, anexo presente, párrafo suelto fuera del anexo, minuta sin anexo, dos anexos y anexo insertado como recaudo (con y sin «INSERTO:» y monto).
- `tests/test_expedientes_confrontacion.py`: la confrontación llama a `anexos_omitidos` y no a `revisar_parrafos`; la traducción del aviso sin ficha conserva lo que dice la minuta.
- `tests/test_lectura_borrador.py`: nombre sin ficha escrito distinto e igual que en la minuta.
- `test_ortografia.py`: «OCUPACIÒN» ahora sale como «acento grave».

## F50 · Falsas «mayúsculas y minúsculas mezcladas» en un kardex ya cargado

**Fecha**: 2026-10-16  
**Alcance**: `expedientes/services.py`, `expedientes/views.py`, los comandos `procesar_documentos`, `reextraer_expediente` y `suprimir_texto_expediente`, las plantillas del kardex y del resultado, y pruebas.

### Origen

En un kardex real, la capa lingüística mostraba 2 observaciones BAJA «mayúsculas y minúsculas mezcladas» (p. ej. `OCHENTa`, sin sugerencia). En el documento impreso y en el visor la palabra está entera en mayúsculas.

### Causa

- **El formato ya se resolvía.** El run lleva su «Todo mayúsculas» directo (`<w:rPr>…<w:caps/>…</w:rPr>`) dentro de un párrafo cuyo estilo no tiene caps. Es el caso que resolvió F39, y el extractor actual lee la palabra entera en mayúsculas. Los 2 casos del borrador tienen esa estructura.
- **El texto guardado era anterior a F39.** El borrador se extrajo el 2026-09-28, antes de F39 (2026-10-05). Al volver a confrontar se reutilizaba el texto ya guardado del documento, aunque la versión del extractor hubiera cambiado. En la base local, ningún documento (144) tiene el texto de la versión actual del extractor.
- **El remedio fallaba en este kardex.** `reextraer_expediente <código>` buscaba el expediente con `get(codigo=…)`. Aquí hay un expediente archivado con el mismo código (F28 lo permite), así que el comando fallaba con `MultipleObjectsReturned`. `suprimir_texto_expediente` tenía el mismo fallo.

### Decisiones del usuario (2026-10-16)

- **Relectura:** «tiene que releer los borradores».
- **Aviso:** pedir que se vuelva a subir lo que no se puede releer.
- **Supresión:** `suprimir_texto_expediente` actúa solo sobre el expediente activo con ese código, nunca sobre los archivados que lo repitan.

### Comportamiento implementado

- **Relectura automática del borrador**:
  - En cada vuelta, el worker devuelve a la cola el borrador que cumple todo esto:
    - está LISTO;
    - su expediente está activo;
    - su texto viene de otra versión del extractor;
    - tiene su original `.docx` conservado (F21) y ese original pasa la verificación de su SHA-256.
  - Al releerse cambian las entradas de la confrontación, y el worker vuelve a confrontar sin intervención (F26, FR-003). La confrontación vieja deja de ser la vigente, y un «Confrontar» posterior ya no la reutiliza (F34).
  - No se releen la minuta ni los recaudos, que no tienen archivo (son temporales), ni el borrador PENDIENTE, PROCESANDO o en ERROR, ni los de expedientes archivados (F25).
  - Si la relectura falla, el borrador queda en ERROR y no vuelve a entrar.
  - `reextraer_expediente` y la relectura comparten `reencolar`.
- **Aviso para volver a subir**:
  - La pantalla del kardex y la del resultado muestran un aviso informativo cuando el kardex activo tiene documentos LISTO leídos con otra versión del extractor que no se releen solos: la minuta, los recaudos y el borrador sin original conservado (p. ej. el que no es `.docx`).
  - El aviso dice: «Algunos documentos se leyeron con una versión anterior del sistema. Elimínelos y vuelva a subirlos para aplicar las mejoras de lectura.», y lista los nombres de los documentos.
  - Dice «documentos» y no «recaudos», porque también incluye la minuta y el borrador. Pide eliminarlos primero porque, si se sube el mismo archivo sin eliminarlo, el sistema responde «Ya está registrado con este rol».
  - No es una observación: no entra en la confrontación, en los totales (F48), en el manifiesto ni en el informe impreso. Se calcula al mostrar la pantalla.
  - Usa el estilo `.aviso` existente.
- **`reextraer_expediente`** vuelve a poner en cola los documentos de todos los expedientes con ese código, archivados incluidos. Si no existe ninguno, sigue respondiendo «El expediente no existe.».
- **`suprimir_texto_expediente`** actúa solo sobre el expediente activo con ese código. Si no hay ninguno, o si hay un kardex y una transferencia vehicular activos con el mismo código, falla con un mensaje claro y no suprime nada.
- El extractor no cambia: no sube la versión del texto ni la del formato de caché.

### Cómo se ve el arreglo en un kardex ya cargado

Basta con que el worker esté corriendo. En pocos segundos relee el borrador `.docx` conservado y vuelve a confrontar; el resultado nuevo aparece en la pantalla del kardex. Para la minuta y los recaudos, el aviso pide eliminarlos y volver a subirlos.

### Pendiente

- [NEEDS CLARIFICATION] ¿Cómo se suprime el texto de un expediente archivado? Hoy el comando no lo permite.
- [NEEDS CLARIFICATION] ¿Cómo se suprime cuando hay un kardex y una transferencia vehicular activos con el mismo código? Hoy el comando se niega.

### Medición

- **Capa lingüística del kardex de la queja**, con las mismas fuentes:
  - con el texto guardado en la base: 12 filas, 2 de ellas «mezcladas»;
  - con el texto actual: 10 filas, ninguna «mezclada».
- **9 casos de prueba**: con el extractor actual hay 0 filas «mezcladas». `main` y esta rama dan los mismos recuentos, 37 filas lingüísticas en total, porque el núcleo y el extractor no cambian.
- **Base local** (solo lectura): el worker releería 10 borradores. Todos los kardex activos (10) mostrarían el aviso, con 62 documentos en total: 10 minutas y 52 recaudos.

### Verificación

- `tests/test_docx_tablas.py`:
  - `test_reextraer_con_codigo_repetido_por_un_archivado`: fallaba en `main` con `MultipleObjectsReturned`.
  - `test_mezcladas_solo_si_word_no_las_imprime_en_mayusculas`: es la estructura del caso con valores ficticios. Ya pasaba en `main` y queda como regresión. La palabra tecleada sin «Todo mayúsculas» sigue marcándose.
- `tests/test_confrontacion_automatica.py`:
  - relectura del borrador de otra versión y nueva confrontación automática, sin volver a releerlo después;
  - casos que no se releen: minuta, borrador en ERROR, borrador sin original y borrador de un archivado;
  - el aviso en el kardex y en el resultado: solo lista lo que no se relee y no entra en la confrontación.
- `tests/test_expedientes_commands.py`: la supresión solo afecta al activo, y sin un único activo no suprime nada.

## F58 · Signo sin cerrar comprensible y anexo que no se puede comprobar

**Fecha**: 2026-10-20  
**Alcance**: `nucleo/ortografia.py` (`_sin_cerrar` y `redaccion`), `nucleo/verificar.py` (`anexos_omitidos`), `expedientes/services.py` (`parsear_observacion_regla`) y catálogo de reglas.

### Origen

- **Comillas sin cerrar**: en un kardex real, una línea de 659 caracteres del borrador abría una razón social con comilla tipográfica `“` y la cerraba con comilla recta `"`. La observación llevaba como fragmento la línea entera (un párrafo enorme en pantalla), el motivo «comillas sin cerrar» y ninguna sugerencia. El usuario no entendía qué estaba mal.
- **Anexo omitido**: en otro kardex, el «ANEXO 1 – HOJA RESUMEN» de la minuta es solo el título y el bloque de firmas, porque la tabla no llega al texto extraído. El borrador trae dos «INSERTO :». Como el anexo no tiene montos que buscar en los recaudos, no se reconocía como insertado y la pantalla decía «No aparece en el borrador», aunque los dos anexos estaban insertados.

### Decisión — anexo sin montos con inserto (confirmado por el usuario, 2026-10-20)

«Mantener aviso, aclarado: sigue saliendo, pero como “No se pudo comprobar el anexo: verifique que esté insertado”, en lugar de “No aparece en el borrador”».

### Comportamiento implementado

- **Signo sin cerrar** (capa lingüística, BAJA):
  - Cada línea se recorre una vez. Cada paréntesis y cada comilla de apertura busca su cierre; una comilla recta tras otra comilla abierta abre una anidada si le sigue una letra o cifra, y si no, cierra la abierta.
  - **Comilla cerrada con otro signo**: el fragmento va desde la comilla de apertura hasta el cierre equivocado (`“INVERSIONES FICTICIAS E.I.R.L."`). El motivo dice cuál: «comilla “ cerrada con comilla recta "» o, al revés, «comilla recta " cerrada con comilla ”». La sugerencia es el mismo fragmento con el cierre correcto (`“INVERSIONES FICTICIAS E.I.R.L.”`).
  - La sugerencia solo se da si es inequívoca: si el cierre correcto aparece más adelante antes de otra apertura (por ejemplo, `TUBO “DE 3" PULGADAS”`), la comilla recta puede ser otra cosa y queda «Sin sugerencia».
  - **Sin cierre**: el motivo es «falta cerrar el paréntesis» o «falta cerrar la comilla», sin sugerencia. El fragmento es una ventana de unos 60 caracteres alrededor del signo, sin cortar palabras.
  - El fragmento es siempre texto literal de la línea, para que la pantalla lo ubique en el borrador.
  - Para descartar lo que se solapa con un dato protegido solo cuenta el signo de apertura: una razón social o un nombre dentro del fragmento no ocultan la observación.
  - Cada signo sin pareja de una línea es una observación (antes, una por línea).
- **Anexo que no se puede comprobar** (`ANEXO`, MEDIA):
  - Si el anexo falta, el borrador tiene «INSERTO:» y el anexo no tiene montos desde 1,000.00, el núcleo emite `[ANEXO] SIN COMPROBAR: «…»`.
  - En pantalla: «No se pudo comprobar el anexo» y «Verifique que «…» esté insertado».
  - No es corregible en el Word: no entra en la carga de `correccion.correcciones`.
  - Sin «INSERTO:», o con un anexo que tiene montos que no están en los recaudos, sigue «No aparece en el borrador».
- Catálogo de reglas `2026.10.20-16`: las confrontaciones guardadas se recalculan.

### Límites

- Si el cierre equivocado queda lejos de la apertura, el fragmento es largo: va hasta ese cierre.
- La comilla simple y el apóstrofo no se revisan.
- Las comillas rectas anidadas dentro de otras rectas no se distinguen: la segunda cierra la primera.

### [NEEDS CLARIFICATION]

- **Anexo sin montos con párrafos de contenido**: con «INSERTO:», un anexo sin montos sale como «No se pudo comprobar» aunque le falten párrafos de contenido y no solo el bloque de firmas. El texto extraído no permite distinguir con certeza las firmas del contenido, y no hay una regla de la notaría para hacerlo. Falta que el usuario confirme si este caso debe seguir como «No aparece en el borrador».

### Medición

Medición privada, solo lectura, main frente a esta rama:

- **Base local** (10 expedientes, dos de ellos cargas del caso de referencia):
  - kardex de la comilla: la observación pasa de un fragmento de 659 caracteres sin sugerencia a uno de 30 caracteres con motivo concreto y sugerencia; sigue ubicada en el borrador;
  - kardex del anexo: pasa de «No aparece en el borrador» a «No se pudo comprobar el anexo»;
  - el total de filas lingüísticas no cambia (19) y los demás kardex no cambian.
- **9 casos de prueba** con el OCR propio del guion: los mismos dos cambios; el resto igual.
- El caso de referencia sigue con 8 de 8 en las dos cargas.

### Verificación

- `tests/test_linguistico.py`, con datos inventados:
  - comilla tipográfica cerrada con recta en una línea de más de 600 caracteres: fragmento, motivo, sugerencia, dato protegido dentro del fragmento y ubicación en el texto;
  - el caso inverso, y el ambiguo sin sugerencia;
  - ventana corta para un paréntesis sin cerrar en una línea larga;
  - comillas rectas anidadas dentro de tipográficas sin observación;
  - los motivos nuevos en los casos existentes.
- `tests/test_anexo_omitido.py`: anexo sin montos con «INSERTO:» (no corregible), y sin «INSERTO:» o con montos sigue «FALTA».
- `tests/test_expedientes_confrontacion.py`: el formato nuevo se interpreta y no cae en «formato desconocido».
