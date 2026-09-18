# Modelo de datos: Migración del núcleo puro

F3 no persiste entidades y no añade tablas. Las estructuras siguientes son valores en memoria; solo el adaptador puede leer/escribir documentos y recursos locales.

## Entrada de confrontación

- **Contenido**: texto o estructuras ficticias/principales que recibe una función del núcleo.
- **Relación**: se entrega a una o más capas; no contiene rutas de archivos, clientes HTTP ni objetos de OCR.
- **Validación**: los tests versionados contienen exclusivamente valores ficticios.

## Resultado de capa

- **Contenido**: hallazgos deterministas devueltos por extracción de campos, verificación, léxico u ortografía.
- **Relación**: corresponde a una entrada y una capa; la interfaz o el proceso consumidor decide cómo presentarlo.
- **Validación**: para una misma entrada, la salida observable es idéntica entre ejecuciones.

## Configuración de recursos

- **Contenido**: identificador de motor, versión, modelo, origen fijado y SHA-256 para OCR/diccionario.
- **Relación**: `adaptadores.diccionario` carga los recursos locales y los entrega como diccionario, lemas y términos aceptados a `nucleo.ortografia.revisar`; la función pura no accede a archivos ni red.
- **Validación**: el hash debe coincidir antes del uso; faltantes o discrepancias causan error explícito.

## Informe agregado de medición

- **Contenido permitido**: nombre de configuración (actual/candidata), ocho observaciones o conteo obtenido, conteo de falsos positivos, conteo de observaciones en escritura correcta, igualdad de cinco corridas y resultado del test sintético (líneas/acentos/Ñ preservados).
- **Contenido prohibido**: texto extraído, identidad, rutas privadas, imágenes, partes de observaciones, tokens o secretos.
- **Relación**: resume una medición local por configuración y fundamenta mantener PP-OCRv4 o aceptar PP-OCRv5.
- **Validación**: solo se registra el agregado; los documentos viven fuera del repositorio.
