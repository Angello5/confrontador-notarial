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
- El anexo insertado se reconoce por un monto desde 1,000.00 presente en los recaudos; una hoja resumen sin montos así sigue contando como omitida.
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
**Alcance**: `expedientes/management/commands/reextraer_expediente.py` y pruebas.

### Origen

En un kardex real, la capa lingüística mostraba 2 observaciones BAJA «mayúsculas y minúsculas mezcladas» (p. ej. `OCHENTa`, sin sugerencia). En el documento impreso y en el visor la palabra está entera en mayúsculas.

### Causa

- **El formato ya se resolvía.** El run lleva su «Todo mayúsculas» directo (`<w:rPr>…<w:caps/>…</w:rPr>`) dentro de un párrafo cuyo estilo no tiene caps. Es el caso que resolvió F39, y el extractor actual lee la palabra entera en mayúsculas. Los 2 casos del borrador tienen esa estructura.
- **El texto guardado era anterior a F39.** El borrador se extrajo el 2026-09-28, antes de F39 (2026-10-05). Al volver a confrontar se reutiliza el texto ya guardado del documento, aunque la versión del extractor haya cambiado. En la base local, ningún documento (144) tiene el texto de la versión actual del extractor.
- **El remedio fallaba en este kardex.** `reextraer_expediente <código>` buscaba el expediente con `get(codigo=…)`. Aquí hay un expediente archivado con el mismo código (F28 lo permite), así que el comando fallaba con `MultipleObjectsReturned`.

### Comportamiento implementado

- `reextraer_expediente` vuelve a poner en cola los documentos de todos los expedientes con ese código, archivados incluidos. Si no existe ninguno, sigue respondiendo «El expediente no existe.».
- El extractor no cambia: no sube la versión del texto ni la del formato de caché.

### Cómo se ve el arreglo en un kardex ya cargado

1. `python manage.py reextraer_expediente <código>`: el borrador se relee desde su original conservado (F21).
2. El worker lo procesa.
3. Volver a confrontar.

Los documentos del cliente y la minuta ya no tienen archivo temporal, así que salen como «Sin archivo» y conservan su texto.

### Pendiente

- [NEEDS CLARIFICATION] Cuando cambia la versión del extractor, ¿debe la confrontación releer sola el borrador conservado, o al menos avisar de que el texto es de una versión anterior? Hoy se confronta con el texto guardado sin avisar.
- [NEEDS CLARIFICATION] `suprimir_texto_expediente` tiene el mismo `get(codigo=…)` y falla igual con un código repetido. No se cambia aquí: decidir si la supresión alcanza a todos los expedientes con ese código o si debe elegirse uno.

### Medición

- **Capa lingüística del kardex de la queja**, con las mismas fuentes:
  - con el texto guardado en la base: 12 filas, 2 de ellas «mezcladas»;
  - con el texto actual: 10 filas, ninguna «mezclada».
- **9 casos de prueba**: con el extractor actual hay 0 filas «mezcladas». `main` y esta rama dan los mismos recuentos, 37 filas lingüísticas en total, porque el núcleo y el extractor no cambian.

### Verificación

- `tests/test_docx_tablas.py`:
  - `test_reextraer_con_codigo_repetido_por_un_archivado`: falla en `main` con `MultipleObjectsReturned`.
  - `test_mezcladas_solo_si_word_no_las_imprime_en_mayusculas`: es la estructura del caso con valores ficticios. Ya pasaba en `main` y queda como regresión. La palabra tecleada sin «Todo mayúsculas» sigue marcándose.
