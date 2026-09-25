# Specification Quality Checklist: F13 · Anclaje por ficha oficial

**Feature**: [spec.md](../spec.md). `[X]` refleja evidencia documental o una
prueba ejecutada; en esta etapa solo hay plan, así que casi todo sigue abierto.

## Anclas y pegado

- [X] CHK001 ¿Está definido qué es un ancla y qué pasa con una ficha que el OCR no leyó completa? [FR-001; research D1]
- [ ] CHK002 ¿Solo RENIEC y BIOMETRICA crean personas y la prosa sola da cero personas? [FR-001; T009]
- [ ] CHK003 ¿Un registro con documento se pega solo por documento exacto y único, y nunca por nombre? [FR-002; T010, T011]
- [ ] CHK004 ¿Un registro con solo nombre se pega solo por clave exacta y única? [FR-003; T011]
- [ ] CHK005 ¿Una discrepancia ancla/adjunto no marca revisión y manda el ancla? [FR-004; T010]
- [ ] CHK006 ¿La revisión manual solo aparece entre anclas y conserva la emisión más reciente de F12? [FR-004/FR-005; T012]
- [ ] CHK007 ¿Las menciones nunca llevan `REVISION_MANUAL`? [SC-004; T009]

## Cónyuge

- [ ] CHK008 ¿El cónyuge queda como atributo del ancla del declarante, con procedencia, y no como persona? [FR-006; T015]
- [ ] CHK009 ¿Los casos sin declarante identificado y con cónyuges distintos tienen respuesta del propietario? [research NEEDS CLARIFICATION; T005]

## Compatibilidad

- [ ] CHK010 ¿La salida literal de `revisar`, `correspondencia`, `diagnostico` y `revisar_parrafos` es idéntica sobre los fixtures ficticios? [FR-008/SC-005; T006]
- [ ] CHK011 ¿`cat["NOMBRE"]` y `cat["DNI"]` incluyen adjuntos, menciones y cónyuges? [FR-008; T008, T010, T015]
- [ ] CHK012 ¿`Persona` y `Catalogo` aceptan las llamadas F11/F12 existentes? [T007]
- [X] CHK013 ¿Está documentada la pérdida de `DOCUMENTO_CRUZADO` entre comparecientes sin ficha? [Clarifications; research §Consecuencias]
- [ ] CHK014 ¿`DOCUMENTO_SIN_TITULAR` no salta para documentos presentes en fuentes sin ficha? [research D8; T018]

## Privacidad y entrega

- [ ] CHK015 ¿Sondeo, logs y errores sin adjuntos, menciones ni cónyuge? [spec Seguridad; T021]
- [ ] CHK016 ¿Solo datos ficticios y sin migración, IA, red ni dependencias? [FR-009; SC-006; T023]
- [ ] CHK017 ¿La medición antes/después alcanza ≥ 49 / 0 / 0 / ≤ 6 y el expediente de referencia sigue 8 de 8 sin falsos positivos? [SC-001..SC-004; T024]
