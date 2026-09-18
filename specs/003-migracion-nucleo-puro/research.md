# Research: Migración del núcleo puro

## Decisiones

### Paquete común y adaptadores

- **Decisión**: colocar verificación, léxico y ortografía en `nucleo/`; dejar extracción de archivos/OCR y aprovisionamiento del diccionario en adaptadores.
- **Rationale**: responde a Clarifications y al principio II. Actualmente `verificar.py` y `lexico.py` importan `extraer.py`; `ortografia.py` descarga el diccionario y lee/escribe la lista de términos. Estos son los bordes de E/S que impiden que las reglas sean puras.
- **Alternativas consideradas**: mover todo el código a una capa nueva; descartada porque aumenta el diff y las reglas deben conservarse casi como están. Mantener todo junto; descartada porque deja E/S en el núcleo.

### Interfaces durante F3

- **Decisión**: adaptar los imports de `app.py` y `app_ortografia.py` y conservar ambas aplicaciones hasta paridad ERP en F4/F5. Mover `revisor_llm.py` y `bench_llm.py` a `experimental/`; el ERP no los importa.
- **Rationale**: respuesta aclarada por el usuario y principio I. Las pruebas de prosa existentes permanecen aisladas y sin llamadas a modelos.
- **Alternativas consideradas**: retirar Streamlit en F3; descartada porque no hay paridad ERP. Mantener la capa de prosa en el flujo productivo; descartada por la constitución.

### Comparación OCR

- **Decisión/evidencia**: se comparó localmente RapidOCR 3.4.3 con PP-OCRv4 ch y PP-OCRv5 latin (`use_cls=False`), usando modelos/diccionarios fijados por SHA-256. La tabla, el detalle de caracteres y la recomendación están abajo en "Investigación sintética de candidatos OCR". La página de modelos enumera latin PP-OCRv5 como familia que cubre español; no enumera un reconocedor `es` dedicado.
- **Alternativas consideradas**: actualizar RapidOCR directamente a una versión flotante; descartada porque no sería reproducible. Conservar v4 sin medir; no responde a la decisión solicitada. La medición no se ejecuta en CI ni con datos versionados.
- **Fuentes primarias**: [RapidOCR model list](https://rapidai.github.io/RapidOCRDocs/main/model_list/), [RapidOCR default model manifest](https://github.com/RapidAI/RapidOCR/blob/main/python/rapidocr/default_models.yaml).
- **Criterio de selección**: cambiar a v5 solo si `local_reference` produce 8 observaciones, las cinco salidas son idénticas, la escritura correcta produce cero observaciones y el test OCR sintético conserva todas las líneas y acentos/Ñ. Si falla un criterio, retener PP-OCRv4 y documentar la medición; el destino del PR #11 queda condicionado al resultado.

### Deuda técnica

- **Decisión**: revisar los diez IDs Sonar individualmente según `docs/deuda-f3.md`, priorizando tests sintéticos antes de cambios de comportamiento. Resolver cada hallazgo con cambio mínimo o registrar razón/riesgo residual por escrito. Revisar antlr4 con una instalación bloqueada de `setuptools` y `--no-build-isolation`, validar hash y registrar resultado. La llamada de `revisor_llm.py` debe pasar la API key fuera de la query URL.
- **Rationale**: el inventario y la propuesta para antlr4 ya están documentados; no se debe diluir el requisito por tratarse de un plan de migración.
- **Alternativas consideradas**: corregir olores de forma masiva o justificar todo sin revisar; ambas descartan evidencia por ID y dejan riesgos sin evaluación.

## Límites pendientes de ejecución

- El usuario ejecuta `local_reference` desde su entorno autorizado; nadie incorpora ni comunica contenido documental. La tarea debe devolver solo los agregados requeridos y el resultado de aprobación.
- Esta comparación cubre OCR sintético y no sustituye la medición privada `local_reference` ni autoriza seleccionar/cambiar el OCR predeterminado o actuar sobre el PR #11.
# Investigación sintética de candidatos OCR

Medición local ejecutada con `python -m pytest -o addopts= -m ocr_research -s
test_ocr_research.py`. El test crea las páginas en memoria; cada página contiene
85 palabras ficticias, acentos, ü, ñ/Ñ, DNI/partida ficticios y monto S/. Se
probaron Liberation Serif (serif) y Liberation Sans (sans), con página tamaño
A4 rasterizada a 200 y 300 DPI. Las líneas se cuentan agrupando las cajas OCR
por coordenada vertical (referencia: 8 líneas); las palabras son tokens exactos
en orden mediante coincidencias de secuencia; los caracteres á, é, í, ó, ú, ü,
ñ y sus formas mayúsculas coinciden respetando mayúsculas (referencia: 32).
Tiempo es una
llamada OCR por página, CPU local; no es una estimación de producción.

## Resultados

| Variante | Fuente | DPI | Líneas | Palabras exactas / 85 | Diacríticos y ñ exactos / 32 | Segundos/página |
|---|---|---:|---:|---:|---:|---:|
| PP-OCRv4 actual | Liberation Serif | 200 | 8/8 | 55 | 1 | 2.0726 |
| PP-OCRv4 actual | Liberation Serif | 300 | 8/8 | 56 | 3 | 1.5189 |
| PP-OCRv4 actual | Liberation Sans | 200 | 8/8 | 52 | 2 | 1.7008 |
| PP-OCRv4 actual | Liberation Sans | 300 | 5/8 | 32 | 1 | 2.0740 |
| PP-OCRv5 latin (`use_cls=False`) | Liberation Serif | 200 | 8/8 | 84 | 31 | 1.4311 |
| PP-OCRv5 latin (`use_cls=False`) | Liberation Serif | 300 | 8/8 | 84 | 31 | 1.3724 |
| PP-OCRv5 latin (`use_cls=False`) | Liberation Sans | 200 | 8/8 | 83 | 31 | 1.4232 |
| PP-OCRv5 latin (`use_cls=False`) | Liberation Sans | 300 | 8/8 | 82 | 31 | 1.3975 |

## Recursos fijados y diccionarios

Todos los hashes siguientes se validan antes de inicializar los modelos en el
test de investigación. Se comparte el detector v4 y el clasificador v4; así la
comparación aísla el reconocedor y los diccionarios.

| Recurso | SHA-256 | Ñ | ñ |
|---|---|---|---|
| Detector `ch_PP-OCRv4_det_infer.onnx` | `d2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9` | — | — |
| Clasificador `ch_ppocr_mobile_v2.0_cls_infer.onnx` | `e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c` | — | — |
| PP-OCRv4 `ch_PP-OCRv4_rec_infer.onnx` | `48fc40f24f6d2a207a2b1091d3437eb3cc3eb6b676dc3ef9c37384005483683b` | No | No |
| Diccionario v4 `ppocr_keys_v1.txt` | `28b2362ad4ab2dc38769aa72feb535e3a9ddb3fd2a7585a05920e6393b1dc7f7` | No | No |
| PP-OCRv5 latin `latin_PP-OCRv5_rec_mobile_infer.onnx` | `b20bd37c168a570f583afbc8cd7925603890efbcdc000a59e22c269d160b5f5a` | No | Sí |
| Diccionario v5 latin `ppocrv5_dict.txt` | `d1979e9f794c464c0d2e0b70a7fe14dd978e9dc644c0e71f14158cdf8342af1b` | No | Sí |

La ausencia en el diccionario hace imposible emitir literalmente ese carácter:
v4 no puede reconocer Ñ ni ñ; v5 latin admite ñ minúscula pero no Ñ mayúscula.
El catálogo RapidOCR incluye latin PP-OCRv5 (español entre los idiomas cubiertos)
pero no un reconocedor PP-OCRv5 `es` dedicado ni otro modelo PP-OCRv5 ONNX
listado que cubra español. Fuente del catálogo y compatibilidad: [RapidOCR model
list](https://rapidai.github.io/RapidOCRDocs/main/model_list/).

## Recomendación

PP-OCRv5 latin supera claramente a v4 en esta muestra: 82–84/85 palabras,
31/32 diacríticos con mayúsculas respetadas y 8/8 líneas en las cuatro páginas; v4 obtiene 32–56/85,
1–3/32 y baja a 5/8 líneas en sans a 300 DPI. Recomiendo mantener v5 latin como
candidato para la siguiente decisión, pero no declararlo apto para textos que
exijan conservar Ñ mayúscula: su diccionario no puede producirla. La
configuración OCR predeterminada no se modificó.
