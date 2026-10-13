# Feature Specification: F16 · Nombres exigibles y domicilio por DNI

**Feature Branch**: `feature/f16-nombres-exigibles`

**Created**: 2026-09-27

**Status**: Implementado e integrado (PR #46 y #73). Pendiente: medición del revisor T007

**Input**: El revisor midió dos falsos positivos en un expediente real. (A) De 5 nombres de la proyección `NOMBRE`, 3 vienen de menciones sin ficha (declaración jurada manuscrita, OCR ilegible) y 1 es la variante adjunta de la biométrica (F15); ninguno está en la minuta ni en el borrador y los cuatro salen como «FALTA … no aparece en el destino». (B) `DOMICILIO_NO_ENCONTRADO` falso: el borrador escribe mal el nombre en la comparecencia, la regla toma otra línea donde el nombre sí está bien (sin dirección) y avisa, aunque la cláusula correcta contiene el DNI de la ficha y la dirección equivalente (AVENIDA = AV.).

## Principio

**El borrador está obligado a contener solo lo que la ficha oficial o la minuta dicen.** Lo demás sirve para reconocer, no para exigir.

## Clarifications

### Session 2026-09-27

- Q: ¿Qué nombres DEBE contener el borrador? → A: Solo (1) los nombres de las personas con ficha (anclas) y (2) los nombres de la minuta. Menciones sin ficha y adjuntos siguen sirviendo para **reconocer** nombres del borrador (que no salgan como «no coincide con ninguna fuente»), nunca para exigirlos. DNI, partidas y montos no cambian. Decidido por el propietario el 2026-09-27.
- Q: ¿Dónde se busca el domicilio de una persona con ficha? → A: En **todas** las cláusulas del borrador que contienen el DNI de la persona o su nombre exacto; se avisa solo si no aparece en ninguna. Se conservan las equivalencias de vía de F12. Decidido por el propietario el 2026-09-27.

## Requirements *(mandatory)*

- **FR-001**: La observación `[NOMBRE] FALTA` DEBE emitirse solo para nombres exigibles: nombre de cada ancla (`Catalogo.personas`) y nombres de los documentos con rol minuta.
- **FR-002**: Nombres de menciones sin ficha, adjuntos (incluida la variante F15) y cónyuges NO DEBEN generar `FALTA`, pero DEBEN seguir en la proyección `cat["NOMBRE"]` para reconocer nombres del borrador y sugerir «debe decir».
- **FR-003**: `FALTA` de `DNI`, `PARTIDA` y `MONTO` sin cambios.
- **FR-004**: `DOMICILIO_NO_ENCONTRADO` DEBE buscar el domicilio en toda cláusula (línea) del borrador que contenga el DNI exacto de la persona o su nombre exacto, y emitirse solo si no está en ninguna.
- **FR-005**: El núcleo no conoce roles: `services.py` calcula los nombres exigibles y los pasa a `revisar()` como parámetro opcional. Sin ese parámetro, `revisar()` se comporta como antes (usado por `app.py` y `app_ortografia.py`).
- **FR-006**: Núcleo puro y determinista; sin dependencias, migraciones ni cambios del sondeo JSON. Solo datos ficticios en tests (DNI `9000xxxx`, nombres inventados).

## Success Criteria *(mandatory)*

- **SC-001**: En el expediente medido por el revisor, 0 `FALTA` de nombres que no estén en una ficha ni en la minuta (hoy 4).
- **SC-002**: En el mismo expediente, 0 `DOMICILIO_NO_ENCONTRADO` cuando la cláusula del DNI contiene el domicilio equivalente (hoy 1).
- **SC-003**: `revisar()` sin nombres exigibles, `correspondencia()`, `diagnostico()` y `revisar_parrafos()` dan la misma salida literal sobre los fixtures ficticios.

## Assumptions

- «Nombres de la minuta» = proyección `NOMBRE` del catálogo de cada documento con rol minuta, con la misma extracción de siempre.
- «Cláusula» = línea del borrador, como en F12. El DNI se reconoce como número completo (no dentro de otro número).
- Si el nombre exacto no aparece en ninguna parte del borrador, las reglas F12 de la persona siguen sin evaluarse (sin cambio).
- `correspondencia()` y `diagnostico()` siguen contando todos los nombres; no forman parte de esta decisión.

## Ampliación · 2026-10-05

Una auditoría visual de los 10 expedientes de prueba encontró 14 falsos positivos de nombre y DNI. El usuario confirmó que los nombres salen del OCR de RENIEC y que ese OCR nunca trae «SEÑORA».

- **FR-A1 (tratamientos)**: el nombre leído del borrador o de una fuente pierde, en sus bordes, el tratamiento, el rótulo y la forma de intervenir:
  - tratamientos: «SEÑOR», «SEÑORA», «SEÑORITA», «DON», «DOÑA», «SR.», «SRA.»;
  - rótulo de cuadro: «NOMBRE»;
  - forma de intervenir: «POR», «PROCEDE POR DERECHO PROPIO», «REPRESENTADO/A», «DEBIDAMENTE».

  Vale también para los nombres sueltos de la carátula y de los cuadros.
- **FR-A2 (nombres cortados)**: un nombre que es un tramo del nombre de una ficha es una lectura cortada (salto de línea, sello, OCR). Por eso no se exige ni genera una segunda observación, aunque sigue reservando su tramo en el borrador. El nombre de una ficha nunca se descarta. Sin fichas (catálogo antiguo), el completo es el nombre más largo que lo contiene.
- **FR-A3 (DNI exigible)**: como en los nombres, las menciones reconocen y no exigen. El FALTA de DNI se limita a los documentos de las fichas RENIEC o biométricas y a los DNI escritos en la minuta. El DNI de una declaración jurada, una vigencia o un certificado SUNARP se sigue usando para validar un DNI del borrador, pero no se exige: suele ser de un cónyuge, un socio u otro apoderado que no comparece, o una lectura OCR con un dígito distinto. Sin minuta, el comportamiento anterior se conserva.
- **Medición** (10 expedientes, confrontación en memoria):
  - desaparecen 14 falsos positivos: 7 DNI de menciones, 4 nombres con prefijo o rótulo y 3 nombres cortados o duplicados;
  - no hay hallazgos nuevos;
  - el expediente con errores sembrados sigue con 8 de 8.
- **Pendiente**: el cónyuge de la declaración jurada conserva el rótulo «O CONVIVIENTE:». Limpiarlo deja a la vista nombres de cónyuge con OCR dañado que hoy generarían sugerencias falsas; requiere su propio tratamiento.
