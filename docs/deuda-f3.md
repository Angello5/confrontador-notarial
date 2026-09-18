# Deuda técnica para F3

Los diez code smells del análisis inicial de SonarCloud sobre `main` (`4cb625e`)
se registran para la migración del núcleo en F3; no se corrigen en F1.

| Regla | Archivo | Función o alcance | Motivo breve |
|---|---|---|---|
| python:S1481 | `app_ortografia.py` | `diccionario_residente` | Variable devuelta por una API existente que no se usa. |
| python:S1192 | `app_ortografia.py` | bloque de curación | Literal de interfaz repetido tres veces. |
| python:S9073 | `test_extraer.py` | `test_legacy_sin_libreoffice` | Aserción compuesta de privacidad del error. |
| python:S9073 | `test_extraer.py` | `test_cuadro_texto_docx` | Aserción compuesta sobre XML sintético. |
| python:S9073 | `test_extraer.py` | `test_pdf_texto_y_tabla_docx` | Aserción compuesta sobre PDF sintético. |
| python:S9073 | `test_ortografia.py` | `test_ortografia` | Aserción compuesta de exclusión léxica. |
| python:S8786 | `verificar.py` | `RE_DNI_DOC` | Expresión regular existente con posible backtracking. |
| python:S7500 | `verificar.py` | `correspondencia` | Comprensión redundante al construir un conjunto. |
| python:S3776 | `verificar.py` | `revisar` | Complejidad cognitiva 22 frente al máximo 15. |
| python:S1172 | `verificar.py` | `revisar` | Parámetro `umbral` no utilizado. |

## Justificación de CLI local en F1

`pythonsecurity:S8705` permanece aplicable por diseño a `_legacy` y `_soffice`:
son adaptadores locales que invocan ejecutables configurados por el proyecto con
una lista de argumentos y sin shell. La ruta del documento se resuelve con
`Path.resolve(strict=True)` y se valida como archivo regular con sufijo de
`LEGACY` antes de llegar al subprocess; las opciones y formatos no provienen del
documento. Esta justificación se revisará si una interfaz futura permite
configurar el ejecutable o el formato desde una entrada no confiable.
