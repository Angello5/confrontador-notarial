# Feature Specification: F27 · Montos por posición, con moneda y concepto

**Feature Branch**: `Angello5/f27-montos-contexto`

**Created**: 2026-09-28

**Status**: Draft

**Input**: Anexo A.3 d) exige verificar los montos «sobre cada aparición del dato en el borrador, y no sobre su mera existencia». Anexo B P-02: 100 % de datos alterados detectados con su valor correcto construido desde la fuente. Medición del revisor en 10 expedientes reales: `RE_MONTO` solo reconoce `S/ 9.99` (11 importes en dólares sin verificar; en 2 expedientes el único importe es en dólares); la verificación es por conjunto, así que una cuota con el importe de otra cuota o un precio sustituido por otro importe válido del documento no se detecta (2 observaciones MONTO en 10 expedientes); la observación no dice el concepto ni el documento fuente.

## Principio

**Cada importe del borrador se compara con el importe que ocupa la misma posición en la minuta.** El conjunto de importes de las fuentes solo decide cuando el importe no tiene par en la minuta.

## Clarifications

### Session 2026-09-28

- Q: ¿Qué es un importe? → A: una cifra con dos decimales (`\d[\d,]*\.\d{2}`) con moneda antes (`S/`, `S/.`, `US$`, `$`, `SOLES`, `DOLARES`, `DOLARES AMERICANOS`) o después (`SOLES`, `DOLARES`, `DOLARES AMERICANOS`, `US$`). El valor comparable es (moneda, importe): `S/ 100.00` y `US$ 100.00` son distintos.
- Q: ¿`$` sin `US`? → A: dólares americanos. [NEEDS CLARIFICATION: confirmar con el propietario; opción por defecto implementada.]
- Q: ¿Cómo se escribe el valor? → A: soles como hasta ahora, solo la cifra (`«100.00»`), para mantener el formato de mensaje; dólares con prefijo (`«US$ 100.00»`).
- Q: ¿Qué es la posición? → A: cada línea del borrador con importes se empareja con una línea de la minuta: (1) fila de cronograma (≥ 2 importes y rótulo de número de cuota o fecha `dd/mm/aaaa`) → la fila de la minuta con el mismo rótulo; (2) si no, párrafo de más de 80 caracteres (como `parrafos()`) → el párrafo de la minuta con importes de mayor `fuzz.partial_ratio`, con el mismo umbral que `revisar_parrafos`. Empate: el primero.
- Q: ¿Y si el par tiene distinto número de importes? → A: no se compara por posición; se aplica la regla de conjunto. Así una inserción no desplaza toda la secuencia. [NEEDS CLARIFICATION: confirmar; opción por defecto implementada.]
- Q: ¿Qué es el concepto? → A: en una fila de cronograma, `CUOTA <n>` o `CUOTA DEL <fecha>`; en un párrafo, hasta 6 palabras previas al importe en la minuta, sin contar otros importes.
- Q: (Ronda 2) ¿Por qué no se detectaba nada en borradores reales? → A: el lector de `.docx` cortaba por `</w:p>` y cada celda de tabla salía en su propia línea, así que ninguna línea era una fila de cronograma. Ahora, dentro de `<w:tbl>`, cada fila `<w:tr>` es una línea con sus celdas separadas por dos espacios (convención de `ocr_lineas`); los párrafos de una celda se unen con un espacio, las celdas vacías se omiten y una tabla anidada se aplana dentro de su celda. Fuera de tablas no cambia nada.
- Q: (Ronda 2) ¿Qué pasa con los textos ya extraídos? → A: `version_extractor()` incluye `_FORMATO_TEXTO` (sube a 2), así que la próxima extracción no reutiliza el texto antiguo. Los expedientes ya cargados conservan su texto antiguo hasta volver a extraerlo con `manage.py reextraer_expediente <codigo>`. No se sube `_FORMATO_CACHE`: la caché de OCR guarda texto de PDF e imágenes, que no cambia, y subirla obligaría a repetir todo el OCR.
- Q: (Ronda 2) ¿De dónde sale el archivo para volver a extraer? → A: del temporal si aún existe; si no, del borrador original conservado por F21 (`services.ruta_original`), que aún no está en esta rama: el comando lo usa cuando exista. Se copia a un temporal nuevo porque el worker borra el temporal al terminar. Sin archivo, el comando lo informa y no toca el documento.
- Q: (Ronda 2) ¿Una celda de cronograma sin moneda es importe? → A: no; se mantiene la definición de importe de la primera clarificación. [NEEDS CLARIFICATION: si los cronogramas reales traen la cifra sin moneda en cada celda, habría que aceptar la moneda de la cabecera de la columna.]
- Q: Carga útil de corrección de F21 → A: F21 no está en `main`; no se toca. La observación posicional usa el mismo formato «hallado» debe decir «esperado», que F21 ya sabe leer.

## Requirements *(mandatory)*

- **FR-001 (moneda)**: `RE_MONTO` reconoce las monedas de la clarificación, antes o después de la cifra. `catalogo()`, `montos_exigibles()` y `revisar()` usan el valor (moneda, importe) según la clarificación.
- **FR-002 (posición)**: `revisar(..., minutas=None)` recibe los textos de la minuta como `{archivo: texto}`. Para cada importe del borrador con par en la minuta (clarificación), si difiere del importe en la misma posición: `[MONTO] «hallado» debe decir «esperado»   (concepto: <concepto>; fuente: <archivo>, p. <n>)`. Si coincide, no hay observación. El esperado de una observación posicional no se repite como `FALTA`.
- **FR-003 (sin par)**: sin par, o con `minutas=None`, regla actual: importe fuera de las fuentes → `debe decir` por similitud o `no coincide con ninguna fuente`.
- **FR-004 (vista)**: `services.py` pasa la minuta a `revisar()` y añade al dict de la observación las claves `concepto` y `fuente` (vacías si no hay), sin cambiar las existentes.
- **FR-005**: `FALTA`, `NOMBRE`, `DNI`, `RUC`, `PARTIDA`, `DIRECCION`, `NUMERO_EN_LETRAS` y `PARRAFO` sin cambios. Núcleo puro y determinista; sin dependencias ni migraciones. Solo datos ficticios.

- **FR-006 (tablas .docx)**: `extraccion._docx` emite cada fila de tabla como una línea según la clarificación de la ronda 2; el texto fuera de tablas es idéntico al de antes.
- **FR-007 (reextracción)**: `version_extractor()` cambia con el formato del texto; `manage.py reextraer_expediente <codigo>` vuelve a poner en cola (`PENDIENTE`) los documentos del expediente con archivo disponible y lista los que no lo tienen, sin tocarlos.

## Success Criteria *(mandatory)*

- **SC-001**: En los 10 expedientes del revisor, se verifican los importes en dólares y se detecta una cuota intercambiada o un precio sustituido por otro importe válido del documento (medición del revisor, fuera del repositorio).
- **SC-002**: Paridad literal de `revisar()` sobre los fixtures ficticios, salvo las observaciones MONTO nuevas.
