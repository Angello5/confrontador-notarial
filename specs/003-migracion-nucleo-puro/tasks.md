# Tasks: Migración del núcleo puro

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`

**Organization**: Las etapas fijan orden, checkpoint y commit local; las etiquetas US conservan trazabilidad con las tres historias. Tests sintéticos preceden cambios en lógica o comportamiento. Nunca usar/añadir documentos reales.

## Etapa 1: Pruebas de caracterización y límites (Setup/Foundation)

**Propósito**: demostrar el comportamiento actual con datos ficticios y detectar E/S indebida desde el núcleo antes de refactorizar.

- [ ] T001 [P] Añadir pruebas ficticias de frontera para la extracción de campos desde texto, verificación, léxico y ortografía en `tests/test_nucleo_puro.py`; comprobar que importar reglas del núcleo no importa el adaptador de extracción de texto desde archivos, OCR, red ni accede a rutas, y usar las rutas finales `nucleo/`.
- [ ] T002 [P] Añadir casos sintéticos de líneas, acentos y Ñ que caractericen la extracción de texto desde archivos/OCR actual en `test_extraer.py`.
- [ ] T003 Registrar en `specs/003-migracion-nucleo-puro/quickstart.md` los resultados agregados de caracterización sintética y los comandos reproducibles, sin copiar salidas que contengan documentos.

**Criterio independiente**: las pruebas de pureza fallan primero ante las importaciones/accesos actuales; las pruebas de caracterización de funciones documentan resultados ficticios reproducibles.

**Checkpoint y commit local**: validar solo tests sintéticos y crear un commit de la etapa con los archivos de test y `specs/003-migracion-nucleo-puro/quickstart.md`.

## Etapa 2: Núcleo puro y adaptadores (US1, P1)

**Meta**: extraer funciones deterministas a un paquete común y poner E/S detrás de adaptadores.

**Prueba independiente**: ejecutar cada capa con entradas sintéticas sin iniciar Streamlit, OCR, red, Django ni acceso a archivos; mismas entradas dan las mismas salidas.

- [ ] T004 [US1] Crear el paquete `nucleo/` y mover las funciones de dominio de `verificar.py` a `nucleo/verificar.py`, eliminando su importación de `extraer.py` sin cambiar reglas.
- [ ] T005 [US1] Mover la lógica léxica de `lexico.py` a `nucleo/lexico.py` y retirar su dependencia de lectura/extracción mediante entrada de texto recibida.
- [ ] T006 [US1] Separar reglas de `ortografia.py` hacia `nucleo/ortografia.py` y extraer lectura/escritura de lista de casa y carga del diccionario a `adaptadores/diccionario.py`.
- [ ] T007 [US1] Mover lectura/conversión/OCR de `extraer.py` a `adaptadores/extraccion.py`, conservando formatos admitidos y outputs sintéticos.
- [ ] T008 [US1] Actualizar `test_verificar.py`, `test_lexico.py`, `test_ortografia.py` y `test_extraer.py` para importar las nuevas rutas y mantener todos los asserts con fixtures ficticios.
- [ ] T009 [US1] Completar primero los casos faltantes de pureza en `tests/test_nucleo_puro.py` y comprobar que el núcleo no importa ni usa `pathlib`, urllib, OCR o funciones de acceso al sistema de archivos.
- [ ] T010 [US1] Actualizar `specs/003-migracion-nucleo-puro/data-model.md` y `specs/003-migracion-nucleo-puro/quickstart.md` si las firmas internas elegidas difieren del plan, sin documentar rutas ni datos privados.

**Checkpoint y commit local**: tests de US1 verdes, formato/lint afectados verdes y salidas sintéticas preservadas; crear un commit de la etapa.

## Etapa 3: Preservación medida y decisión OCR (US2, P1)

**Meta**: verificar resultado de referencia y comparar ambas configuraciones OCR con hashes reproducibles.

**Prueba independiente**: evidencia agregada acredita 8 observaciones, 0 en la escritura correcta, cinco corridas idénticas y test sintético sin pérdida de líneas ni acentos/Ñ.

- [ ] T011 [US2] Fijar versiones de RapidOCR/onnxruntime como paquetes Python en `requirements.in` y su lock `requirements.txt`. Registrar por separado los SHA-256 de modelos/diccionarios OCR en el paso o manifiesto de verificación de recursos del CI y en `specs/003-migracion-nucleo-puro/quickstart.md`; validar esos recursos antes de correr la comparación.
- [ ] T012 [US2] Añadir primero en `test_extraer.py` la prueba sintética comparativa v4/v5 para conservar líneas, acentos y Ñ; ejecutarla con modelos fijados antes de cambiar la configuración predeterminada.
- [ ] T013 [US2] Implementar en `adaptadores/extraccion.py` la configuración candidata PP-OCRv5 latin con `use_cls=False`, manteniendo disponible la configuración PP-OCRv4 ch para comparación y fallback.
- [ ] T014 [US2] [REQUIERE MEDICIÓN LOCAL DE LA PERSONA USUARIA] Ejecutar `tests/test_referencia_local.py` con cada configuración desde el entorno autorizado, fuera de CI/repositorio; comunicar solo conteos y booleanos, nunca texto, imágenes, rutas ni logs del expediente.
- [ ] T015 [US2] Aplicar el gate de `specs/003-migracion-nucleo-puro/spec.md`: seleccionar v5 solo con 8 observaciones, cinco salidas idénticas, cero en escritura correcta y test sintético sin pérdidas; en otro caso conservar v4 y registrar motivo agregado en `specs/003-migracion-nucleo-puro/quickstart.md`.
- [ ] T016 [US2] Registrar en `specs/003-migracion-nucleo-puro/quickstart.md` el resultado agregado y recomendar al responsable cerrar o reemplazar el PR #11 según la decisión; no editar el PR desde esta etapa.

**Checkpoint y commit local**: hashes verificados, test sintético verde y decisión documentada. El commit de la etapa incluye la configuración elegida y evidencia únicamente agregada. T014 bloquea esta etapa hasta recibir el resultado local.

## Etapa 4: Compatibilidad Streamlit, prosa y deuda (US3, P2)

**Meta**: conservar interfaces transitorias, aislar prosa y atender deuda de Sonar/instalación con cambios mínimos.

**Prueba independiente**: ambos comandos Streamlit inician con imports nuevos; tests ordinarios no importan prosa; riesgos y los diez IDs tienen resolución o justificación comprobable.

- [ ] T017 [US3] Actualizar `app.py` para importar extracción/verificación de `adaptadores/` y `nucleo/`, preservando su ejecución Streamlit hasta paridad ERP.
- [ ] T018 [US3] Actualizar `app_ortografia.py` para importar ortografía/extracción de `nucleo/` y `adaptadores/`, preservando el flujo Streamlit hasta paridad ERP.
- [ ] T019 [US3] Mover `revisor_llm.py` y `bench_llm.py` a `experimental/`, adaptar sus imports del adaptador en `experimental/revisor_llm.py` y `app.py`, y mantener `test_revisor_llm.py` opt-in, fuera de la suite ordinaria, con ejecución explícita documentada sin red ni modelos; confirmar que ningún módulo del ERP/núcleo importa esos módulos.
- [ ] T020 [US3] Añadir primero en `test_revisor_llm.py` un test que demuestre que la API key no forma parte de la query URL; después cambiar `experimental/revisor_llm.py` para enviarla en el mecanismo de autenticación soportado y no imprimirla.
- [ ] T021 [US3] Resolver o justificar por ID los olores AaCzSzcyMhSFhiPLM0QS y AaCzSzcyMhSFhiPLM0QR en `app_ortografia.py`, con cambios mínimos y sin alterar comportamiento.
- [ ] T022 [US3] Resolver o justificar por ID los olores AaCzSzcYMhSFhiPLM0QI, AaCzSzcYMhSFhiPLM0QJ, AaCzSzcYMhSFhiPLM0QK y AaCzSzdRMhSFhiPLM0Qh en `test_extraer.py` y `test_ortografia.py`, manteniendo aserciones y datos ficticios.
- [ ] T023 [US3] Añadir primero en `test_verificar.py` cobertura sintética para regex/correspondencia/resultados; después resolver o justificar por ID AaCzSzZyMhSFhiPLM0QE, AaCzSzZyMhSFhiPLM0QF, AaCzSzZyMhSFhiPLM0QH y AaCzSzZyMhSFhiPLM0QG en `verificar.py`.
- [ ] T024 [US3] Validar en un entorno limpio el riesgo de antlr4 con `setuptools` fijado por hash y `--no-build-isolation`; actualizar `requirements.in`, `requirements.txt` y `requirements-dev.txt` solo si la instalación reproducible pasa; registrar cualquier riesgo residual en `specs/003-migracion-nucleo-puro/research.md`.
- [ ] T025 [US3] Verificar en `tests/conftest.py` y `.github/workflows/ci.yml` que la suite ordinaria excluye `experimental/`, no importa sus módulos ni ejecuta modelos; ajustar solo las reglas de recolección/test necesarias.

**Checkpoint y commit local**: smoke tests de ambas apps, tests deterministas, revisión por ID de los diez smells, tests de prosa sin red y validación de instalación completados; crear un commit de la etapa.

## Etapa 5: Gates y documentación (Polish)

- [ ] T026 Ejecutar `python -m ruff check .`, `python -m ruff format --check .`, `python -m pytest --cov --cov-report=term --cov-report=xml:coverage.xml` y `python -m pip_audit --strict -r requirements.txt -r requirements-dev.txt`; actualizar `specs/003-migracion-nucleo-puro/quickstart.md` con resultados sin datos reales.
- [ ] T027 Verificar imports productivos/CI sin IA, secretos, datos reales o recursos privados en el diff; documentar únicamente excepciones de deuda con IDs en `specs/003-migracion-nucleo-puro/research.md`.
- [ ] T028 Validar el Quality Gate de SonarQube en CI y `gitleaks` antes de declarar F3 lista; registrar estado y enlace de evidencia saneado en `specs/003-migracion-nucleo-puro/quickstart.md`.

**Checkpoint y commit local**: todos los gates de ejecución verdes, deuda resuelta/justificada y documentación actualizada; crear un commit local final de etapa.

## Dependencias y orden

- Etapa 1 precede a Etapa 2: caracteriza comportamiento y establece pruebas de frontera.
- Etapa 2 precede a Etapa 3: OCR compara el adaptador de extracción sobre las interfaces migradas.
- Etapa 3 precede a Etapa 4: la selección de modelos debe quedar decidida/documentada antes de cerrar configuración y dependencias.
- Etapa 4 precede a Etapa 5: los gates finales cubren todo el árbol resultante.
- Dentro de Etapa 4, T021 y T022 pueden hacerse en paralelo porque tocan archivos diferentes; T023 es independiente de T021/T022 salvo que T021 use funciones de la app.
- **MVP técnico**: Etapa 1 y Etapa 2 (US1). No completa F3 sin la medición de US2 y el aislamiento de US3.

## Conteo por etapa e historias

| Etapa | Tareas | Conteo | Dependencia del usuario |
|---|---|---:|---|
| 1. Caracterización | T001–T003 | 3 | Ninguna |
| 2. Núcleo puro | T004–T010 | 7 | Ninguna |
| 3. Medición/OCR | T011–T016 | 6 | T014: medición `local_reference` con referencia privada |
| 4. Streamlit/prosa/deuda | T017–T025 | 9 | Ninguna |
| 5. Gates/documentación | T026–T028 | 3 | Quality Gate depende de CI remoto |
| **Total** | **T001–T028** | **28** | **1 tarea requiere medición local de la persona usuaria** |

| Historia | Tareas asociadas | Prueba independiente |
|---|---|---|
| US1 | T004–T010 (7) | Lógica del paquete común con datos sintéticos, sin E/S, resultados iguales. |
| US2 | T011–T016 (6) | 8 observaciones, cero en escritura correcta, cinco corridas idénticas, OCR sintético conserva líneas/acentos/Ñ. |
| US3 | T017–T025 (9) | Apps Streamlit funcionan; ERP/núcleo no importan prosa; API key fuera de URL; deuda atendida o justificada. |

## Oportunidades paralelas

- T001 y T002 trabajan en archivos distintos y pueden avanzar en paralelo.
- En Etapa 4, T021 y T022 tocan grupos de archivos separados; solo paralelizar si se evita editar `app_ortografia.py` a la vez.
- No paralelizar las tareas OCR que preparan hashes, test comparativo, ejecución local y decisión: tienen dependencia estricta.

## Estrategia incremental

1. Completar Etapa 1 y detenerse en su checkpoint.
2. Migrar las reglas/adaptadores en Etapa 2 y validar US1 por separado.
3. Ejecutar Etapa 3 con participación de la persona usuaria antes de elegir OCR.
4. Completar Etapa 4 sin conectar prosa con el ERP y resolver/justificar todos los IDs de deuda.
5. Cerrar con gates locales, CI, Quality Gate de SonarQube y evidencia saneada de Etapa 5.
