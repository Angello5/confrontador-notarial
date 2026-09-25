# Feature Specification: F13 · Anclaje por ficha oficial

**Feature Branch**: `feature/f13-anclaje-fichas` (sobre F12)

**Created**: 2026-09-25

**Status**: Draft

**Input**: Medido sobre los recaudos de los 10 expedientes reales (369 páginas): 55 fichas oficiales producen 49 personas confirmadas (89 %), pero alrededor aparecen 47 registros con nombre sin documento, 33 con documento sin nombre y 64 marcas de revisión manual: **unas tres filas por persona real**. El propietario fija el principio: un legajo puede traer varios DNI de varias personas, y lo que identifica a cada una es **la estructura de la ficha RENIEC y la de la biométrica**.

## Principio

**Cada ficha oficial (RENIEC o biométrica) es un ancla: una persona.** Las demás fuentes —declaración jurada manuscrita, SUNARP, prosa, DNI escaneado— solo pueden **adjuntar** datos a un ancla. Nunca crean una persona ni cruzan dos.

## Clarifications

### Session 2026-09-25

- Q: ¿Por qué no basta con unificar mejor? → A: Porque el problema es de origen, no de fusión. Un nombre manuscrito mal leído no debe competir con el de RENIEC; debe pegarse a él o descartarse.
- Q: ¿Qué pasa con un compareciente que no tiene ficha en el legajo? → A: Sigue verificándose por la capa de campos de siempre (`revisar()` sobre nombres y documentos sueltos), que no cambia. Además queda listado aparte como "mención sin ficha", para que el notario vea que falta su ficha. No entra en las reglas por persona (documento cruzado, estado civil, edad, domicilio), que exigen ancla.
- Q: ¿Se pierden personas? → A: No. Toda persona confirmada hoy que provenga de una ficha sigue existiendo. Las que hoy se confirman solo por prosa pasan a "mención sin ficha".

## Requirements *(mandatory)*

- **FR-001**: Solo las páginas RENIEC y BIOMETRICA DEBEN crear personas. Una ficha, una persona, con su documento y sus procedencias.
- **FR-002**: Un registro de fuente no oficial con documento DEBE adjuntarse al ancla con ese documento exacto; si no existe ancla, queda como mención sin ficha, no como persona.
- **FR-003**: Un registro de fuente no oficial con solo nombre DEBE adjuntarse al ancla cuyo nombre normalizado coincida exactamente y sea única; en cualquier otro caso queda como mención sin ficha.
- **FR-004**: Ante discrepancia entre un ancla y una fuente no oficial, manda el ancla y NO se marca conflicto. La revisión manual queda solo para discrepancias **entre anclas** (dos fichas de la misma persona con datos distintos), donde manda la de emisión más reciente, como en F12.
- **FR-005**: Dos anclas con el mismo documento y el mismo nombre normalizado DEBEN unificarse; con distinto documento, nunca, aunque el nombre coincida.
- **FR-006**: El cónyuge de la declaración jurada DEBE adjuntarse al ancla del declarante como atributo `conyuge` (nombre), no como persona.
- **FR-007**: La tabla de extracción DEBE mostrar anclas, sus adjuntos con procedencia y, aparte, las menciones sin ficha con su origen.
- **FR-008**: La capa de campos (`revisar`, `correspondencia`, `diagnostico`) y la proyección `cat["NOMBRE"]`, `cat["DNI"]` NO DEBEN cambiar: siguen viendo todos los nombres y documentos, vengan de donde vengan.
- **FR-009**: Sin migraciones ni entidades nuevas.

### Seguridad y privacidad (Constitución I, II, IV)

Núcleo puro y determinista; sin IA, red ni dependencias nuevas; datos personales nunca en logs ni en el JSON de sondeo; solo datos ficticios en pruebas y documentación.

## Success Criteria *(mandatory)*

Medidos con el mismo guion sobre los mismos 10 expedientes (barrido crudo local), antes y después:

- **SC-001**: Personas confirmadas desde fichas: **≥ 49** (ninguna pérdida).
- **SC-002**: Registros con nombre sin documento presentados como personas: **0** (pasan a adjuntos o menciones).
- **SC-003**: Registros con documento sin nombre presentados como personas: **0**.
- **SC-004**: Marcas de revisión manual: **solo entre anclas**; sobre estos expedientes, ≤ 6 (hoy 64).
- **SC-005**: Las observaciones de la capa de campos son idénticas antes y después sobre entradas ficticias.
- **SC-006**: Ningún dato real en el diff.

## Assumptions

- `docs/catalogo-datos.md` (orden de confianza) y `docs/catalogo-fuentes.md` son la referencia.
- Las 6 fichas oficiales que hoy no producen persona (3 solo documento, 3 solo nombre) son un problema de lectura OCR y quedan fuera de esta fase, anotadas como deuda.
- El guion de medición vive fuera del repositorio porque usa expedientes reales; el spec fija los números, no el guion.
- Consecuencia aceptada por el propietario (2026-09-25): dos comparecientes **sin ficha** con los documentos intercambiados ya no producen `DOCUMENTO_CRUZADO`, porque el titular de esa regla debe ser un ancla. La capa de campos tampoco lo señala, ya que ambos documentos están en las fuentes.
- Cónyuge (aclaraciones del propietario, 2026-09-25): si el declarante no queda identificado, el cónyuge se queda en la mención del declarante o, si no hay declarante, en una mención propia `SIN_FICHA` sin nombre; nunca se descarta. Si dos declaraciones con cónyuges distintos se pegan al mismo ancla, el ancla muestra el primero por orden de página, cada adjunto conserva el suyo y no hay marca de revisión.
