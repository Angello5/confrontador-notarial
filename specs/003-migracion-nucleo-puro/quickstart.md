# Validación local: Migración del núcleo puro

Esta guía valida el diseño de F3 sin requerir expedientes reales en el repositorio.

## Prerrequisitos

- Python 3.13 y entorno con dependencias fijadas de `requirements.txt` y `requirements-dev.txt`.
- Paquetes Python OCR fijados con hashes en `requirements.txt` (RapidOCR/onnxruntime). Los hashes SHA-256 de modelos OCR y del diccionario `es_PE` son recursos externos y se mantienen en el paso/manifiesto `Verify public test resources` del CI y en esta guía, nunca en `requirements*.txt`.
- LibreOffice en Linux para pruebas sintéticas `.doc`/`.rtf`.
- Solo para la medición privada: referencia autorizada fuera del repositorio y permiso de la persona responsable. No copiarla, nombrar sus documentos ni incluir su ruta en commits/logs.

## Suite sintética predeterminada

```bash
python scripts/generar_fixtures.py
python -m pytest --cov --cov-report=term --cov-report=xml:coverage.xml
```

**Esperado**: pasan fixtures y pruebas ficticias de cada capa; `local_reference` no se selecciona por defecto. La suite no accede a la referencia privada.

Las pruebas opt-in de `test_revisor_llm.py` están excluidas de la suite ordinaria. Para ejecutar únicamente sus filtros sintéticos, sin red ni modelos:

```bash
python -m pytest -o addopts= -m revisor_llm test_revisor_llm.py
```

**Caracterización de Etapa 1**: `test_extraer.py` prueba `ocr_lineas` con cajas y texto ficticios inyectados; no descarga ni carga modelos. La extracción debe conservar el orden de las líneas, las tildes y la Ñ. `tests/test_nucleo_puro.py` caracteriza funciones que reciben texto/estructuras, bloquea `open`/`os.open` durante su uso y verifica que importar `nucleo.*` no carga adaptadores, rutas, red ni OCR. El guard AST usa una lista blanca mínima de imports (`collections`, `rapidfuzz`, `re` y `unicodedata`), revisa también imports diferidos y relativos, y rechaza accesos dinámicos como `__builtins__`.

Comandos reproducibles y resultado de esta caracterización:

```bash
python scripts/generar_fixtures.py
python -m pytest tests/test_nucleo_puro.py test_extraer.py test_revisor_llm.py -q
python -m pytest -o addopts= -m revisor_llm test_revisor_llm.py -q
```

Etapa 2: los módulos de reglas viven en `nucleo/`; OCR, archivos y recursos del diccionario quedan en `adaptadores/`. Las capas reciben textos/estructuras y el corrector ortográfico recibe los recursos ya cargados. `test_verificar.py`, `test_lexico.py`, `test_ortografia.py` y `test_extraer.py` usan las rutas finales. Resultado de Etapa 2: suite `23 passed, 2 deselected`; guard `2 passed` sin xfail. La simulación en un árbol temporal con `nucleo.verificar` importando `adaptadores` falló el guard como se esperaba. Solo se usaron fixtures ficticios.

Checkpoint de Etapa 1 (Python 3.13.9; entorno existente del proyecto):

| Comando | Resultado |
|---|---|
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS: 65 archivos ya formateados |
| `python -m pytest --cov --cov-report=term --cov-report=xml:coverage.xml` | PASS: 22 aprobadas, 2 deseleccionadas, 1 xfail esperado; cobertura total 52 % |
| `python -m pip_audit --strict -r requirements.txt -r requirements-dev.txt` | PASS: no se encontraron vulnerabilidades conocidas |
| `pre-commit run --all-files` | PASS: Ruff check, Ruff format y detección de secretos |

Checkpoint de Etapa 2 (Python 3.13.9, `.venv` instalado con los locks):

| Comando | Resultado |
|---|---|
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS: 72 archivos ya formateados |
| `python -m pytest --cov --cov-report=term --cov-report=xml:coverage.xml` | PASS: 23 aprobadas, 2 deseleccionadas; cobertura total 36 %; XML validado con las tres rutas nuevas de `nucleo/` |
| `python -m pip_audit --strict -r requirements.txt -r requirements-dev.txt` | PASS: no se encontraron vulnerabilidades conocidas |
| `pre-commit run --all-files` | PASS: Ruff check, Ruff format y detección de secretos |

## Recursos OCR/diccionario verificados en CI

Estos hashes identifican los archivos de modelos/diccionario que usa la verificación de recursos del workflow. No son hashes de distribuciones Python; esos pertenecen a los locks `requirements*.txt`.

| Recurso PP-OCRv4 | SHA-256 |
|---|---|
| `ch_PP-OCRv4_det_infer.onnx` | `d2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9` |
| `ch_PP-OCRv4_rec_infer.onnx` | `48fc40f24f6d2a207a2b1091d3437eb3cc3eb6b676dc3ef9c37384005483683b` |
| `ch_ppocr_mobile_v2.0_cls_infer.onnx` | `e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c` |

| Diccionario `es_PE` fijado a `LibreOffice/dictionaries@32b006a2c22a4ac7e8ed3f03346f7b3d85a970a4` | SHA-256 |
|---|---|
| `es_PE.aff` | `d966cb748e4a688ed75ec84b50c0835ac438e5325ee4fce703a093794f9cba7e` |
| `es_PE.dic` | `1d810a0a319fee329000538cf4df76621bb71228172558b87490f8b9c19b9d75` |

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
