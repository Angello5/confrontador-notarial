# Feature Specification: Migración del núcleo puro

**Feature Branch**: `003-migracion-nucleo-puro`

**Created**: 2026-09-18

**Status**: Implementado e integrado (PR #17)

**Input**: User description: "Convertir los módulos actuales (extraer, verificar, léxico, ortografía) en un núcleo de funciones puras, sin interfaz, conservando exactamente el resultado medido en el expediente de referencia. La capa de prosa (revisor_llm.py, bench_llm.py) se mueve a experimental/. Se atiende la deuda registrada en docs/deuda-f3.md (code smells de SonarCloud, riesgo residual de antlr4, API key en query de revisor_llm) y la decisión sobre actualizar RapidOCR (PR de Dependabot #11, bloqueado por cambio de modelos con hash), que exige medición de calidad de OCR antes de cambiar la configuración."

## Clarifications

### Session 2026-09-18

- Q: ¿Qué organización de paquetes debe adoptar el núcleo puro? → A: Un paquete común (por ejemplo, `nucleo/`) mantiene `verificar`, léxico y ortografía casi como están; extracción queda como adaptador separado para OCR y archivos. Solo se separa lo que exige el principio II: el núcleo no usa sistema de archivos, red ni OCR; la descarga del diccionario `es_PE` pasa a un adaptador.
- Q: ¿Qué debe ocurrir con las aplicaciones Streamlit y los módulos de prosa durante F3? → A: `app.py` y `app_ortografia.py` siguen funcionando hasta la paridad del ERP en F4/F5 y durante F3 solo se adaptan a los nuevos imports. `revisor_llm.py` y `bench_llm.py` pasan a `experimental/`; el ERP no los importa.
- Q: ¿Qué alternativa OCR se debe evaluar y qué evidencia permite cambiar la configuración actual? → A: Se adopta PP-OCRv5 latin con `use_cls=False`: T014 fue ejecutada por la persona usuaria el 2026-09-18 sobre `8a344fb`, con 1 prueba aprobada en 10,23 s, OCR real y cero archivos `.json` residuales en la caché; el gate confirmó 8 observaciones, cinco salidas idénticas, 0 observaciones en la escritura correcta y el piso sintético. El PR #11 de Dependabot (RapidOCR 3.9.2) queda sustituido por esta decisión y lo cerrará el coordinador al publicar el PR de F3.
- Q: ¿Qué rótulos de DNI y forma de nombre se conservan en la verificación? → A: Se conserva la equivalencia de la regex original para `DNI`/`IDENTIDAD` y sus rótulos, se acepta además `D.N.I.` y `D.N.I` sin punto final por decisión del usuario del 2026-09-18, y se rechazan letras separadas por espacios y coincidencias dentro de palabras. `RE_NOMBRE` mantiene el cuantificador lazy para conservar nombres antes de `DE NACIONALIDAD` aun sin coma, con entrada ficticia cubierta por test.

## User Scenarios & Testing

### User Story 1 - Ejecutar las capas deterministas (Priority: P1)

El equipo de desarrollo puede invocar extracción de campos desde texto, verificación, léxico y ortografía como lógica independiente de la interfaz y de los servicios externos. La entrada de texto o estructuras produce resultados reproducibles. La extracción de texto desde archivos pertenece al adaptador.

**Why this priority**: El núcleo puro es el resultado central de F3 y habilita su prueba y reutilización desde las fases posteriores.

**Independent Test**: Invocar cada capa con datos sintéticos y comprobar que devuelve sus resultados sin requerir una interfaz, Django, base de datos, OCR ni sistema de archivos.

**Acceptance Scenarios**:

1. **Given** entradas sintéticas idénticas, **When** se ejecutan repetidamente las capas del núcleo, **Then** cada ejecución devuelve el mismo resultado.
2. **Given** las entradas del conjunto sintético, **When** se ejecuta una capa por separado, **Then** el resultado se puede comprobar sin iniciar una interfaz o servicio externo.

### User Story 2 - Preservar los resultados medidos (Priority: P1)

El equipo puede comprobar que la migración conserva la medición existente del expediente de referencia y no introduce falsos positivos.

**Why this priority**: La constitución exige preservar el comportamiento medido y prohíbe integrar cambios que empeoren la medición privada.

**Independent Test**: Ejecutar la prueba de referencia local autorizada fuera del repositorio y comparar conteo, falsos positivos y resultados repetidos sin registrar contenido del expediente.

**Acceptance Scenarios**:

1. **Given** el expediente de referencia y el código migrado, **When** se ejecuta la medición privada, **Then** se conservan 8 de 8 errores detectados y 0 falsos positivos.
2. **Given** cinco ejecuciones de la misma medición, **When** se comparan sus salidas, **Then** todas son idénticas y ninguna incluye datos del expediente en logs o errores.
3. **Given** la escritura correcta de referencia, **When** se ejecuta la confrontación, **Then** no se producen observaciones.

### User Story 3 - Mantener fuera del ERP la capa de prosa (Priority: P2)

El equipo puede conservar la capa de prosa existente en el área experimental sin que el ERP ni el núcleo la importen, desplieguen o usen.

**Why this priority**: La constitución prohíbe modelos de lenguaje en el ERP y asigna esa capa a `experimental/`.

**Independent Test**: Revisar las dependencias e imports del núcleo y comprobar que no incluyen los módulos de prosa ni requieren sus dependencias.

**Acceptance Scenarios**:

1. **Given** la estructura resultante de F3, **When** se inspecciona el núcleo y su paquete productivo, **Then** no importan `revisor_llm.py`, `bench_llm.py` ni modelos de lenguaje.
2. **Given** el código de prosa conservado, **When** se consulta su ubicación, **Then** `revisor_llm.py` y `bench_llm.py` viven bajo `experimental/` y no participan en las pruebas ordinarias del núcleo.

## Edge Cases

- Si la medición de referencia no está disponible localmente, las pruebas predeterminadas siguen siendo ejecutables con datos ficticios y la medición privada no se sustituye por datos reales versionados.
- Si falta un recurso OCR/diccionario público fijado por hash, la verificación debe identificar el recurso ausente o inválido; no debe cambiar silenciosamente la configuración.
- Si falla la carga/compilación de la dependencia transitiva `antlr4-python3-runtime`, el error no debe exponer documentos ni secretos.
- Si cambian los hashes de los modelos OCR o `use_cls`, el texto cacheado con la configuración anterior no se reutiliza.
- Las peticiones de `revisor_llm.py` no deben enviar la API key dentro de la URL. La ubicación experimental no autoriza al ERP a importar o ejecutar la capa de prosa.

## Requirements

### Functional Requirements

- **FR-001**: El sistema MUST ofrecer extracción de campos desde texto, verificación, léxico y ortografía como operaciones deterministas del núcleo que reciben texto o estructuras y devuelven resultados.
- **FR-002**: La lógica del núcleo MUST permanecer independiente de Django, base de datos, OCR y sistema de archivos; la extracción de texto desde archivos y el OCR son operaciones del adaptador externo al núcleo.
- **FR-003**: Las pruebas predeterminadas MUST usar exclusivamente fixtures y datos ficticios.
- **FR-004**: La migración MUST conservar la medición del expediente de referencia: 8 de 8 errores, 0 falsos positivos, cero observaciones en la escritura correcta y salidas idénticas en ejecuciones repetidas. La medición privada se ejecuta fuera del repositorio y no se ejecuta en CI.
- **FR-005**: El código de prosa `revisor_llm.py` y `bench_llm.py` MUST ubicarse en `experimental/`; el ERP y el núcleo MUST no importarlos, desplegarlos ni depender de sus dependencias.
- **FR-006**: La deuda de los diez code smells registrados en `docs/deuda-f3.md` MUST revisarse durante F3 y su resolución o justificación debe quedar verificable sin cambiar reglas de negocio no acordadas.
- **FR-007**: La estrategia de instalación de `antlr4-python3-runtime==4.9.3` MUST revisarse para reducir el riesgo de su aislamiento de compilación descrito en `docs/deuda-f3.md`, preservando instalación verificable por hash.
- **FR-008**: La capa de prosa MUST evitar enviar la API key en la query URL. Las pruebas de esa capa no deben llamar a modelos ni registrar credenciales.
- **FR-009**: RapidOCR 3.4.3 y onnxruntime 1.30.0 MUST quedar fijados con hashes en los locks. Los modelos OCR se fijan por SHA-256 en el paso de verificación de recursos del CI y en `quickstart.md`, separados de los hashes de paquetes Python; la aplicación no descarga recursos en tiempo de ejecución.
- **FR-010**: El núcleo MUST organizar extracción de campos desde texto, `verificar`, léxico y ortografía en un paquete común (por ejemplo, `nucleo/`) manteniendo su lógica casi como está; extracción de texto desde archivos y OCR MUST quedar en un adaptador separado. El núcleo no importa ni usa sistema de archivos, red u OCR; la descarga del diccionario `es_PE` pertenece a un adaptador.
- **FR-011**: `app.py` y `app_ortografia.py` MUST seguir funcionando hasta que el ERP alcance paridad en F4/F5 y durante F3 solo se adaptan a los nuevos imports. `revisor_llm.py` y `bench_llm.py` MUST moverse a `experimental/`; el ERP no los importa.
- **FR-012**: El detector predeterminado es PP-OCRv5 mobile y el reconocedor sigue siendo PP-OCRv5 latin mobile, con `use_cls=False`. El cambio de detector se apoya en la medición agregada del PR #37 (50 frente a 46 personas completas en 300 páginas; 14 % más rápido); la comprobación privada de exactitud queda pendiente del propietario. El reconocedor ya cumplió el test sintético ordinario (8/8 líneas, al menos 82/85 palabras y 31/32 diacríticos) y T014 (8 observaciones, cinco salidas idénticas y 0 observaciones en la escritura correcta). La medición sintética detallada permanece opt-in. La metadata `character` del reconocedor v5 incluye Ñ/ñ; una Ñ aislada puede descartarse y causar una observación dentro de un nombre. T014 no se ejecuta en CI.

### Key Entities

- **Entrada de confrontación**: Texto o estructura ficticia que una operación del núcleo procesa.
- **Resultado de capa**: Salida determinista de la extracción de campos desde texto, verificación, léxico u ortografía. La extracción de texto desde archivos produce la entrada de texto del núcleo.
- **Medición de referencia**: Comparación local y privada de resultados, conteo de errores y falsos positivos; sus documentos no se versionan.
- **Configuración OCR**: Versiones de RapidOCR y de modelos fijados por origen y SHA-256.

## Success Criteria

### Measurable Outcomes

- **SC-001**: En la medición privada, el núcleo detecta 8 de 8 errores, produce 0 falsos positivos y cero observaciones en la escritura correcta.
- **SC-002**: Cinco corridas con la misma entrada de referencia producen salidas idénticas.
- **SC-003**: La suite predeterminada puede ejecutarse íntegramente con datos ficticios y sin acceso al directorio privado de referencia.
- **SC-004**: El código del núcleo y las dependencias productivas no contienen imports ni llamadas a la capa de prosa o a modelos de lenguaje.
- **SC-005**: La verificación de los recursos OCR/diccionario comprueba los hashes documentados antes de ejecutar pruebas que los requieren.
- **SC-006**: La prueba sintética ordinaria mantiene el piso medido de PP-OCRv5 (8/8 líneas, ≥82/85 palabras, ≥31/32 diacríticos); T014 confirma 8 observaciones, cinco salidas idénticas y 0 observaciones en la escritura correcta antes de cerrar la etapa. La metadata v5 contiene Ñ/ñ; se documenta el comportamiento de una Ñ aislada y su efecto en nombres.

## Assumptions

- La línea base de comportamiento es la medición F1 documentada en la constitución y el quickstart: 8 errores detectados, 0 falsos positivos y salida idéntica en ejecuciones repetidas.
- La medición privada se realiza por el usuario en su entorno autorizado; el código, tests, logs y commits solo contienen datos ficticios.
- Los tests predeterminados usan pytest y los recursos públicos OCR/diccionario fijados por hash que documenta `specs/001-base-devsecops/quickstart.md`.
- Esta fase solo especifica y planifica la migración del núcleo; la especificación no ejecuta cambios de código de migración.
- Las reglas de negocio existentes se conservan; cualquier regla nueva requiere decisión explícita y prueba primero.
- RapidOCR usa la metadata `character` (502 caracteres) incrustada en el ONNX v5 e ignora `rec_keys_path`; `ppocrv5_dict.txt` no se usa. T014 fue aprobada el 2026-09-18; el resultado agregado se conserva en `quickstart.md`.
