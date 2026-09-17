# Quickstart de validación · F1

Esta guía describe la validación tras implementar el plan. Los comandos de F1 propuestos aún no existen completos en esta etapa; no se han ejecutado ni se afirma CI verde.

## Prerrequisitos

- Clon limpio privado, Python 3.13, Git y LibreOffice (`libreoffice` en PATH) en Linux; gitleaks fijado y verificado según documentación de implementación.
- Recursos OCR y diccionario es_PE aprovisionados con los orígenes/versiones documentados. Solo fixtures ficticios; ningún expediente privado en el clon.
- Antes de conectar Sonar: revisión de saneamiento del contenido y nombres, configuración CI presente, análisis automático desactivado, proyecto Cloud privado. GitHub Pro/Team/Enterprise y Sonar Team/Enterprise para las capacidades elegidas; verificar disponibilidad, no contratar automáticamente.
- Variables públicas de proyecto/organización y `SONAR_TOKEN` aprovisionados por el responsable en almacenes de secretos; nunca pegarlos en comandos o documentos.

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
gitleaks dir --redact .
python -m pre_commit install
python -m pre_commit run --all-files
```

Esperado: pruebas recolectadas y aprobadas; XML válido con líneas productivas; código existente en verde, sin exclusiones globales. Repetir generación y pruebas conserva resultados. Los expedientes reales nunca son necesarios. El escaneo de directorio complementa, no sustituye, el escaneo de commits de CI.

## Medición local con expedientes externos

La ruta se configura localmente mediante `EXPEDIENTES_REFERENCIA_DIR`, fuera del repositorio, sin imprimirla. El test lee y mide dentro de su cuerpo y solo devuelve resumen no identificable.

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
2. Preparar enmienda constitucional de TODO(SONAR) y la única excepción de arranque de PR 1. Añadir sonar y ci-required de cinco dependencias y gate de código nuevo del contrato.
3. Validación previa local y evidencias de hallazgos; commit/push; abrir PR 2.
4. Verificar cinco controles y agregado. Probar fallos individuales, omisión/cancelación, ausencia de cobertura/credenciales, umbrales, cambios pequeños y sin código productivo nuevo. Solo material ficticio; retirar pruebas antes de merge.
5. Verificar PR de Dependabot y documentación, sin auto-merge. No ensayo de forks ni escenario independiente de SHA obsoleto; mantener protección de rama actualizada y prohibición de pull_request_target.
6. Verificar protección de seis checks, PR obligatorio, cero reviews requeridas, sin bypass/force push. Si cambia código/configuración, nuevo commit/push y checks del SHA final.
7. Mergear PR 2 con todos los checks verdes.
8. Verificar ejecución completa en main después del merge; solo entonces declarar F1 terminada. Registrar evidencia posterior en el PR, sin commits directos a main.
