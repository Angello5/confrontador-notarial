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

**Esperado**: pasan fixtures y pruebas ficticias de cada capa; `local_reference` y `ocr_research` no se seleccionan por defecto. La suite no accede a la referencia privada.

### Cobertura de `experimental/`

Por decisión de la revisión del PR #17 (2026-09-19), `experimental/` se
excluye únicamente del denominador de cobertura: está fuera del ERP, no se
despliega y sus pruebas son opt-in. Continúa incluido en el análisis de
SonarQube para detectar vulnerabilidades, bugs y secretos; no se usa
`sonar.exclusions`.

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

Estos hashes identifican los modelos OCR predeterminados y el diccionario `es_PE` que usa la verificación de recursos del workflow. No son hashes de distribuciones Python; esos pertenecen a los locks `requirements*.txt`.

La revisión de secretos conserva en `.gitleaksignore` únicamente tres huellas
históricas del commit `32c9142` (`generic-api-key`, líneas 28, 29 y 36) para
recursos OCR públicos. El código actual usa nombres descriptivos y no requiere
excepciones adicionales. Verificar localmente con Gitleaks 8.28.0 (SHA-256
`a65b5253807a68ac0cafa4414031fd740aeb55f54fb7e55f386acb52e6a840eb`), sin
escanear `.venv/` ni datos locales:

```bash
gitleaks dir --redact .
gitleaks git --redact --log-opts="2893539..HEAD"
```

Ambos comandos deben terminar sin hallazgos.

| Detector predeterminado | SHA-256 |
|---|---|
| `ch_PP-OCRv5_mobile_det.onnx` | `4d97c44a20d30a81aad087d6a396b08f786c4635742afc391f6621f5c6ae78ae` |

| Recurso PP-OCRv5 latin predeterminado | SHA-256 |
|---|---|
| `latin_PP-OCRv5_rec_mobile_infer.onnx` | `b20bd37c168a570f583afbc8cd7925603890efbcdc000a59e22c269d160b5f5a` |

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
curl -fsSL https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.4.0/onnx/PP-OCRv5/det/ch_PP-OCRv5_mobile_det.onnx -o ~/.cache/notaria-ocr/models/ch_PP-OCRv5_mobile_det.onnx
curl -fsSL https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.4.0/onnx/PP-OCRv5/rec/latin_PP-OCRv5_rec_mobile_infer.onnx -o ~/.cache/notaria-ocr/models/latin_PP-OCRv5_rec_mobile_infer.onnx
(cd ~/.cache/notaria-ocr/models && printf '%s\n' '4d97c44a20d30a81aad087d6a396b08f786c4635742afc391f6621f5c6ae78ae  ch_PP-OCRv5_mobile_det.onnx' 'b20bd37c168a570f583afbc8cd7925603890efbcdc000a59e22c269d160b5f5a  latin_PP-OCRv5_rec_mobile_infer.onnx' | sha256sum -c -)
```

Para medir la configuración vigente, con `fonts-liberation` instalado en Linux
y esos recursos verificados, ejecutar explícitamente el test opt-in:

```bash
python -m pytest -o addopts= -m ocr_research -s test_ocr_research.py
```

El test usa el detector v5 mobile y el reconocedor v5 de `OCR_MODELS`; lee el
alfabeto de metadata ONNX y no requiere un archivo de claves externo. La
comparación v4/v5 original queda registrada como medición histórica en
`research.md`.

## Aprovisionamiento offline para el servidor (F8)

En el equipo conectado, descarga/prepara los recursos como arriba. Copia íntegro `~/.cache/notaria-ocr/models/` al mismo directorio del usuario de servicio en el servidor sin red. Antes de iniciar el ERP, valida los nombres y hashes en el servidor:

```bash
cd ~/.cache/notaria-ocr/models
sha256sum -c - <<'EOF'
4d97c44a20d30a81aad087d6a396b08f786c4635742afc391f6621f5c6ae78ae  ch_PP-OCRv5_mobile_det.onnx
b20bd37c168a570f583afbc8cd7925603890efbcdc000a59e22c269d160b5f5a  latin_PP-OCRv5_rec_mobile_infer.onnx
EOF
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
RapidOCR usa 502 caracteres de metadata `character` del ONNX v5 (incluye ñ, Ñ, Ú, Á e Í) e ignora `rec_keys_path`; v4 sí carece de ñ/Ñ. Una Ñ aislada a veces se descarta (una vez se leyó como N y tres fueron descartadas); en SEÑORA, NÚÑEZ, MUÑOZ, ESPAÑA y ÑANDÚ se lee bien. Si se descarta dentro de un nombre, se genera una observación.

**Resultado T014–T016 (2026-09-19)**: la persona usuaria ejecutó T014 sobre `c0febe2`: 1 prueba aprobada en 10,00 s, OCR real con PP-OCRv5 latin y cero archivos `.json` después en su caché. El gate se cumple (8 observaciones, cinco salidas idénticas, cero en la escritura correcta y piso sintético), por lo que se adopta PP-OCRv5 latin con `use_cls=False`. El PR #11 de Dependabot (RapidOCR 3.9.2) queda sustituido por esta decisión; no se cierra aquí y el coordinador lo cerrará al publicar el PR de F3.

## Aprovisionamiento offline para F8

La deuda de aprovisionamiento offline de modelos para F8 está descrita en
`docs/deuda-f3.md` y debe resolverse allí al definir el despliegue; esta guía
solo conserva la validación local de hashes y el procedimiento reproducible.

## Gates previos a completar F3

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest --cov --cov-report=term --cov-report=xml:coverage.xml
python -m pip_audit --strict -r requirements.txt -r requirements-dev.txt
```

El Quality Gate de SonarQube y la revisión de secretos corresponden al CI del PR; la medición privada no se ejecuta en CI. Revisar los 10 IDs de `docs/deuda-f3.md` y documentar resolución o justificación por ID.

## Checkpoint de Etapa 5

Resultado local (2026-09-19, Python 3.13.9, PostgreSQL de prueba en
`127.0.0.1:55432`): `manage.py check`, `migrate`, `makemigrations --check`,
generación de fixtures, Ruff check, Ruff format, pytest con cobertura,
`pip-audit --strict` y `pre-commit --all-files` pasaron. La suite reportó
`113 passed, 4 deselected` y cobertura XML válida (86 % total; 90,4 % de
368/407 líneas ejecutables nuevas cubiertas contra `origin/main`, excluyendo
`experimental/`); solo se usaron fixtures
ficticios. La revisión del diff no encontró secretos, datos reales, recursos
privados ni imports de IA en el flujo productivo del ERP; la UI Streamlit
transitoria conserva su aislamiento documentado en `experimental/`.

F3 queda lista para PR solo tras aplicar este arreglo de CI. T028 queda
pendiente: el Quality Gate de SonarQube y `gitleaks` requieren el CI del PR;
no se declara evidencia remota antes de publicar dicho PR.
