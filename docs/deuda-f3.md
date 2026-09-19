# Deuda técnica para F3

## Limitación conocida de OCR

RapidOCR usa la metadata `character` incrustada en el ONNX latin v5 (502
caracteres, incluidos ñ, Ñ, Ú, Á e Í) e ignora `rec_keys_path`;
`ppocrv5_dict.txt` no se usa. PP-OCRv4 sí carece de ñ/Ñ. Una Ñ aislada a
veces se descarta: en cuatro intentos, una vez se leyó como N y tres veces se
descartó. En palabras (SEÑORA, NÚÑEZ, MUÑOZ, ESPAÑA, ÑANDÚ) se lee bien; si se
descarta dentro de un nombre, se genera una observación. T014 sigue siendo el
gate de la medición privada.

Los diez code smells del análisis inicial de SonarCloud sobre `main` (`4cb625e`)
se registran para la migración del núcleo en F3; no se corrigen en F1.

| ID Sonar | Regla | Archivo | Función o alcance | Motivo breve |
|---|---|---|---|---|
| AaCzSzcyMhSFhiPLM0QS | python:S1481 | `app_ortografia.py` | `diccionario_residente` | Variable devuelta por una API existente que no se usa. |
| AaCzSzcyMhSFhiPLM0QR | python:S1192 | `app_ortografia.py` | bloque de curación | Literal de interfaz repetido tres veces. |
| AaCzSzcYMhSFhiPLM0QI | python:S9073 | `test_extraer.py` | `test_legacy_sin_libreoffice` | Aserción compuesta de privacidad del error. |
| AaCzSzcYMhSFhiPLM0QJ | python:S9073 | `test_extraer.py` | `test_cuadro_texto_docx` | Aserción compuesta sobre XML sintético. |
| AaCzSzcYMhSFhiPLM0QK | python:S9073 | `test_extraer.py` | `test_pdf_texto_y_tabla_docx` | Aserción compuesta sobre PDF sintético. |
| AaCzSzdRMhSFhiPLM0Qh | python:S9073 | `test_ortografia.py` | `test_ortografia` | Aserción compuesta de exclusión léxica. |
| AaCzSzZyMhSFhiPLM0QE | python:S8786 | `verificar.py` | `RE_DNI_DOC` | Expresión regular existente con posible backtracking. |
| AaCzSzZyMhSFhiPLM0QF | python:S7500 | `verificar.py` | `correspondencia` | Comprensión redundante al construir un conjunto. |
| AaCzSzZyMhSFhiPLM0QH | python:S3776 | `verificar.py` | `revisar` | Complejidad cognitiva 22 frente al máximo 15. |
| AaCzSzZyMhSFhiPLM0QG | python:S1172 | `verificar.py` | `revisar` | Parámetro `umbral` no utilizado. |

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
separadas. `AaCzSzcyMhSFhiPLM0QS` corresponde al valor de la API de caché de
Streamlit que se consume como métrica; `AaCzSzcyMhSFhiPLM0QR` queda
justificado como literal deliberado de interfaz, sin exclusión global.

Los cuatro IDs del verificador (`AaCzSzZyMhSFhiPLM0QE`,
`AaCzSzZyMhSFhiPLM0QF`, `AaCzSzZyMhSFhiPLM0QH`, `AaCzSzZyMhSFhiPLM0QG`)
apuntaban al módulo legado `verificar.py`; la lógica fue trasladada a
`nucleo/verificar.py` sin cambiar la regla, y el shim ya no contiene esas
expresiones. Se conserva esta justificación por ID para evitar una exclusión
global de reglas.

La instalación aislada de `antlr4-python3-runtime==4.9.3` fue validada en un
entorno virtual temporal con `setuptools==84.0.0` fijado por hash y
`--no-build-isolation`; importó correctamente `antlr4`. El riesgo residual es
que el sdist conserva su propia metadata de build y el CI instala con
aislamiento; no se cambian los locks porque la instalación reproducible pasó.
