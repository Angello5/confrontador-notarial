# Benchmark OCR experimental

Esta prueba usa el mismo núcleo vigente de `nucleo.verificar` que usa el
confrontador. No copia ni reemplaza `adaptadores/extraccion.py`: los adaptadores
experimentales producen texto por página y el catálogo actual se encarga de
asociar personas, documentos, procedencias y campos.

## Ejecución

Para usar la interfaz, instala estas dependencias y Streamlit en un entorno
Python aparte del ERP (Streamlit exige `pillow<13` y el ERP usa pillow 13):

```bash
python -m pip install -r experimental/requirements-ocr-benchmark.txt streamlit
streamlit run experimental/app_ocr_benchmark.py --server.port 8504
```

La interfaz acepta varios PDF o imágenes en una sola selección. Cada documento
se procesa por separado para conservar su nombre y sus resultados. La referencia puede ser un archivo Word (`.docx`, `.doc` o `.rtf`) o texto
(`.txt`/`.md`). Se extrae una vez y se compara contra cada documento y cada
motor seleccionado. La tabla muestra el archivo de referencia usado en cada
fila, CER, WER, precisión de caracteres y precisión de palabras; CER/WER igual a
cero y precisión igual a 100% significan coincidencia exacta. Si se comparan
varios documentos, el Word debe contener el texto esperado para esa comparación.
El benchmark CPU desactiva la ruta OneDNN/PIR de PaddleX que es incompatible
con algunas combinaciones de PaddlePaddle 3.x; esto prioriza una comparación
reproducible sobre la aceleración específica de ese backend. Los modelos de
PaddleOCR se descargan la primera vez que se inicializa cada motor; los
documentos de prueba deben ser ficticios o estar autorizados para el entorno
local.

## Qué compara

- **PaddleOCR v4**: detector `PP-OCRv4_mobile_det` con el reconocedor latino
  disponible `latin_PP-OCRv5_mobile_rec`. No es una comparación v4 completa:
  la API actual de PaddleOCR no ofrece un reconocedor español/latino v4.
- **PaddleOCR v5**: `PP-OCRv5_mobile_det` + `latin_PP-OCRv5_mobile_rec`.
- **PaddleOCR v6**: modelos multilingües `PP-OCRv6_medium_det` y
  `PP-OCRv6_medium_rec`, que cubren lenguas de escritura latina.
- **LiteParse**: parser local con Tesseract configurado con idioma `spa`.

Para que el tiempo sea comparable, un PDF se rasteriza a 200 DPI y cada motor
recibe las mismas páginas. La tabla muestra preparación, procesamiento, tiempo
total, caracteres, personas, DNI, partidas y montos detectados por el núcleo.
Si se sube una referencia `.docx`, `.doc`, `.rtf`, `.txt` o `.md`, también calcula CER y WER.

## Verificación sin modelos

La suite experimental ejecuta el contrato con runners falsos, sin red ni
modelos:

```bash
python -m pytest -q test_ocr_benchmark.py -m ocr_research
```

El estado de cada dependencia se muestra en la barra lateral. Si un motor no
está instalado o no puede cargar sus modelos, se registra como error sin ocultar
los resultados de los otros motores.
