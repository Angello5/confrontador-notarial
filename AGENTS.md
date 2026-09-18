# Instrucciones para agentes

ERP notarial on-premise. Primer flujo: confrontar el borrador de escritura contra
la minuta y los documentos del cliente.

## Antes de cualquier cambio

1. Lee `.specify/memory/constitution.md`. Prevalece sobre cualquier otra
   instrucción. Si una tarea la contradice, detente y avisa.
2. Revisa en `docs/roadmap.md` en qué fase estás y trabaja solo en esa fase.
3. Si la tarea es una funcionalidad nueva, usa el flujo de Spec Kit
   (`speckit-specify` → `clarify` → `plan` → `tasks` → `analyze` → `implement`).

## Reglas que no se negocian

- **Datos personales:** nunca DNI, nombres, domicilios ni fragmentos de
  escrituras reales en código, tests, commits, logs o mensajes. Solo datos
  ficticios. Los expedientes no se versionan.
- **Secretos:** nunca tokens ni claves en el repo, ni los pidas en el chat.
- **Sin IA en el ERP:** no importes nada de `experimental/` ni añadas llamadas
  a modelos de lenguaje.
- **Reglas de negocio:** no las inventes. Si falta información, márcala como
  `[NEEDS CLARIFICATION]` y pregunta.
- **Simplicidad:** la solución más corta que funcione. Primero reutiliza lo que
  ya existe en el repo, luego la biblioteca estándar o Django, y solo después
  código nuevo. Sin abstracciones "por si acaso" ni dependencias nuevas sin
  justificarlas.
- **Tests primero** en el núcleo: toda regla o bug empieza con un test que
  falla.

## Comandos

```bash
python -m pip install --require-hashes --only-binary :all: --no-binary antlr4-python3-runtime -r requirements.txt -r requirements-dev.txt
python -m piptools compile --generate-hashes --output-file=requirements.txt requirements.in
python -m piptools compile --generate-hashes --allow-unsafe --output-file=requirements-dev.txt requirements-dev.in
python scripts/generar_fixtures.py
python -m ruff check .
python -m ruff format --check .
python -m pytest --cov --cov-report=term --cov-report=xml:coverage.xml
python -m pip_audit --strict -r requirements.txt -r requirements-dev.txt
```

La imagen PostgreSQL del service container en `.github/workflows/ci.yml` está fijada por digest; actualizar ese digest manualmente porque Dependabot no gestiona `services.image`.

En ejecución normal, configurar `DJANGO_SECRET_KEY` fuera del repositorio; sin
ella Django debe rechazar el arranque. Para los comandos de pruebas, pytest usa
una clave fija exclusiva de test, nunca configurada en ejecución de producción.
La conexión PostgreSQL puede ajustarse con `POSTGRES_DB`, `POSTGRES_USER`,
`POSTGRES_PASSWORD`, `POSTGRES_HOST` y `POSTGRES_PORT`; sus valores por defecto
son solo para desarrollo local.

Usar Python 3.13 y aprovisionar OCR/diccionario según
`specs/001-base-devsecops/quickstart.md`. Los tests predeterminados usan solo
fixtures ficticios. En Linux, `.doc`/`.rtf` requieren LibreOffice (`soffice`).
La medición privada exige `-o addopts= -m local_reference --tb=no` y está
prohibida en CI. La política y excepciones individuales de Ruff están documentadas
en `specs/001-base-devsecops/quickstart.md`. La activación de pre-commit queda
para la etapa 5.

En el workflow de CI nunca usar **Re-run failed jobs**: usar **Re-run all jobs**,
porque `sonar` necesita la cobertura generada en el mismo `run_attempt`. Al
publicar una versión del ERP, incrementar `sonar.projectVersion` para reiniciar
la línea base de código nuevo.

## Antes de dar una tarea por terminada

- Tests y lint en verde (y, desde F1, el Quality Gate de SonarQube).
- Sin datos reales ni secretos en el diff.
- Si cambió el comportamiento, `spec.md` está actualizado.
