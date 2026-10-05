# F39 · Errores lingüísticos y anexo omitido

**Fecha**: 2026-10-05  
**Estado**: implementado en el núcleo; cobertura con datos ficticios.  
**Alcance**: `nucleo/ortografia.py`, `nucleo/verificar.py`, `expedientes/services.py`, `lista_notarial.txt` y catálogo de reglas.

## Origen

El usuario pidió el 2026-10-05 quitar la regla de párrafos y centrar la revisión en los errores lingüísticos.

La capa lingüística (F23, `specs/017-componente-linguistico/`) mostraba 76 filas en los 11 expedientes de prueba. Solo unas 14 eran errores reales; el resto venía de cinco fuentes de ruido:

- las iniciales del digitador en la línea de cierre;
- el nombre del abogado que autoriza la minuta;
- siglas como SAC, EIRL y UIT;
- palabras válidas que faltan en el diccionario, como SUSCRIBIENDOLO y BIOMETRICA;
- topónimos repetidos legítimamente, como «LIMA LIMA».

A la vez, la capa no veía las erratas marcadas con una minúscula dentro de la palabra («lA», «HIzo», «LoS», «OCHENTa»). Ese tipo de errata aparece en 6 de los 11 borradores.

La regla de párrafos daba 9 alertas: 5 eran ruido (sellos, firmas, «HYPERLINK», viñetas) y 4 correspondían al anexo omitido en dos expedientes. El usuario ya había dicho que omitir el anexo (la hoja resumen con montos, cuotas y pagos) es un error real.

## Comportamiento implementado

- **Anexo omitido** (`ANEXO`, MEDIA): el ERP ya no compara la minuta párrafo por párrafo. Para cada anexo de la minuta («ANEXO 1 – HOJA RESUMEN», «ANEXO III CRONOGRAMA…»), si falta la mayoría de sus párrafos, sale una sola alerta: «ANEXO 1 – HOJA RESUMEN · No aparece en el borrador». `revisar_parrafos` se conserva para `app.py`, `app_ortografia.py` y el CLI.
- **Mayúsculas y minúsculas mezcladas** (capa lingüística):
  - Se reporta una palabra con una minúscula intercalada («lA», «HIzo», «CREDITOz»), sea cual sea su largo.
  - No se reportan las palabras en mayúsculas, en minúsculas ni con mayúscula inicial. Tampoco las marcas como «WhatsApp».
  - Se sugiere la palabra en mayúsculas solo si ya aparece así en el texto.
- **Acento grave** (ortografía y tildes): «SÈTIMA», «CLÀUSULA» y «RESOLUCIÒN» salen con su corrección exacta («SÉTIMA», «CLÁUSULA», «RESOLUCIÓN»), en lugar de «no existe en castellano» con una sugerencia al azar. Como el resto de la ortografía (FR-002b), la palabra que ya trae la minuta no se reporta.
- **Palabra repetida**: solo se reportan palabras gramaticales («EL EL», «DE DE», «QUE QUE»). Los departamentos, provincias y distritos homónimos («LIMA LIMA») y los apellidos iguales («ZAFIRO ZAFIRO») son correctos.
- **Menos ruido en ortografía**:
  - las iniciales entre barras de la línea de cierre («-/@/ XYZ / -/@/») no se revisan;
  - el nombre del abogado de «AUTORIZA: …, ABOGADO(A)» se da por bueno;
  - «Nº» y «1ª» no forman palabra con la letra que sigue;
  - la lista de la casa suma siglas (SAC, SAA, SRL, EIRL, UIT, JUS, ICAP) y términos que el diccionario no trae.

Catálogo de reglas `2026.10.05-7`. `ANEXO` tiene severidad MEDIA; la capa lingüística sigue en BAJA.

## Medición

Confrontación en memoria de los 11 expedientes de prueba:

- **Regla**: desaparecen las 9 alertas de párrafo y aparecen 2 de anexo omitido, una en cada expediente que lo omite. El resto de la regla y de personas no cambia; el expediente con errores sembrados sigue con 8 de 8.
- **Lingüístico**: pasa de 76 a 32 filas. Hay 31 errores reales:
  - 14 minúsculas intercaladas, entre ellas 5 en dos borradores que no tenían ninguna alerta (las de los nombres ya las observa la regla de nombres);
  - 4 acentos graves;
  - 5 «EL EL»;
  - 6 erratas: tres en una razón social, una en el nombre de una calle, «CONSTACIA» y «RERERIDO»;
  - 1 espacio antes de coma;
  - 1 comilla sin cerrar.

  La fila restante es un anglicismo («PRICING»).

## Límites

- Un anexo hecho solo de filas cortas (menos de 80 caracteres) no se evalúa.
- La repetición de una palabra que no es gramatical («CONTRATO CONTRATO») ya no se reporta.
- La concordancia de género con la ficha RENIEC («QUEDANDO ADVERTIDA» para un otorgante varón) queda fuera: la ficha no siempre trae el sexo legible.

## Verificación

- `tests/test_linguistico.py`: minúscula intercalada, acento grave, palabra repetida y formas válidas (siglas, «Nº», marcas, abreviaturas, topónimos y apellidos repetidos), todo con datos ficticios.
- `tests/test_anexo_omitido.py`: anexo ausente, anexo presente, párrafo suelto fuera del anexo, minuta sin anexo y dos anexos.
- `tests/test_expedientes_confrontacion.py`: la confrontación llama a `anexos_omitidos` y no a `revisar_parrafos`.
- `test_ortografia.py`: «OCUPACIÒN» ahora sale como «acento grave».
