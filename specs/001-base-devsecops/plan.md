# Implementation Plan: F1 · Base DevSecOps

**Branch**: `feature/f1_devsecops` | **Date**: 2026-09-17 | **Spec**: [spec.md](spec.md)

**Input**: `specs/001-base-devsecops/spec.md`, incluidas las cuatro aclaraciones del usuario.

## Summary

Sanear el contenido actual y los nombres de fixtures antes de activar cualquier análisis. Conservar los casos existentes con un expediente sintético generado, convertir los scripts de pruebas a pytest y dejar el código existente en verde. Implantar cinco controles automáticos y un resultado agregado que bloquee cualquier revisión incompleta. SonarQube Cloud analiza desde CI; `main` permanece privada, exige PR y checks, sin aprobaciones de revisores con un mantenedor. F1 no reescribe historia ni migra el núcleo a una arquitectura nueva. PR 1 contiene etapas 1–5 con cuatro controles; después el usuario conecta Cloud y analiza main saneada. PR 2 añade sonar y ci-required, atiende hallazgos existentes, formaliza la excepción constitucional y activa protección completa.

## Technical Context

**Language/Version**: Python 3.13 como versión objetivo de CI y del entorno local; no matriz adicional en F1. Validar instalación del conjunto fijado en esa versión antes de activar workflows.

**Primary Dependencies**: Se reutilizan `requirements.txt` y sus bibliotecas: RapidOCR/onnxruntime, PyMuPDF, openpyxl, Pillow, rapidfuzz, spylls, Streamlit y pandas. Añadir únicamente herramientas solicitadas de desarrollo: ruff, pytest, pytest-cov, pip-audit y pre-commit, fijadas en `requirements-dev.txt`; acciones y gitleaks fijados a revisiones verificadas. La selección de parches y hashes exactos se ejecuta al implementar y queda versionada, no se instala `latest` en CI.

**Storage**: Sin base de datos nueva. Fixtures sintéticos regenerables, cobertura XML y evidencia saneada por ejecución. Expedientes reales solo en directorio externo local, sin artefactos de contenido.

**Testing**: pytest con marker registrado `local_reference`, excluido por defecto; CI lo excluye explícitamente. Cobertura de módulos productivos, incluidos los no importados, sin tests ni generador en el denominador. Sonar distingue producción de tests y aplica cobertura nueva >=80 %; no imponer 80 % global como sustituto del umbral de código nuevo.

**Target Platform**: Runner efímero Ubuntu 24.04 de GitHub Actions, Python 3.13 y LibreOffice headless para formatos antiguos. OCR y diccionario se aprovisionan antes de pruebas, con versiones/origen comprobados; ningún test obtiene expedientes externos. No se exige GPU.

**Project Type**: Herramientas Python existentes y automatización de desarrollo, sin nueva interfaz ERP.

**Performance Goals**: No hay SLA de duración en la spec. Timeout operativo de 30 minutos por job y 300 segundos para esperar el Quality Gate; expirar significa fallo, nunca aprobación. Ajustar solo con medición si la primera ejecución fría lo requiere.

**Constraints**: Privacidad, repo privado, sin reescritura de historia, sin exclusiones globales de reglas; code smells Sonar existentes como deuda F3 no bloqueante, sin llamadas IA en ERP o tests CI. Las capacidades de las cuentas son prerrequisitos verificables de activación, no supuestas como ya contratadas.

**Scale/Scope**: Un repositorio, un mantenedor, cinco grupos de controles en cada PR y push a `main`. F1 únicamente.

## Constitution Check

| Principio | Comprobación inicial y diseño final |
|---|---|
| I. Determinismo / sin IA | Generador reproducible; mismos casos y resultados. No ejecutar clientes de modelos. La prueba determinista de filtrado existente puede conservarse sin invocar servicios. No integrar prosa experimental al ERP. |
| II. Núcleo puro | No ampliar acoplamientos; la separación completa ya está asignada a F3. Adaptación Linux limitada al adaptador de formatos existente. |
| III. Tests primero | Antes de corregir comportamiento del núcleo o adaptador, crear prueba fallida ficticia. Medición local de no regresión obligatoria si cambia el núcleo. |
| IV. Privacidad | Saneamiento local previo a importar en Cloud, también rutas, referencias e informes. Historial retenido privado no autoriza enviar datos históricos. |
| V. Simplicidad | Un workflow, configuración nativa y bibliotecas existentes. Sin servicio, base de datos, motor de políticas ni framework nuevo. |
| VI. Seguridad | Credenciales solo para escáner aislado, permisos mínimos, ejecutores efímeros; no ejecución privilegiada de PR desconocidos. |
| VII. DevSecOps | Cinco controles, agregado estricto, puerta de calidad constitucional y protección real. PR 1 integra cuatro controles; análisis inicial de main por el usuario; enmienda TODO(SONAR) y excepción única en PR 2. Excepción única autorizada expresamente por el usuario; formalización constitucional en PR 2. |
| VIII. Usabilidad | No hay pantallas nuevas. Resultados de CI legibles, asociados a revisión y sin datos sensibles. |

**Resultado previo a investigación**: compatible con el alcance F1 y las decisiones explícitas. La deuda estructural existente corresponde a F3; no se declara resuelta en F1.

**Resultado posterior al diseño**: arranque autorizado por la cláusula de la constitución v1.3.0, sin bypass ni enmienda pendiente; la conexión inicial está condicionada al saneamiento verificado y capacidades de las cuentas; la enmienda se formaliza en PR 2 conforme a la autorización expresa del usuario. La enmienda debe precisar el alcance de contenido enviado frente al historial privado retenido, de acuerdo con la decisión explícita del usuario. Si no se puede garantizar ese límite, NO se activa el análisis; no se justifica una excepción de privacidad mediante Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-base-devsecops/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/ci.md
└── checklists/requirements.md
```

`tasks.md` organiza la implementación en las seis etapas solicitadas, cada una con checkpoint y commit al cierre.

### Source Code (repository root)

```text
.github/workflows/ci.yml           # cinco controles + agregado
.github/dependabot.yml            # pip y github-actions, semanal
.pre-commit-config.yaml           # lint, formato y gitleaks
pyproject.toml                    # ruff, pytest, cobertura
requirements.txt                 # producción existente, corregir vulnerabilidades
requirements-dev.txt             # herramientas solicitadas con versiones fijadas
sonar-project.properties          # análisis CI y cobertura
scripts/generar_fixtures.py       # expediente ficticio reproducible
tests/                           # nuevas pruebas y fixtures
    fixtures/                    # solo archivos generados ficticios
    conftest.py                  # selección local explícita y recursos
    test_referencia_local.py     # medición real solo local
test_*.py                       # scripts actuales convertidos a tests recolectables
extraer.py                       # adaptación mínima del lector legacy a Linux
verificar.py, lexico.py, ortografia.py  # saneamiento / correcciones necesarias
.gitignore                      # artefactos y datos locales, no desproteger expedientes
AGENTS.md, docs/roadmap.md       # comandos F1 y avance solo tras validación real
.specify/memory/constitution.md # v1.3.0 ya vigente: no requiere enmienda en F1
```

**Structure Decision**: Mantener módulos y tests actuales en raíz para reducir movimiento. `tests/` contiene nuevos fixtures y pruebas específicas; pytest descubre ambos ubicaciones. El generador se ejecuta explícitamente y no requiere desactivar las exclusiones de documentos privados: sus salidas pueden permanecer ignoradas y se regeneran desde el script versionado. `ci-required` usa exactamente cinco dependencias en `needs`, `if: always()` y un único paso shell con la comparación definida en `contracts/ci.md`; no requiere script ni suite propios. El resto del código existente permanece dentro del lint y la revisión de hallazgos.

## Secuencia de implementación

1. Inventario local de datos sensibles sin copiar valores a logs; saneamiento de código/tests/rutas, nombres de fixtures neutros y actualización de referencias. No importar aún proyecto Cloud ni activar escaneos remotos. Documentar alcance de revisión, no los datos eliminados.
2. Generador sintético y conversión a pytest: casos de extracción/OCR, tablas, documentos legacy, notas, comparación de borradores correctos e incorrectos, léxico y ortografía. Conservar casos de filtrado determinista existentes sin llamadas IA. Aislar medición real tras selección local y fallar de forma saneada si faltan archivos.
3. Corregir compatibilidad de `textutil` en Linux en el adaptador compartido usando LibreOffice headless con directorio temporal y perfil aislado, errores controlados y pruebas de preservación de formatos. Mantener comportamiento existente en macOS cuando corresponda. No migrar el núcleo en F1.
4. Configurar herramientas y llevar código existente a verde: ruff con E4/E7/E9/F y S, formato, tests y auditoría estricta. Configurar `[tool.ruff.lint.per-file-ignores]` con `"test_*.py" = ["S101"]` y `"tests/**" = ["S101"]`: permite asserts de pruebas sin justificar cada uno. La justificación de esta política se documenta una vez en el PR. S101 permitido en tests por per-file-ignores; cualquier otra excepción S solo como noqa individual con código y motivo, listada en el PR. Las excepciones de otras herramientas conservan justificación individual; no excluir archivos para esconder hallazgos.
5. PR 1: añadir únicamente lint, tests, dependencies y secrets en CI, pre-commit y Dependabot; no crear jobs sonar ni ci-required. Preparar `sonar-project.properties` sin conexión automática, para usar análisis basado en CI después. Validación previa → commit/push → PR en borrador → cuatro checks verdes → merge sin bypass → verificación de main. La finalización de esta secuencia completa etapas 1–5, no F1.
6. Tras PR 1, el usuario conecta Cloud privado y ejecuta el primer análisis de main saneada con su cobertura; no analizar commits anteriores. PR 2: atender vulnerabilidades, bugs y Security Hotspots existentes, corregidos o justificados por escrito; registrar code smells existentes como deuda F3 no bloqueante. Añadir sonar y ci-required de cinco dependencias, gate y protección final; la constitución v1.3.0 ya resolvió TODO(SONAR) y la cláusula de arranque. Validación previa → commit/push → PR 2 → seis checks verdes → merge sin bypass → verificación de main. No declarar F1 completa antes de esta última comprobación.


## Complexity Tracking

Sin abstracciones ni dependencias no solicitadas. Las herramientas de calidad son requisitos expresos. La pequeña adaptación Linux y el agregado se justifican por fallos concretos de compatibilidad y de semántica de checks; no se aceptan violaciones constitucionales.
