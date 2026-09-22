# Deuda técnica para F3

## Cobertura de `experimental/`

La capa `experimental/` (`revisor_llm.py` y `bench_llm.py`) se mantiene bajo
análisis de SonarQube, incluyendo seguridad, bugs y secretos, pero queda fuera
del denominador de cobertura. La decisión del PR #17 (2026-09-19) responde a
que está fuera del ERP, no se despliega y sus pruebas son opt-in; por ello se
configura `sonar.coverage.exclusions=experimental/**` y la exclusión equivalente
en Coverage.py, sin usar `sonar.exclusions`.

## Limitación conocida de OCR

RapidOCR usa la metadata `character` incrustada en el ONNX latin v5 (502
caracteres, incluidos ñ, Ñ, Ú, Á e Í) e ignora `rec_keys_path`;
`ppocrv5_dict.txt` no se usa. PP-OCRv4 sí carece de ñ/Ñ. Una Ñ aislada a
veces se descarta: en cuatro intentos, una vez se leyó como N y tres veces se
descartó. En palabras (SEÑORA, NÚÑEZ, MUÑOZ, ESPAÑA, ÑANDÚ) se lee bien; si se
descarta dentro de un nombre, se genera una observación. T014 sigue siendo el
gate de la medición privada.

### Eñe significativa en la capa de regla

Desde F5, `nucleo.verificar.norm()` conserva `Ñ`/`ñ` como `Ñ` y sigue
ignorando las tildes de las vocales. Así, una eñe omitida en el borrador se
señala como diferencia de nombre y no se pierde por normalización. El riesgo
residual es un falso positivo cuando una foto de DNI hace que el OCR descarte
una eñe aislada: la fuente puede conservar la eñe y el texto extraído del
borrador no. Si aparece, debe diagnosticarse junto con la calidad del OCR y no
confundirse con un cambio de la regla. T014 sigue siendo el gate de la medición
privada.

### Eñe coherente en el núcleo

`nucleo.lexico.sin_tilde()` y `nucleo.ortografia.plano()` aplican ahora el
mismo criterio que `norm()`: las vocales pierden sus combinantes, pero la
virgulilla que sigue a `N`/`n` recompone `Ñ`/`ñ`. `TILDE_IMPOSIBLE` y
`ACENTO_CORRECTO` no incluyen la eñe como error ni la convierten. El vocabulario
léxico y las sugerencias ortográficas distinguen `MUÑOZ` de `MUNOZ`; la lista de
la casa conserva ambas formas si se reciben explícitamente. Las tres funciones
repiten deliberadamente el pequeño bucle porque `nucleo/` mantiene módulos
puros independientes; si la regla crece, conviene extraer una función común
de normalización en `nucleo` sin mezclar adaptadores.

La medición contra el expediente de referencia queda pendiente del usuario.
Debe ejecutarse desde el repositorio saneado, con los recursos privados
aprovisionados, exactamente en este orden:

```bash
python -m pytest -o addopts= -m local_reference --tb=no
```

### Apellidos compuestos y deduplicación de carátula

`nucleo.verificar.nombres()` conserva las partículas de `STOP` que aparecen
entre palabras del nombre y solo elimina ruido en sus extremos. El límite es de
7 palabras: cubre nombres con dos partículas compuestas sin ampliar más de lo
necesario la heurística de carátula. `catalogo()`, `correspondencia()` y
`revisar()` reciben así el nombre completo; la carátula registra una sola
observación por candidato repetido.

### Formularios de cliente en PDF

La capa de regla se diseñó para la prosa notarial, pero los documentos del
cliente suelen ser formularios con campos etiquetados. Esta ronda cubre esa
disposición de RENIEC en fuentes `.pdf`: `catalogo()` conserva la vía de prosa
(`nombres()`) y además intenta `nombre_reniec()`, uniendo los resultados en el
conjunto de nombres sin duplicarlos. Las imágenes mantienen su vía existente
de `RE_CUI` y `nombre_reniec()`.

Los demás formatos no se amplían todavía a la vía RENIEC: el hallazgo verificado
corresponde a formularios escaneados en PDF y no hay fixtures ficticios que
representen formularios en `.docx`, `.doc`, `.rtf`, `.odt`, `.xlsx`, `.txt` o
`.csv`; por ahora siguen usando la vía de prosa. Las partidas registrales y
otros formularios tampoco están cubiertos todavía.

`RE_DNI_DOC` captura únicamente números de exactamente 8 dígitos y exige que no
formen parte de una secuencia numérica mayor. `RE_CUI` conserva el formato de
las imágenes: 8 dígitos, guion y dígito verificador. Esto evita que partidas,
asientos o trámites numerados contaminen el diagnóstico de correspondencia.

Los diez code smells del análisis inicial de SonarCloud sobre `main` (`4cb625e`)
se registran para la migración del núcleo en F3; no se corrigen en F1.

| ID Sonar | Regla | Archivo | Función o alcance | Motivo breve |
|---|---|---|---|---|
| AaCzSzcyMhSFhiPLM0QS | python:S1481 | `app_ortografia.py` | `diccionario_residente` | Se descarta explícitamente el diccionario (`_`); la caché de `diccionario` conserva la residencia en RAM. |
| AaCzSzcyMhSFhiPLM0QR | python:S1192 | `app_ortografia.py` | bloque de curación | Constante `CASA` para la etiqueta repetida del control de interfaz. |
| AaCzSzcYMhSFhiPLM0QI | python:S9073 | `test_extraer.py` | `test_legacy_sin_libreoffice` | Aserción compuesta de privacidad del error. |
| AaCzSzcYMhSFhiPLM0QJ | python:S9073 | `test_extraer.py` | `test_cuadro_texto_docx` | Aserción compuesta sobre XML sintético. |
| AaCzSzcYMhSFhiPLM0QK | python:S9073 | `test_extraer.py` | `test_pdf_texto_y_tabla_docx` | Aserción compuesta sobre PDF sintético. |
| AaCzSzdRMhSFhiPLM0Qh | python:S9073 | `test_ortografia.py` | `test_ortografia` | Aserción compuesta de exclusión léxica. |
| AaCzSzZyMhSFhiPLM0QE | python:S8786 | `nucleo/verificar.py` | `RE_DNI_DOC`, `RE_NOMBRE` | Patrones lineales, sin cuantificadores anidados ambiguos; tests de entradas patológicas acotados a 0,5 s. La QE ampliada registra equivalencia con la regex previa y la decisión explícita de aceptar `D.N.I.`/`D.N.I`; `RE_NOMBRE` conserva el cuantificador lazy para no perder nombres sin coma. |
| AaCzSzZyMhSFhiPLM0QF | python:S7500 | `nucleo/verificar.py` | `correspondencia` | `set(RE_DNI_DOC.findall(d))` expresa directamente la conversión requerida. |
| AaCzSzZyMhSFhiPLM0QH | python:S3776 | `nucleo/verificar.py` | `revisar` | Se conserva la función como unidad de regla hasta F4: dividirla cambiaría el flujo medido; revisión prevista al introducir el servicio de confrontación. |
| AaCzSzZyMhSFhiPLM0QG | python:S1172 | `nucleo/verificar.py` | `revisar` | `umbral` se conserva en la firma transitoria para compatibilidad con el shim CLI y ambas apps; se eliminará al migrar esos llamadores en F4. |

## Riesgo residual de instalación

`antlr4-python3-runtime==4.9.3`, dependencia transitiva de `omegaconf`, solo se
publica como sdist. Aunque el sdist está fijado por hash, su aislamiento de
compilación instala `setuptools>=40.8.0` sin versión fija ni hash para ejecutar
el código de construcción. En F3 se revisará instalar primero un `setuptools`
bloqueado y luego antlr4 con `--no-build-isolation`; F1 acepta el riesgo y no
cambia la instalación del CI.

## Justificación de CLI local en F1

`pythonsecurity:S8705` permanece aplicable por diseño a `_legacy` y `_soffice`:
son adaptadores locales que invocan ejecutables configurados por el proyecto con
una lista de argumentos y sin shell. La ruta del documento se resuelve con
`Path.resolve(strict=True)` y se valida como archivo regular con sufijo de
`LEGACY` antes de llegar al subprocess; las opciones y formatos no provienen del
documento. Esta justificación se revisará si una interfaz futura permite
configurar el ejecutable o el formato desde una entrada no confiable.

## Aprovisionamiento offline de modelos para F8

En el equipo conectado, aprovisionar los dos modelos verificados en `~/.cache/notaria-ocr/models/`. Copiar ese directorio al servidor sin red, conservando nombres y estructura; en el servidor comprobarlo antes de arrancar:

```bash
cd ~/.cache/notaria-ocr/models
sha256sum -c - <<'EOF'
d2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9  ch_PP-OCRv4_det_infer.onnx
b20bd37c168a570f583afbc8cd7925603890efbcdc000a59e22c269d160b5f5a  latin_PP-OCRv5_rec_mobile_infer.onnx
EOF
```

## Cierre F3 por ID

Los diez IDs fueron revisados en la rama F3. Los cuatro olores de aserciones
compuestas (`AaCzSzcYMhSFhiPLM0QI`, `AaCzSzcYMhSFhiPLM0QJ`,
`AaCzSzcYMhSFhiPLM0QK`, `AaCzSzdRMhSFhiPLM0Qh`) quedaron con aserciones
separadas. `AaCzSzcyMhSFhiPLM0QS` se resolvió descartando el valor no usado y
`AaCzSzcyMhSFhiPLM0QR` con la constante `CASA`.

Los cuatro IDs del verificador (`AaCzSzZyMhSFhiPLM0QE`,
`AaCzSzZyMhSFhiPLM0QF`, `AaCzSzZyMhSFhiPLM0QH`, `AaCzSzZyMhSFhiPLM0QG`)
se resolvieron o justificaron individualmente: la regex ahora es lineal y se
probó contra una entrada patológica, la comprensión usa `set()` y QH/QG tienen
justificación de compatibilidad y fase concreta.

La instalación aislada de `antlr4-python3-runtime==4.9.3` fue validada en un
entorno virtual temporal con `setuptools==84.0.0` fijado por hash y
`--no-build-isolation`; importó correctamente `antlr4`. El riesgo residual es
que el sdist conserva su propia metadata de build y el CI instala con
aislamiento; no se cambian los locks porque la instalación reproducible pasó.
