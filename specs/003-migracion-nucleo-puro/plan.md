# Implementation Plan: Migración del núcleo puro

**Branch**: `003-migracion-nucleo-puro` | **Date**: 2026-09-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-migracion-nucleo-puro/spec.md`

## Summary

Migrar extracción de campos desde texto, verificación, léxico y ortografía a un paquete común de lógica pura, conservando sus reglas y resultados medidos. Mantener extracción de texto desde archivos/OCR y acceso a diccionarios en adaptadores; actualizar los imports de Streamlit durante la transición; mover los módulos de prosa a `experimental/`. La configuración OCR solo cambia a PP-OCRv5 latin si pasa todos los criterios locales de FR-012. Resolver los diez hallazgos de SonarCloud y el riesgo de instalación de antlr4, o dejar justificaciones verificables.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: Dependencias ya fijadas en `requirements.txt` y `requirements-dev.txt`; pytest, RapidOCR, onnxruntime, PyMuPDF y spylls ya existen. No añadir dependencias sin necesidad demostrada.

**Storage**: Sin base de datos. El núcleo recibe texto/estructuras y retorna resultados; los adaptadores conservan sus recursos locales fuera del núcleo.

**Testing**: pytest con fixtures ficticios por defecto. Tests del núcleo antes de los cambios de comportamiento. La medición `local_reference` es explícita, local y prohibida en CI; incluye la referencia externa que usa la persona responsable.

**Target Platform**: Python local en Linux y Windows; LibreOffice (`soffice`) para formatos legacy en Linux. Sin servicios de red en tiempo de ejecución del núcleo.

**Project Type**: Biblioteca interna de dominio con adaptadores CLI/archivos y dos interfaces Streamlit transitorias.

**Performance Goals**: No degradar materialmente los tiempos de lectura existentes; no se fija una meta numérica nueva sin una línea base medida.

**Constraints**: Comportamiento privado preservado: 8 observaciones, 0 falsos positivos, 0 observaciones en la escritura correcta y cinco corridas idénticas. PP-OCRv5 latin es el candidato predeterminado; el test ordinario debe sostener al menos su nivel sintético medido (8/8 líneas, 82/85 palabras, 31/32 diacríticos), y T014 sigue pendiente. La metadata `character` incrustada en el ONNX v5 contiene 502 caracteres, incluidos ñ/Ñ, Ú, Á e Í; RapidOCR ignora `rec_keys_path`. Una Ñ aislada puede descartarse; en palabras (SEÑORA, NÚÑEZ, MUÑOZ, ESPAÑA, ÑANDÚ) se lee bien, y su descarte dentro de un nombre genera observación. Solo datos ficticios en repo/logs; sin IA en el ERP; hashes de paquetes Python se guardan en `requirements*.txt` y hashes de modelos OCR en el paso/manifiesto de verificación de recursos del CI y en `quickstart.md`.

**Scale/Scope**: Migrar los módulos actuales y sus pruebas; no construir todavía flujo Django/ERP ni retirar Streamlit antes de paridad F4/F5.

## Constitution Check

**Pre-diseño: PASS**

- I. Determinismo: se preservan reglas y medición, y OCR no cambia sin gate aprobado.
- II. Núcleo puro: archivos/OCR, red y sistema de archivos quedan en adaptadores; el núcleo recibe valores y retorna resultados.
- III. Pruebas primero: pruebas sintéticas de regresión se escriben antes de mover o cambiar comportamiento; la referencia privada no entra al repo ni a CI.
- IV. Privacidad: usar fixtures ficticios; los logs y errores solo exponen estado agregado; referencia privada permanece fuera del worktree.
- V. Simplicidad: un paquete común, adaptadores solo para límites requeridos, sin dependencias ni abstracciones especulativas.
- VI. Seguridad: no desplegar/importar la capa de prosa desde el ERP; la API key no va en query URL. No se crea interfaz ERP en F3.
- VII. DevSecOps: lint, suite, SonarQube Quality Gate, `pip-audit` y `gitleaks` son gates de ejecución F3; no se ejecuta ni se declara gate remoto en esta etapa de planificación.
- VIII. Usabilidad: no aplica a cambios de núcleo; las apps Streamlit existentes siguen operativas y se adaptan a imports.

No hay violaciones justificadas ni complejidad adicional propuesta.

## Project Structure

### Documentation (this feature)

```text
specs/003-migracion-nucleo-puro/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── tasks.md
```

No se requieren contratos públicos: las funciones y adaptadores son interfaces internas de Python.

### Source Code (repository root)

```text
nucleo/
├── verificar.py       # reglas puras de confrontación
├── lexico.py          # reglas puras de vocabulario
└── ortografia.py      # reglas puras sobre texto/entradas recibidas

adaptadores/
├── extraccion.py      # extracción de texto desde archivos, OCR y conversión
└── diccionario.py     # aprovisionamiento/carga del diccionario es_PE

experimental/
├── revisor_llm.py
└── bench_llm.py

app.py                 # Streamlit conservado y adaptado a imports
app_ortografia.py      # Streamlit conservado y adaptado a imports
test_*.py              # tests ficticios del núcleo/adaptadores ya existentes
tests/                 # medición local y comprobaciones de fixtures
```

**Structure Decision**: Un paquete de dominio `nucleo/` concentra la extracción de campos desde texto y las demás reglas existentes con el menor traslado posible. `adaptadores/` contiene únicamente capacidades de extracción de texto desde archivos, E/S/OCR/red exigidas por el principio II. Las rutas definitivas y ajustes mínimos de imports se confirman al ejecutar tareas; no se crearán capas extra.

## Phase 0: Research

Las decisiones conocidas se basan en respuestas de clarificación, constitución, quickstart F1, módulos y tests existentes. No queda ninguna incógnita que requiera decisión de producto. La medición de OCR permanece como validación local pendiente de la persona usuaria, no como tarea de investigación automatizada.

## Phase 1: Design and Validation

- `data-model.md` define las entradas/salidas y el informe agregado de mediciones; no añade entidades persistidas.
- No se crea `contracts/`: no hay interfaz pública entre sistemas.
- `quickstart.md` fija comandos y resultados esperados para tests sintéticos, referencia privada y recursos OCR/diccionario.
- Las tareas posteriores se agrupan por etapas con checkpoint y commit local de documentación/implementación al cierre de cada etapa. Ningún commit incluye archivos fuera de `specs/003-*` durante esta planificación.

## Constitution Check (post-design)

**PASS, sujeto a gates de ejecución**: el diseño mantiene pureza, determinismo, tests ficticios, límites de privacidad y dependencias existentes. La configuración de esta rama es PP-OCRv5 latin, sujeta al test sintético de nivel y a la medición privada local T014 (8 observaciones, cinco corridas idénticas, cero observaciones en escritura correcta). La persona usuaria ejecuta T014; no se versionan expedientes ni resultados con contenido documental.

## Complexity Tracking

No hay violaciones de la constitución ni complejidad adicional que justificar.
