# F30 · Reglas adicionales de la escritura

**Fecha**: 2026-10-02  
**Estado**: implementado en el núcleo; cobertura con datos ficticios.  
**Alcance**: `nucleo/verificar.py`, `nucleo/correccion.py`, catálogo de reglas y pruebas puras.

## Comportamiento implementado

- **Área**: compara el área expresada en letras con la cifra en m², en cualquiera de los dos órdenes. Acepta `M2`, `MT2`, `MTS2` y `METROS CUADRADOS`, enteros y hasta dos decimales. En letras acepta centésimas (`Y 50/100`, `PUNTO CERO CINCO`) y decímetros cuadrados (`CON CINCUENTA DECIMETROS CUADRADOS`). La discrepancia produce `[AREA]`.
- **Número en letras**: compara cifras parentéticas con su expresión en letras, incluidos importes con moneda, decimales y porcentajes. Produce `[NUMERO_EN_LETRAS]` cuando difieren.
- **Correlativos**: lee rótulos de cláusula al comienzo de una línea (`PRIMERA`, `SEGUNDA`, etc.) e incisos de letra, número o romano. Señala saltos y repeticiones con `[CORRELATIVO]`; un `1` inicia una serie y cada cláusula reinicia sus incisos. Las cláusulas femeninas y masculinas son series aparte, pero un ordinal que continúa la numeración general no es salto (`SEGUNDO:` seguido de `TERCERA.-`); si falta uno, el «debe decir» sigue esa numeración. En el `.docx`, el salto de línea manual (`<w:br/>`) separa líneas como un párrafo, para que el inciso que lo sigue se lea al inicio de línea.
- **Copropiedad**: en una misma oración que mencione copropiedad, acciones y derechos, cuota ideal o participación, suma porcentajes. Señala con `[COPROPIEDAD]` un total que no llegue a 100 % ni a un múltiplo de 100 %. Admite tolerancia de una centésima por cuota para redondeos y reconoce una cuota que equivale a la suma de las otras.
- **Importes por concepto**: extrae precio, tasación, valor comercial, valor de realización e hipoteca de fuente y borrador. Si el concepto existe en las fuentes y su cifra difiere, emite `[MONTO]` con el concepto. Esta comparación también funciona cuando la cifra carece de símbolo monetario. No repite una observación de `[MONTO]` ya emitida por la comparación previa. La hipoteca aporta su monto solo con la fórmula «hasta por» o con el rótulo «monto del gravamen» o «monto de la hipoteca». Levantarla, cancelarla o la penalidad por no levantarla la nombran sin dar su monto. Esta corrección es del 2026-10-05, con catálogo `2026.10.05-1`, y se hizo porque un pago de cancelación se comparaba con la penalidad diaria.
- **Datos registrales**: extrae zona registral, tipo de registro, oficina registral y provincia. Valida el número de zona (I–XIV) y su sede. Cuando las fuentes contienen un único valor de zona o registro, propone ese valor. Para oficina y provincia propone un nombre de fuente solo si la similitud llega a 80 %. Reconoce nombres con artículo inicial, como `PROVINCIA DE LA CONVENCION`.

Las reglas están catalogadas en `nucleo/catalogo_reglas.toml` con versión `2026.10.02-2`: `AREA` y `DATO_REGISTRAL` tienen severidad ALTA; `CORRELATIVO` y `COPROPIEDAD`, MEDIA. Los hallazgos de área, correlativo, copropiedad y número en letras no generan reemplazo automático: su «debe decir» expresa una cifra o una secuencia esperada, sin determinar qué tramo jurídico corresponde cambiar. La corrección de un dato registral solo se ofrece cuando el valor propuesto aparece en una fuente.

## Límites actuales

- Las reglas de área y número en letras necesitan los formatos de cifra y unidad indicados; no interpretan cualquier redacción en prosa ni validan la medida contra una fuente.
- Los correlativos deben aparecer al inicio de línea y con un separador (`:`, `.`, `.-`, `-` o `)`). Tras `.-` y `)` el espacio es opcional (`B.-SUSCRIBIR`); tras `.` y `-` se exige, para no confundir decimales ni siglas. No se interpreta la jerarquía de incisos anidados.
- La suma de cuotas se hace dentro de una sola oración y línea. Si las cuotas están repartidas en varias oraciones, no se comparan. Las frases `CADA UNO` y `CADA UNA` se omiten por ambigüedad.
- La comparación de importes por concepto usa la cifra con dos decimales y el concepto cercano dentro de la misma oración; no distingue varias obligaciones que compartan un concepto.
- La provincia puede describir el bien o la oficina. El extractor toma el nombre que sigue a `PROVINCIA DE` o `PROVINCIA:`; una provincia de borrador muy distinta de las fuentes no se señala para evitar confundir otros lugares mencionados en la escritura.
- El catálogo de zonas y sedes es una lista incorporada al código. La validación y los umbrales son reglas heurísticas; se requiere evaluación con documentos de la notaría antes de medir sensibilidad y falsos positivos en expedientes reales.

## Verificación

`tests/test_reglas_f30.py` usa textos inventados para cubrir diferencias y coincidencias de área, número en letras, secuencias, cuotas, precio y datos registrales, además de la exclusión de correcciones automáticas ambiguas. `tests/test_nucleo_puro.py` lee los archivos del núcleo explícitamente como UTF-8 para que la prueba de pureza sea reproducible en Windows sin ajustar `PYTHONUTF8`.
