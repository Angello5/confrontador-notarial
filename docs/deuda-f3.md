# Deuda técnica para F3

## Limitación conocida de OCR

PP-OCRv5 latin no tiene Ñ mayúscula en su diccionario, por lo que no puede
emitirla literalmente. La confrontación aplica NFKD y mayúsculas antes de
comparar, así que Ñ se reduce a N en ambos textos; esta limitación queda
aceptada para ese uso. La medición privada T014 sigue siendo el gate para
completar la adopción.

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
