# Quickstart de validación · F1

Esta guía describe la validación tras implementar el plan. Los comandos de F1 propuestos aún no existen completos en esta etapa; no se han ejecutado ni se afirma CI verde.

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
2. Añadir sonar y ci-required de cinco dependencias y el gate de código nuevo del contrato; la constitución v1.3.0 ya resolvió TODO(SONAR) y la cláusula de arranque.
3. Validación previa local y evidencias de hallazgos; commit/push; abrir PR 2.
4. Verificar cinco controles y agregado. Probar fallos individuales, omisión/cancelación, ausencia de cobertura/credenciales, umbrales, cambios pequeños y sin código productivo nuevo. Solo material ficticio; retirar pruebas antes de merge.
5. Verificar PR de Dependabot y documentación, sin auto-merge. No ensayo de forks ni escenario independiente de SHA obsoleto; mantener protección de rama actualizada y prohibición de pull_request_target.
6. Verificar protección de seis checks, PR obligatorio, cero reviews requeridas, sin bypass/force push. Si cambia código/configuración, nuevo commit/push y checks del SHA final.
7. Mergear PR 2 con todos los checks verdes.
8. Verificar ejecución completa en main después del merge; solo entonces declarar F1 terminada. Registrar evidencia posterior en el PR, sin commits directos a main.
