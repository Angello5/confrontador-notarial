# Feature Specification: F24 · Montos exigibles

**Feature Branch**: `Angello5/montos-exigibles-P-05-f24-montos-exigibles`

**Created**: 2026-09-28

**Status**: Draft

**Input**: Anexo B P-05 exige cero observaciones sobre datos correctos en el conjunto de prueba controlado. El revisor midió 9 expedientes reales sin errores intencionados: 303 observaciones, de las que 268 son `[MONTO] FALTA: … esta en las fuentes y no aparece en el destino` (un solo expediente aporta 259). Son importes de recaudos (liquidaciones, vigencias, tasas, hojas de cálculo) que el borrador no tiene por qué citar.

## Principio

**El borrador está obligado a contener solo los montos de la minuta.** Los montos de los demás documentos sirven para reconocer, no para exigir (mismo principio que F16 para nombres).

## Clarifications

### Session 2026-09-28

- Q: ¿Qué montos DEBE contener el borrador? → A: Solo los de los documentos con rol minuta. Los montos del resto de fuentes siguen en `cat["MONTO"]` para reconocer montos del borrador (que no salgan como «no coincide con ninguna fuente») y sugerir «debe decir». [NEEDS CLARIFICATION: confirmar con el propietario; opción por defecto implementada, análoga a la aprobada en F16.]
- Q: ¿Y si el expediente no tiene minuta con montos? → A: No se exige ningún monto (conjunto vacío). La detección de un monto del borrador distinto de las fuentes no cambia. [NEEDS CLARIFICATION: confirmar; opción por defecto implementada.]

## Requirements *(mandatory)*

- **FR-001**: La observación `[MONTO] FALTA` DEBE emitirse solo para montos exigibles: los que `RE_MONTO` encuentra en los textos de rol minuta.
- **FR-002**: Montos de los demás documentos NO DEBEN generar `FALTA`, pero DEBEN seguir en `cat["MONTO"]` para reconocer montos del borrador y sugerir «debe decir».
- **FR-003**: `FALTA` de `NOMBRE` (F16), `DNI` y `PARTIDA` y el resto de observaciones sin cambios.
- **FR-004**: El núcleo no conoce roles: `services.py` calcula los montos exigibles con `montos_exigibles(minutas)` y los pasa a `revisar()` como parámetro opcional `montos_exigibles`. Sin él (`None`), `revisar()` se comporta como antes (`app.py`, `app_ortografia.py`).
- **FR-005**: Núcleo puro y determinista; sin dependencias, migraciones ni cambios de plantilla. Solo datos ficticios en tests.

## Success Criteria *(mandatory)*

- **SC-001**: En los 9 expedientes medidos por el revisor, 0 `[MONTO] FALTA` de montos que no estén en la minuta (hoy 268 en total).
- **SC-002**: `revisar()` sin `montos_exigibles` da la misma salida literal sobre los fixtures ficticios (paridad F13/F15).

## Assumptions

- «Montos de la minuta» = `RE_MONTO` sobre el texto normalizado de cada documento con rol minuta, la misma extracción que usa `catalogo()`.
