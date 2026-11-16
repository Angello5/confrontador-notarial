# Research · F76 Lectura rápida de escaneos

Sin `[NEEDS CLARIFICATION]` en la spec. Las decisiones salen del código y de las mediciones del 2026-11-16 (`docs/mediciones-ocr.md`).

## R1. Motor de ejecución

- **Decision**: OpenVINO a través de RapidOCR (`Det.engine_type` y `Rec.engine_type`), leyendo los mismos archivos `.onnx` ya fijados por SHA-256. Variable `OCR_MOTOR` con valores `openvino` (por defecto) y `onnxruntime`.
- **Rationale**: texto idéntico en 18 páginas reales y entre 2 y 6 veces más páginas por minuto. El Xeon Bronze 3204 tiene AVX-512, que OpenVINO aprovecha sin configuración.
- **Alternatives considered**: ONNX Runtime con más hilos (apenas mejora); modelos cuantizados a 8 bits (cambian el texto: fuera de alcance); OCR fuera del servidor (prohibido por el principio VI).

## R2. Reparto de páginas

- **Decision**: `concurrent.futures.ProcessPoolExecutor` creado una vez por proceso del worker, con `OCR_PROCESOS` procesos. Cada tarea lleva la ruta del archivo y el número de página; el proceso de lectura abre el PDF, rasteriza la página y ejecuta `ocr_informe` completo, relecturas incluidas. El proceso principal decide qué páginas son escaneadas, recoge los informes por índice y aplica la comparación con la capa de texto dudosa, como hoy.
- **Rationale**: cada página ya se lee de forma independiente; el orden se conserva por índice. Los procesos de lectura solo importan el adaptador, no Django.
- **Alternatives considered**: hilos (el motor escala mal con hilos); varios workers por documento (no aceleran un PDF grande y multiplican el riesgo del tiempo límite); enviar la imagen ya rasterizada (copia decenas de MB entre procesos).
- Con `OCR_PROCESOS=1` no se crea ningún grupo de procesos: la lectura es en serie, como hoy.

## R3. Hilos por proceso

- **Decision**: `OCR_HILOS` fija los hilos del motor en cada proceso (`inference_num_threads` en OpenVINO, `intra_op_num_threads` en ONNX Runtime). Por defecto 1.
- **Rationale**: sin fijarlos, cada proceso pide todos los núcleos y se estorban: una página llegó a tardar 37 s dentro de su proceso. El servidor no tiene hilos lógicos: 3 procesos de 1 hilo ocupan exactamente 3 núcleos.

## R4. Identidad de la lectura

- **Decision**: `version_extractor()` añade `"motor"` a su identidad solo cuando no es `onnxruntime`, junto con la versión de `openvino`. `OCR_PROCESOS` y `OCR_HILOS` no entran.
- **Rationale**: con el motor actual la llave es la de antes (SC-005) y la caché existente sigue valiendo; con OpenVINO la caché se separa por construcción, como exige el principio IV. El número de procesos no cambia el texto.

## R5. Tiempo límite por avance

- **Decision**: `leer_con_calidad(ruta, avance=None)` llama a `avance()` al terminar cada página. `services._procesar_fila` pasa una función que actualiza `Documento.procesando_el`, como mucho una vez cada 30 s. `recuperar_documentos_vencidos` no cambia: sigue comparando `procesando_el` con el límite.
- **Rationale**: el campo ya existe y ya gobierna la recuperación; pasa a significar «último avance». Sin migración.
- **Alternatives considered**: subir el límite (un documento colgado tardaría más en recuperarse); un campo nuevo (no aporta nada).

## R6. Prioridad de la cola

- **Decision**: `tomar_pendiente` ordena por un `Case` (borrador y minuta primero) y después por `id`.
- **Rationale**: un cambio pequeño en la consulta existente; conserva `select_for_update(skip_locked=True)`.
- Los recaudos no quedan sin atender: borradores y minutas son pocos y cortos, y la cola se vacía entre vueltas.

## R7. Fallos

- **Decision**: una excepción en un proceso de lectura se propaga al principal y el documento termina en «Error» por el camino actual, sin texto parcial. Si un proceso muere, el grupo se descarta y se crea de nuevo para el siguiente documento.
- **Decision**: al arrancar, `procesar_documentos` carga el motor configurado; si falta `openvino` o un modelo, se detiene con un mensaje claro antes de tomar documentos.

## R8. Memoria y convivencia

- Cada proceso carga sus modelos: unos 1,7 GB con ONNX Runtime (F33). Con OpenVINO no está medido; la medición del servidor lo fija y actualiza los límites de F8.
- La capa de sentido corre en el proceso principal después de leer, no a la vez, así que sus 3 hilos no se suman a los de la lectura.
- Se documenta un solo worker: con dos, los procesos de lectura se duplican.

## R9. Medición en el servidor

- **Decision**: `scripts/medir_lectura_paralela.py` genera escaneos ficticios (reutiliza el generador de `scripts/medir_tiempos_ingesta.py`), lee cada configuración y entrega páginas por minuto, memoria máxima y si el texto y los avisos coinciden con la lectura en serie del motor actual.
- La muestra privada se mide con el mismo script apuntando a una carpeta fuera del repositorio; solo deja recuentos.
