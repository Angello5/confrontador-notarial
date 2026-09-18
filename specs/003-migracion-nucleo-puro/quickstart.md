# Validación local: Migración del núcleo puro

Esta guía valida el diseño de F3 sin requerir expedientes reales en el repositorio.

## Prerrequisitos

- Python 3.13 y entorno con dependencias fijadas de `requirements.txt` y `requirements-dev.txt`.
- Recursos públicos OCR/diccionario con versiones y hashes de la guía F1.
- LibreOffice en Linux para pruebas sintéticas `.doc`/`.rtf`.
- Solo para la medición privada: referencia autorizada fuera del repositorio y permiso de la persona responsable. No copiarla, nombrar sus documentos ni incluir su ruta en commits/logs.

## Suite sintética predeterminada

```bash
python scripts/generar_fixtures.py
python -m pytest --cov --cov-report=term --cov-report=xml:coverage.xml
```

**Esperado**: pasan fixtures y pruebas ficticias de cada capa; `local_reference` no se selecciona por defecto. La suite no accede a la referencia privada.

## Medición privada de comportamiento

Ejecutar solo en el entorno autorizado, fuera de CI y con la referencia fuera del repositorio. No añadir contenido/ruta a archivos versionados ni guardar la salida de pytest.

```bash
test -n "$EXPEDIENTES_REFERENCIA_DIR" && python -m pytest -o addopts= -m local_reference --tb=no
```

**Esperado**: 8 observaciones en el borrador observado, 0 observaciones en la escritura correcta y cinco corridas idénticas. La prueba informa un resultado agregado sin documento, fragmentos, rutas ni credenciales.

## Comparación OCR requerida para evaluar PP-OCRv5

1. Validar hashes de los modelos PP-OCRv4 ch y del candidato PP-OCRv5 latin, el diccionario y las versiones de RapidOCR/onnxruntime. El candidato v5 usa `use_cls=False`; no dejar modelos descargados automáticamente sin pin.
2. Ejecutar los mismos recursos ficticios OCR con ambas configuraciones y comparar texto por salida; registrar conteos agregados de líneas y conservación de acentos/Ñ, sin guardar imágenes o texto real.
3. La persona responsable ejecuta el test `local_reference` por separado con cada configuración en el entorno autorizado y devuelve solo: 8 observaciones, cero en escritura correcta y cinco salidas idénticas (sí/no por condición).
4. Cambiar a PP-OCRv5 latin solo si todas las condiciones anteriores pasan. Si alguna falla o la medición no puede ejecutarse, retener PP-OCRv4 y documentar el motivo agregado.

**Esperado al aprobar**: mismos resultados deterministas requeridos, cero observaciones en escritura correcta, cinco salidas iguales, sin pérdida de líneas/acentos/Ñ y hashes validados. La decisión sobre el PR #11 sigue esa evidencia; no se modifica el PR durante estas pruebas.

## Gates previos a completar F3

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest --cov --cov-report=term --cov-report=xml:coverage.xml
python -m pip_audit --strict -r requirements.txt -r requirements-dev.txt
```

El Quality Gate de SonarQube y la revisión de secretos corresponden al CI del PR; la medición privada no se ejecuta en CI. Revisar los 10 IDs de `docs/deuda-f3.md` y documentar resolución o justificación por ID.
