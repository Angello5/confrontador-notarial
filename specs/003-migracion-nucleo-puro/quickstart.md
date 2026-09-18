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

| Detector compartido y modelos de comparación PP-OCRv4 | SHA-256 |
|---|---|
| `ch_PP-OCRv4_det_infer.onnx` | `d2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9` |
| `ch_PP-OCRv4_rec_infer.onnx` | `48fc40f24f6d2a207a2b1091d3437eb3cc3eb6b676dc3ef9c37384005483683b` |
| `ch_ppocr_mobile_v2.0_cls_infer.onnx` | `e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c` |

| Recurso PP-OCRv5 latin predeterminado | SHA-256 |
|---|---|
| `latin_PP-OCRv5_rec_mobile_infer.onnx` | `b20bd37c168a570f583afbc8cd7925603890efbcdc000a59e22c269d160b5f5a` |
| `ppocrv5_dict.txt` | `d1979e9f794c464c0d2e0b70a7fe14dd978e9dc644c0e71f14158cdf8342af1b` |

| Diccionario `es_PE` fijado a `LibreOffice/dictionaries@32b006a2c22a4ac7e8ed3f03346f7b3d85a970a4` | SHA-256 |
|---|---|
| `es_PE.aff` | `d966cb748e4a688ed75ec84b50c0835ac438e5325ee4fce703a093794f9cba7e` |
| `es_PE.dic` | `1d810a0a319fee329000538cf4df76621bb71228172558b87490f8b9c19b9d75` |

El preaprovisionamiento local se instala en `~/.cache/notaria-ocr/models/`;
la aplicación valida estos SHA-256 y no descarga ni consulta la red durante su
ejecución. RapidOCR 3.4.3 y onnxruntime 1.30.0 están fijados por hashes en
`requirements.txt`.

```bash
mkdir -p ~/.cache/notaria-ocr/models
cp "$(~/.venvs/confrontador/bin/python -c 'import rapidocr; from pathlib import Path; print(Path(rapidocr.__file__).parent / "models" / "ch_PP-OCRv4_det_infer.onnx")')" ~/.cache/notaria-ocr/models/
cp "$(~/.venvs/confrontador/bin/python -c 'import rapidocr; from pathlib import Path; print(Path(rapidocr.__file__).parent / "models" / "ppocrv5_dict.txt")')" ~/.cache/notaria-ocr/models/
curl -fsSL https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.4.0/onnx/PP-OCRv5/rec/latin_PP-OCRv5_rec_mobile_infer.onnx -o ~/.cache/notaria-ocr/models/latin_PP-OCRv5_rec_mobile_infer.onnx
(cd ~/.cache/notaria-ocr/models && printf '%s\n' 'd2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9  ch_PP-OCRv4_det_infer.onnx' 'b20bd37c168a570f583afbc8cd7925603890efbcdc000a59e22c269d160b5f5a  latin_PP-OCRv5_rec_mobile_infer.onnx' 'd1979e9f794c464c0d2e0b70a7fe14dd978e9dc644c0e71f14158cdf8342af1b  ppocrv5_dict.txt' | sha256sum -c -)
```

## Medición privada de comportamiento

Ejecutar solo en el entorno autorizado, fuera de CI y con la referencia fuera del repositorio. No añadir contenido/ruta a archivos versionados ni guardar la salida de pytest.

**Esperado**: 8 observaciones en el borrador observado, 0 observaciones en la escritura correcta y cinco corridas idénticas. La prueba informa un resultado agregado sin documento, fragmentos, rutas ni credenciales.

## Gate local T014

El test ordinario fija el piso sintético medido de PP-OCRv5 latin: 8/8 líneas,
al menos 82/85 palabras y 31/32 diacríticos. La comparación detallada de
investigación continúa opt-in. La medición local usa la instalación autorizada
`~/.venvs/confrontador`, fuera de CI y con la referencia fuera del repo:

```bash
test -n "$EXPEDIENTES_REFERENCIA_DIR" && ~/.venvs/confrontador/bin/python -m pytest tests/test_referencia_local.py -o addopts= -m local_reference --tb=no
```

Si `requirements.txt` o `requirements-dev.txt` cambió, instalar sus locks antes
de medir:

```bash
~/.venvs/confrontador/bin/python -m pip install --require-hashes --only-binary :all: --no-binary antlr4-python3-runtime -r requirements.txt -r requirements-dev.txt
```

Comunicar solo si hubo 8 observaciones, cero en la escritura correcta y cinco
salidas idénticas. No copiar texto, imágenes, rutas ni logs del expediente.
PP-OCRv5 latin no emite Ñ mayúscula; la confrontación normaliza Ñ a N antes de
comparar.

**Esperado al aprobar**: 8 observaciones, cero observaciones en escritura correcta, cinco salidas iguales, piso sintético de v5 y hashes validados. La Ñ mayúscula es una limitación documentada; la confrontación la normaliza a N. La decisión sobre el PR #11 queda para después de T014; no se modifica el PR durante estas pruebas.

## Gates previos a completar F3

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest --cov --cov-report=term --cov-report=xml:coverage.xml
python -m pip_audit --strict -r requirements.txt -r requirements-dev.txt
```

El Quality Gate de SonarQube y la revisión de secretos corresponden al CI del PR; la medición privada no se ejecuta en CI. Revisar los 10 IDs de `docs/deuda-f3.md` y documentar resolución o justificación por ID.
