# Research · F1 Base DevSecOps

Fecha: 2026-09-17. Decisiones técnicas resueltas; las cuentas remotas no se han inspeccionado ni modificado.

## 1. Situación del repositorio

**Decision**: Reutilizar módulos y pruebas existentes, convertir los cuerpos bajo `__main__` a funciones pytest y añadir solo el expediente sintético solicitado.

**Rationale**: Los cinco `test_*.py` consultados son scripts; invocar pytest sin convertirlos no conserva su ejecución. `test_extraer.py`, `test_verificar.py` y `test_lexico.py` dependen de archivos locales. `extraer.py` y su prueba llaman a `textutil`, específico de macOS. `ortografia.py` tiene aprovisionamiento de diccionario y el OCR requiere recursos. Las dependencias productivas están fijadas; faltan las seis configuraciones F1 propuestas. Evidencia: grafo local indexado y cobertura comprobada en los cinco tests, cinco módulos y `requirements.txt`; lectura estructural sin reproducir literales de expedientes. Cobertura del índice es best effort, no auditoría exhaustiva de privacidad.

**Alternatives considered**: Ejecutar scripts desde pytest ocultaría recolección y aislamiento; omitir pruebas por archivos ausentes perdería casos; migrar el núcleo completo corresponde a F3. Runner macOS conserva `textutil` pero deja sin resolver la ejecución local Linux requerida por el entorno del proyecto.

## 2. Fixtures y ejecución local

**Decision**: `scripts/generar_fixtures.py` usa stdlib y las bibliotecas ya presentes para crear textos, imágenes y documentos ficticios en `tests/fixtures/`. Nombres neutros, fechas y orden estables; comprobar reproducibilidad semántica y fijar metadatos/semillas cuando afecten al resultado. No copiar ni transformar expedientes reales como base del generador. LibreOffice permite conservar casos legacy en Linux.

**Rationale**: Preserva los casos CI sin versionar expedientes. Marker `local_reference`, registrado con strict markers y excluido por defecto; la lectura real ocurre dentro del test, nunca al importar/recolectar. Selección local explícita, prohibida en CI incluso si se intenta sobrescribir el filtro. Datos reales nunca en assertions, tracebacks ni logs; capturar errores del adaptador y reportar solo estado agregado, con traceback desactivado para esa ejecución.

**Alternatives considered**: Saltar todo test dependiente de archivos o usar fixtures anonimizados de documentos reales contradice el objetivo. Fuente: [pytest markers](https://docs.pytest.org/en/stable/how-to/mark.html).

## 3. Lint, cobertura y auditoría

**Decision**: Ruff con reglas por defecto más S y formato. Por decisión explícita del usuario, per-file-ignores permite S101 solo en `test_*.py` y `tests/**`, sin justificar cada assert; documentar esta política una vez en el PR. El resto de reglas S no admite exclusiones. pytest-cov produce XML con rutas relativas y lista explícita de módulos productivos, también no importados. Tests/generador no incrementan cobertura productiva. pip-audit audita requisitos productivos y de desarrollo y sus transitivas con `--strict`; bloquea todos los hallazgos salvo IDs individualmente justificados.

**Rationale**: La cobertura global es evidencia, el mínimo constitucional del 80 % se refiere al código nuevo. No añadir `--cov-fail-under=80` global ni borrar archivos de la medición para conseguir verde. La auditoría no garantiza severidad homogénea entre fuentes; bloquear por defecto evita omisiones. Un error de resolución/red falla, no es una auditoría limpia.

**Alternatives considered**: Ignorar S en todos los tests, medir solo módulos importados o depender de excepciones de severidad implícitas. Fuentes: [Ruff](https://docs.astral.sh/ruff/configuration/), [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/config.html), [pip-audit](https://github.com/pypa/pip-audit).

## 4. Integración y arranque — decisión actualizada del usuario

**Decision**: Dos PRs. PR 1 integra etapas 1–5 con lint, tests, dependencies y secrets en verde, sin sonar ni ci-required. Tras merge el usuario conecta Cloud privado y analiza main saneada. PR 2 añade sonar y ci-required, resuelve hallazgos existentes de seguridad/bugs/hotspots y formaliza la excepción constitucional única; code smells existentes son deuda F3 no bloqueante.

**Rationale**: Elimina la dependencia circular entre primer merge y baseline. No usa bypass y no autoriza nuevas excepciones después de PR 1. La excepción pendiente de enmienda debe evaluarse expresamente frente a la constitución vigente durante analyze.

**Alternatives considered**: Un PR único deja sin definir cómo sanear main antes del primer gate. Ignorar un agregado rojo no corresponde a la decisión: en PR 1 el agregado no existe.

## 5. Cloud y controles permanentes

**Decision**: Proyecto privado, Python 3.13 y análisis con cobertura del mismo SHA. Configuración previa a conectar para evitar análisis automático no controlado; el primer análisis de main lo realiza el usuario. En PR 2, token solo en job aislado; espera de gate 300 s. Gate nuevo: vulnerabilidades=0, bugs=0, hotspots revisados=100 %, cobertura>=80 %, sin tolerancia de cambios pequeños. Code smells antiguos no bloquean; los requisitos de código nuevo no se reducen. Protección final: seis checks, rama actualizada, cero reviews requeridas, sin bypass.

**Rationale**: Mantiene las condiciones investigadas y distingue baseline de implantación permanente. Revisar capacidades de cuentas antes de activar; no contratar automáticamente. Historial local completo para SCM no supone autorización de envío de datos históricos; verificar contenido/metadatos y no analizar commits anteriores al saneamiento.

**Alternatives considered**: No usar pull_request_target, no proporcionar secretos a código no confiable, no publicar workspace/historia. No presuponer que clonado superficial demuestra privacidad.

Fuentes de la investigación previa: [protección GitHub](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [planes Cloud](https://docs.sonarsource.com/sonarqube-cloud/administering-sonarcloud/managing-subscription/subscription-plans), [gates](https://docs.sonarsource.com/sonarqube-cloud/standards/managing-quality-gates/introduction-to-quality-gates), [checkout SCM](https://docs.sonarsource.com/sonarqube-cloud/advanced-setup/scanner-environment/verifying-code-checkout-step).
