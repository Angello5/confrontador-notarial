# Quickstart de validación · F1

Esta guía distingue los checkpoints ejecutados de las etapas pendientes. Las
etapas 1–4 tienen evidencia local abajo; no se afirma CI verde ni F1 completa.

## Checkpoint ejecutado · Etapa 1 (T001–T006)

Revisión local del árbol partiendo de `6c2539e`, con constitución v1.3.0.
`git status --short` confirmó el árbol limpio y
`gh repo view --json visibility --jq .visibility` confirmó `PRIVATE`.
No se activó SonarQube ni se enviaron documentos o historial a servicios externos.

| Alcance de T001 | Saneamiento y resultado |
|---|---|
| 72 archivos versionados: código, tests, documentación, metadatos y rutas | Revisión local de literales, referencias e identificadores, con salida redactada. No se copiaron valores originales a informes ni archivos temporales. |
| Los cinco `test_*.py` | Identificadores, nombres, fragmentos y referencias ficticios; se conservan las 34 aserciones, sus casos y relaciones esperadas. |
| `bench_llm.py`, `verificar.py`, `lexico.py`, `README.md` | Ejemplos, comentarios y referencias saneados; sin cambios en las reglas del verificador ni del léxico. El benchmark no se ejecutó. |
| `revisor_llm.py` | Ruta personal de credenciales sustituida por `.env` junto al módulo; se conserva la prioridad de `GEMINI_API_KEY`. No se leyeron credenciales ni se llamó a modelos. |
| Fixtures | Cero archivos documentales versionados que renombrar. Referencias neutras bajo `tests/fixtures/`: `cliente/dni.png`, `cliente/minuta.docx`, `borrador/observado.docx`, `resultado/correcto.docx` y `ajeno/plantilla.doc`. Su generación queda en T009. |
| `.gitignore` | Exclusiones de expedientes y secretos conservadas; patrón de carpetas con sufijo numérico reparado al separar el comentario. Añadidos fixtures generados, formatos documentales y artefactos locales de calidad. |

Datos de prueba: cuatro DNI distintos de ocho dígitos (`90000001`–`90000004`),
con CUI `90000004-1`; partida `80000001` y kardex `70001`. Los números
mantienen la longitud de sus ejemplos anteriores. Las cantidades mantienen
el patrón `S/ 12,345.67`. Los sustitutos nominales y sus erratas conservan
las relaciones de igualdad, ausencia, flexión y corrección que prueban los tests.

Validación T005 en Python 3.13.9, con un entorno temporal y las versiones ya
fijadas `rapidfuzz==3.14.5` y `spylls==0.1.7`, sin modificar requisitos:

| Comprobación | Resultado |
|---|---|
| `python test_ortografia.py` | PASS: 11 errores, 11 palabras correctas y tratamiento de apellidos ficticios. |
| `python test_revisor_llm.py` | PASS: 10 casos, 4 aceptados y 6 descartados; sin llamadas a modelos. |
| Casos léxicos autónomos | PASS: acentos y flexión/errata conservados. |
| `catalogo` y regex con textos ficticios | PASS: DNI rotulado, CUI de imagen, ambas formas de partida y montos con separador de miles y dos decimales. |
| AST de los 13 archivos Python y comparación de aserciones | Sintaxis válida; 34 aserciones conservadas en los cinco tests. AST ejecutable de verificador y léxico sin cambios. |
| Revisión de originales en árbol y contenido añadido | Sin coincidencias de los identificadores y nombres retirados; referencias nuevas neutras. Las líneas eliminadas permanecen en el historial privado, no se duplican en evidencia. |
| Revisión local de patrones de secretos | Sin coincidencias detectadas en los 72 archivos. Es una comprobación limitada por patrones, separada de la revisión de datos personales; gitleaks todavía no está instalado y se incorpora en etapas posteriores. |
| `git check-ignore --stdin` | PASS para 17 rutas ficticias de expedientes, secretos y artefactos; `.env.example` sigue versionable. |
| `ruff check .` | Cinco hallazgos preexistentes (E401/E741), comprobados contra la revisión inicial sin hallazgos nuevos; corrección reservada a etapa 4. |
| `git diff --check` | PASS. |

T005 aprobado para saneamiento. La suite documental completa no se declara
aprobada: faltan los fixtures sintéticos de etapa 2 y la adaptación de
`textutil` a Linux de etapa 3. No se midió cobertura ni se declaró CI verde.
T006 registra estos cambios en el commit local `chore: sanitize repository data`;
no incluye push ni integración. El historial no se reescribe y publicar el
repositorio exige limpiarlo en una fase aparte. La etapa 2 no se inicia aquí.

## Prerrequisitos

Para etapa 2 basta Python 3.13, los dos archivos de requisitos y los recursos
OCR/diccionario indicados a continuación. LibreOffice se integra en etapa 3;
Ruff y pip-audit se validan en etapa 4; gitleaks y controles remotos pertenecen a etapas posteriores.

- Clon limpio privado, Python 3.13, Git y LibreOffice (`soffice` en PATH) en Linux; gitleaks fijado y verificado según documentación de implementación.
- Recursos OCR y diccionario es_PE aprovisionados con los orígenes/versiones documentados. Solo fixtures ficticios; ningún expediente privado en el clon.
- Antes de conectar Sonar: revisión de saneamiento del contenido y nombres, configuración CI presente, análisis automático desactivado, proyecto Cloud privado. GitHub Pro/Team/Enterprise y Sonar Team/Enterprise para las capacidades elegidas; verificar disponibilidad, no contratar automáticamente.
- Variables públicas de proyecto/organización y `SONAR_TOKEN` aprovisionados por el responsable en almacenes de secretos; nunca pegarlos en comandos o documentos.

## Aprovisionamiento reproducible de pruebas · T012

```bash
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
```

El generador usa solo stdlib, PyMuPDF y openpyxl, ya presentes en los requisitos
productivos. No necesita python-docx, reportlab, fuentes externas ni documentos
de clientes. Genera el DOCX como ZIP/XML, la imagen con las fuentes incorporadas
de PyMuPDF y el XLSX con openpyxl. Orden, fechas, permisos ZIP y metadatos son
fijos; los PDF no incorporan identificadores aleatorios.

RapidOCR 3.4.3 y onnxruntime 1.23.2 usan los modelos PP-OCRv4 de
`https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.4.0/onnx/PP-OCRv4/`:
`det/ch_PP-OCRv4_det_infer.onnx`, `rec/ch_PP-OCRv4_rec_infer.onnx` y
`cls/ch_ppocr_mobile_v2.0_cls_infer.onnx`. Sus SHA-256 coinciden con el manifiesto
`default_models.yaml` del paquete. El diccionario es_PE se fija al commit
`32b006a2c22a4ac7e8ed3f03346f7b3d85a970a4` de LibreOffice/dictionaries.
Antes de los tests, aprovisionar y verificar así (solo descarga recursos públicos):

```bash
python - <<'PY'
from hashlib import sha256
from pathlib import Path
from urllib.request import urlopen
import rapidocr
from extraer import _ocr

_ocr()  # Aprovisiona/carga modelos; no procesa documentos.
modelos = {
    "ch_PP-OCRv4_det_infer.onnx": "d2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9",
    "ch_PP-OCRv4_rec_infer.onnx": "48fc40f24f6d2a207a2b1091d3437eb3cc3eb6b676dc3ef9c37384005483683b",
    "ch_ppocr_mobile_v2.0_cls_infer.onnx": "e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c",
}
for nombre, esperado in modelos.items():
    rutas = list(Path(rapidocr.__file__).parent.rglob(nombre))
    assert len(rutas) == 1 and sha256(rutas[0].read_bytes()).hexdigest() == esperado

base = "https://raw.githubusercontent.com/LibreOffice/dictionaries/32b006a2c22a4ac7e8ed3f03346f7b3d85a970a4/es/es_PE"
for extension, esperado in {
    ".aff": "d966cb748e4a688ed75ec84b50c0835ac438e5325ee4fce703a093794f9cba7e",
    ".dic": "1d810a0a319fee329000538cf4df76621bb71228172558b87490f8b9c19b9d75",
}.items():
    ruta = Path.home() / ".cache/notaria-ocr" / ("es_PE" + extension)
    if ruta.exists():
        contenido = ruta.read_bytes()
    else:
        with urlopen(base + extension, timeout=30) as respuesta:
            contenido = respuesta.read()
    assert sha256(contenido).hexdigest() == esperado, "Recurso distinto de la versión fijada"
    if not ruta.exists():
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(contenido)
print("Recursos de pruebas verificados.")
PY
python scripts/generar_fixtures.py
python -m pytest --cov --cov-report=term --cov-report=xml:coverage.xml
```

No se descargan expedientes en pruebas. Si falta un recurso, se aprovisiona antes
de ejecutar la suite. Los 11 documentos ficticios se regeneran y permanecen
ignorados; no se añaden a Git a la fuerza. La conversión a `.doc` sigue dentro
del test legacy y usa LibreOffice desde T017 (ver etapa 3).

## Checkpoint ejecutado · Etapa 2 (T007–T014)

Entorno: Python 3.13.9, pytest 8.4.2, pytest-cov 7.0.0 y requisitos productivos
sin cambios. Antes de crear los fixtures, las pruebas de cuadro de texto,
verificación y léxico fallaron por archivos ausentes; después se aprobaron.

| Casos conservados | Evidencia |
|---|---|
| Imagen OCR, filtro de sello inclinado, lectura repetida/caché y PDF escaneado | Imagen ficticia con DNI, rótulos y sello; catálogo de cuatro personas y lectura de DNI correcta. El PDF contiene imagen y cero texto embebido. |
| `.doc` OLE, texto convertido y lectura `.rtf` | Aserciones conservadas en `test_legacy`; único fallo Linux pendiente de etapa 3, sin skip ni xfail. |
| XLSX y nota de cuadro de texto | Filas conservadas; nota dentro de `w:txbxContent` en Choice y Fallback, dos copias en XML y una en texto extraído. |
| Catálogo, borrador observado, resultado sin falsos positivos y diagnóstico | DNI/partida/cuatro nombres, al menos seis observaciones, resultado vacío y rechazo de plantilla ajena, también mezclada con fuentes válidas. La plantilla de diagnóstico usa DOCX; el caso de lectura DOC permanece en el test legacy. |
| Léxico | Seis correcciones, corpus sin errores, tres errores de minuta, acento grave y flexión frente a errata. |
| Ortografía | Once errores, once correctas, apellidos ficticios con/sin extra y correcciones exactas de tilde. |
| Filtro determinista | Diez casos, cuatro aceptados, seis descartados y respaldo de fuentes; sin invocar modelos. |
| Casos adicionales | PDF con texto, tabla DOCX, tabulador sin XML residual, regeneración binaria idéntica y cinco escenarios de selección/privacidad. |

Resultados T013:

- `python -m pytest --collect-only -q`: 15 pruebas seleccionadas de 16;
  la medición `local_reference` está deseleccionada por defecto.
- Suite completa con cobertura: **14 aprobadas, 1 fallo conocido (`textutil`),
  1 deseleccionada**. Una copia limpia del árbol, sin fixtures previos, reproduce
  ese resultado después de generar, también con `CI=true`.
- Regeneración: los SHA-256 de los 11 fixtures son idénticos entre ejecuciones.
- Cobertura: XML parseable, rutas relativas, 643 líneas productivas y 338
  cubiertas (52,57 %). Incluye explícitamente los ocho módulos productivos,
  también las interfaces y benchmark no importados (0 %); tests y generador no
  incrementan el denominador. No se impone un 80 % global. Si se solicita
  cobertura sin XML válido/productivo, la sesión no aprueba.
- Selección local: exclusión predeterminada y al quitar `addopts`; rechazo en CI
  aunque se seleccione el marker; error saneado ante ruta ausente, incluso con
  `--showlocals --tb=long -s`. El recorrido completo local se probó con una copia
  temporal exclusivamente sintética: ocho observaciones, cero falsos positivos
  y cinco repeticiones iguales. No se abrieron expedientes reales.
- La medición privada requiere exactamente `-m local_reference`, directorio
  externo y archivos presentes. Descarta capturas, sanea errores y elimina
  su caché OCR temporal incluso al fallar.

T013 aprobado con la única limitación legacy prevista. T014 registra el commit
local `test: add synthetic fixtures and pytest`; no hay push ni avance a etapa 3.

## Etapa 3: T015–T017 y T019 ejecutadas; T018 pendiente de medición local

LibreOffice en Linux: paquete de la distribución (`apt install libreoffice-writer`
o equivalente), ejecutable `soffice` en PATH. Probado con LibreOffice 26.2,
Python 3.13.

- Tests primero: `test_legacy` y `test_legacy_sin_libreoffice` fallaron antes del
  cambio. Único caller de `_legacy`: `leer` en `extraer.py`.
- `_legacy` usa `textutil` en macOS (sin cambios) y `soffice --headless` en el
  resto: argumentos sin shell, timeout de 120 s, directorio temporal y perfil
  aislado por conversión. Ejecutable ausente, fallo o sin salida → `ValueError`
  sin stderr, contenido ni rutas.
- `test_legacy` crea el `.doc` OLE desde `minuta.rtf` con el mismo conversor;
  comprueba lectura `.doc`/`.rtf` y que no quedan temporales.
- Suite completa con cobertura en Linux: **16 aprobadas, 1 deseleccionada**, sin
  fallos; dos ejecuciones consecutivas y regeneración de fixtures sin cambios.
- T018: medición `local_reference` pendiente con `EXPEDIENTES_REFERENCIA_DIR`;
  la ejecuta el usuario en su máquina antes del merge de PR 1 porque cambió
  `extraer.py`.

## Checkpoint ejecutado · Etapa 4 (T020–T025)

Entorno nuevo `.venv/t024`, Python 3.13.9, instalado únicamente desde ambos
archivos de requisitos; recursos OCR/diccionario verificados con los hashes de
T012. Herramientas fijadas: Ruff 0.16.8, pip-audit 2.10.1, pre-commit 4.6.2,
pytest 9.0.3 y pytest-cov 7.0.0. Pre-commit queda instalado; su configuración y
activación pertenecen a etapa 5.

Cambios de versiones: Pillow 11.0.0 → 12.3.0 y pytest 8.4.2 → 9.0.3.
La auditoría inicial emitió 35 filas (18 IDs únicos) en esos dos paquetes;
la final no encuentra vulnerabilidades, sin IDs exceptuados. Se corrigieron
los IDs de Pillow PYSEC-2026-{165,2249,2250,2252,2253,2254,2255,2256,2257,
2874,3451,3453,3454,3493,3494,3495,3496} y de pytest PYSEC-2026-1845.
Las restantes versiones directas no cambiaron; `pip check` confirma compatibilidad.
Versiones consultadas en [PyPI](https://pypi.org/) y comprobadas por instalación
real en Python 3.13 y auditoría estricta de las dependencias transitivas.

Ruff: 13 hallazgos iniciales, 7 corregidos y 6 justificados. Se separaron dos
imports E401 y renombraron tres variables E741; se aplicó formato a los 18
archivos Python propios. S324: SHA-1 solo identifica la caché, se declara
`usedforsecurity=False` y se conserva la clave anterior. S607: macOS usa
`/usr/bin/textutil`, evitando buscar el binario en PATH; el nuevo test ficticio
falló antes del cambio y pasó después, conservando argumentos y tabuladores.
No se alteraron reglas de negocio ni se ejecutaron modelos o expedientes reales.

Política para el PR: S101 permitido únicamente en `test_*.py` y `tests/**` por
per-file-ignores, porque pytest usa asserts. Las demás excepciones S requieren
`noqa` individual con código exacto y motivo, listadas en el PR. El coordinador
aprobó esta precisión durante T021 y se sincronizó la frase en spec, plan y
contrato CI; no hay exclusiones globales ni por archivo de otras reglas.
Copiar al PR las seis excepciones revisadas:

| Ubicación | Regla | Justificación individual |
|---|---|---|
| `extraer.py` · `_soffice` | S603 | LibreOffice: conversor configurado por código, argumentos en lista sin shell, perfil temporal propio; no se interpreta una cadena de comandos del documento. |
| `extraer.py` · `_legacy` | S603 | textutil: ejecutable absoluto fijo, opciones fijas y ruta como argumento, sin shell. |
| `ortografia.py` · `_descargar` | S310 | Descarga de diccionario desde URL HTTPS fija en código; solo concatena `.aff`/`.dic` internas, no una URL suministrada por documentos. |
| `revisor_llm.py` · `consultar` | S310 | Request construido con esquema HTTPS y host fijos; modelo va en la ruta, no cambia el esquema; no se invocó la red de modelos durante las pruebas. |
| `tests/conftest.py` · `pytest_sessionfinish` | S314 | XML local de confianza generado por coverage en la misma ejecución; no es XML de documentos subidos. |
| `tests/test_seleccion_local.py` · `test_seleccion_privada` | S603 | Intérprete propio y argumentos de pytest fijados por el test, entorno controlado y sin shell. |

No se añadieron dependencias para estas revisiones ni se cambiaron APIs para
eludir el detector. Las excepciones deben revisarse si cambia la procedencia de
argumentos, URLs o XML; no autorizan procesar entradas arbitrarias sin validación.

Con el entorno nuevo activado, resultados del checkpoint T024:

| Comando / comprobación | Resultado |
|---|---|
| `python -m pip install -r requirements.txt -r requirements-dev.txt` | PASS en entorno nuevo, sin dependencias previas. |
| Aprovisionamiento T012 | PASS: SHA-256 de tres modelos OCR y dos archivos del diccionario. |
| `python scripts/generar_fixtures.py` | PASS: fixtures exclusivamente ficticios. |
| `ruff check .` | PASS: cero hallazgos pendientes. |
| `ruff format --check .` | PASS: 56 archivos examinados, sin reformatear. |
| `python -m pytest --cov --cov-report=term --cov-report=xml:coverage.xml` | PASS: 17 passed, 1 deselected; incluye los 16 casos previos y el test macOS. |
| `coverage.xml` | XML válido, ocho módulos productivos, rutas relativas, 665 líneas válidas / 366 cubiertas (55,04 %); sin imponer umbral global. |
| `pip-audit --strict -r requirements.txt -r requirements-dev.txt` | PASS: No known vulnerabilities found; cero excepciones. |
| `python -m pip check` | PASS: No broken requirements found. |
| Muestras ficticias por stdin de Ruff | S101 detectada fuera de tests; S301 detectada dentro de tests; assert permitido en tests. No se conservaron muestras. |
| Revisión del diff y `git diff --check` | PASS: cambios de formato, correcciones descritas y documentación; sin nuevos datos reales ni secretos. |

T024 aprobado. T025 registra el commit local `chore: pass lint and dependency audit`.
No se inicia etapa 5, no hay push, PR, cambios de CI ni activación de Sonar.
T019 está completada por `2be5a48`, «Finalizar etapa 3» (mensaje distinto al
previsto); T018 sigue abierta. Pendiente: medición local_reference con EXPEDIENTES_REFERENCIA_DIR, la ejecuta el usuario en su máquina antes del merge de PR 1 (extraer.py cambió).

Deuda fuera de alcance: revisor_llm.py envía la API key en la query (?key=); usar cabecera x-goog-api-key si la capa experimental se reactiva.

## Validación local sintética

Desde la raíz del repositorio, después de implementar:

```bash
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
python scripts/generar_fixtures.py
python -m ruff check .
python -m ruff format --check .
python -m pytest -m 'not local_reference' --cov --cov-report=term --cov-report=xml:coverage.xml
python -m pip_audit --strict -r requirements.txt -r requirements-dev.txt
```

En etapa 5, una vez configurados gitleaks y `.pre-commit-config.yaml`, añadir:

```bash
gitleaks dir --redact .
python -m pre_commit install
python -m pre_commit run --all-files
```

Esperado: pruebas recolectadas y aprobadas; XML válido con líneas productivas; código existente en verde, sin exclusiones globales. Repetir generación y pruebas conserva resultados. Los expedientes reales nunca son necesarios. El escaneo de directorio complementa, no sustituye, el escaneo de commits de CI.

## Medición local con expedientes externos

La ruta se configura localmente mediante `EXPEDIENTES_REFERENCIA_DIR`, fuera del repositorio, sin imprimirla. El test lee y mide dentro de su cuerpo y solo devuelve resumen no identificable.

Ese directorio externo debe contener `cliente/`, `observado.docx` y
`correcto.docx`, correspondientes al expediente de referencia con baseline
ocho observaciones y cero falsos positivos. Los nombres locales neutros no se
versionan; el test nunca lee datos privados al importar o recolectar. Cambiar
esa baseline requiere una medición y decisión expresa, no ajustar el test para
obtener verde.

```bash
python -m pytest -o addopts= -m local_reference --tb=no -q
```

Esperado: ejecución únicamente tras selección expresa, resumen sin datos personales y fallo saneado si falta el directorio o los archivos requeridos. Ejecutar el mismo comando con indicador CI debe ser rechazado. Si se modificó el núcleo, comparar con baseline local sin regresión antes del merge; no subir reportes de contenido.

## PR 1 · Etapas 1–5

1. Validación previa local: tests, ruff, auditoría y secretos en verde; árbol/diff saneados.
2. Commit de etapa y push de rama privada.
3. PR 1 en borrador: verificar lint, tests, dependencies y secrets para el SHA final. No existen sonar ni ci-required aún.
4. Pasar PR 1 a listo y mergear con los cuatro checks verdes, sin bypass.
5. Verificar ejecución de los cuatro controles en main; registrar evidencia en el PR.

## Entre PRs · Conexión por el usuario

El usuario conecta SonarQube Cloud privado y realiza el primer análisis de main ya saneada, con cobertura de ese SHA y configuración preparada. No analizar commits anteriores. Verificar alcance de fuentes y metadatos antes del envío. Esperar esta acción si aún no se completó; nunca pedir secretos en chat.

## PR 2 · Etapa 6

1. Inventariar vulnerabilidades, bugs y Security Hotspots existentes; corregirlos o justificarlos individualmente por escrito. Registrar code smells existentes como deuda F3 en `docs/deuda-f3.md`, sin bloquear ni excluir código del análisis.
2. Añadir sonar y ci-required de cinco dependencias y el gate de código nuevo del contrato; la constitución v1.3.0 ya resolvió TODO(SONAR) y la cláusula de arranque.
3. Validación previa local y evidencias de hallazgos; commit/push; abrir PR 2.
4. Verificar cinco controles y agregado. Probar fallos individuales, omisión/cancelación, ausencia de cobertura/credenciales, umbrales, cambios pequeños y sin código productivo nuevo. Solo material ficticio; retirar pruebas antes de merge.
5. Verificar PR de Dependabot y documentación, sin auto-merge. No ensayo de forks ni escenario independiente de SHA obsoleto; mantener protección de rama actualizada y prohibición de pull_request_target.
6. Verificar protección de seis checks, PR obligatorio, cero reviews requeridas, sin bypass/force push. Si cambia código/configuración, nuevo commit/push y checks del SHA final.
7. Mergear PR 2 con todos los checks verdes.
8. Verificar ejecución completa en main después del merge; solo entonces declarar F1 terminada. Registrar evidencia posterior en el PR, sin commits directos a main.
