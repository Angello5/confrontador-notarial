# Specification Quality Checklist: F12 · Persona ampliada

**Propósito**: revisar el contrato aprobado, sus fuentes documentales y la
compatibilidad F11/F5 antes de implementar. `[X]` requiere evidencia concreta;
en esta etapa todos los ítems quedan pendientes.

**Feature**: [spec.md](../spec.md)

## Completitud y claridad

- [ ] CHK001 ¿Quedan explícitos los ocho campos opcionales (cuatro valores y cuatro procedencias) y la compatibilidad de los cuatro argumentos posicionales previos? [Clarity, Spec FR-001]
- [ ] CHK002 ¿Se define que la procedencia de cada valor seleccionado indica archivo y página, incluso después de unificar apariciones? [Completeness, Spec FR-001/FR-008]
- [ ] CHK003 ¿Se especifican los rótulos exactos y fronteras de columna/sección para domicilio y distrito RENIEC y estado civil biométrico? [Gap, Spec FR-002; research §Evidencia]
- [ ] CHK004 ¿Se limita cada captura a RENIEC o BIOMETRICA inequívoca y a la persona del mismo bloque, sin usar pie, operador ni otra página? [Coverage, Spec FR-002]
- [ ] CHK005 ¿Se definen las cuatro categorías civiles sin género y la conducta ante valor fuera de catálogo? [Clarity, Spec FR-003]
- [ ] CHK006 ¿Se define qué fechas `dd/mm/aaaa` y `dd-mm-aaaa` son inequívocas y que una letra OCR no se corrige por suposición? [Clarity, Spec FR-004; Edge Cases]
- [ ] CHK007 ¿Se documenta que domicilio conserva la dirección literal y distrito pertenece al domicilio, no al nacimiento? [Consistency, docs/catalogo-datos.md]
- [ ] CHK008 ¿Queda definida la precedencia RENIEC sobre biométrica en conflicto civil, junto con una señal visible de revisión manual? [Coverage, Spec Edge Cases]
- [ ] CHK009 ¿Se especifica cómo se empareja una persona del borrador con una persona de fuente antes de afirmar una discrepancia? [Gap, Spec FR-005/FR-007]
- [ ] CHK010 ¿Se define qué significa «sin cónyuge» para una persona concreta y si se compara minuta, borrador o ambos? [Conflict, Spec US1/FR-005; research §Evidencia]
- [ ] CHK011 ¿Queda resuelta por el propietario la fecha de referencia y puede medirse la edad cumplida sin consultar el reloj dentro del núcleo? [Ambiguity, Spec US2]
- [ ] CHK012 ¿Queda aprobada la lista cerrada de abreviaturas de domicilio equivalentes y la política para variantes no listadas? [Ambiguity, Spec US3]
- [ ] CHK013 ¿Se especifica qué hacer cuando falta documento o cuando fecha/estado/domicilio son ilegibles, sin inventar un valor? [Coverage, Spec US1–US3; Edge Cases]

## Consistencia y aceptación

- [ ] CHK014 ¿Se corrige la atribución de fecha y domicilio a biométrica del Input para concordar con la tabla de `docs/catalogo-datos.md`? [Conflict, Spec Input]
- [ ] CHK015 ¿Se explica por qué los dos catálogos cuentan 28/27 y 30/32 páginas de RENIEC/biométrica? [Assumption, docs/catalogo-datos.md; docs/catalogo-fuentes.md]
- [ ] CHK016 ¿SC-001 identifica rótulos y procedencias suficientes para medir los cuatro campos en una ficha ficticia sin usar heurísticas no aprobadas? [Measurability, Spec SC-001]
- [ ] CHK017 ¿SC-002–SC-004 cubren positivos, negativos y ausencias de lectura de cada regla con observaciones estructuradas verificables? [Acceptance Criteria, Spec SC-002–SC-004]
- [ ] CHK018 ¿FR-009/SC-005 exigen comparar contenido y orden de todas las observaciones previas con la misma entrada ficticia? [Measurability, Spec FR-009/SC-005]
- [ ] CHK019 ¿Se mantiene `revisar()` textual y `comparar_personas()` de dos argumentos compatible mientras las reglas nuevas viven en la capa de regla? [Consistency, Spec FR-005–FR-009; plan §Contract]
- [ ] CHK020 ¿Se conserva la ausencia de migración/entidad y la separación entre validación local, Quality Gate remoto y medición privada? [Coverage, Spec FR-010; Constitución VII]

## Seguridad y privacidad

- [ ] CHK021 ¿La spec limita los valores nuevos a HTML autorizado y prohíbe su inclusión en sondeo JSON, logs, errores y trazas? [Completeness, Spec Seguridad]
- [ ] CHK022 ¿Se requieren datos solo ficticios en pruebas, fixtures, documentación y commits, sin ejemplos reales ni archivos de expedientes? [Coverage, Spec SC-006]
- [ ] CHK023 ¿El plan conserva núcleo puro, determinismo, ausencia de IA/red y cero dependencias nuevas? [Consistency, Constitución I/II/V]
- [ ] CHK024 ¿Las preguntas pendientes están visibles como bloqueos de implementación y no como decisiones tomadas por el agente? [Ambiguity, research §Preguntas pendientes]

## Evidencia

Planificación documental solamente. No se declara test, lint, cobertura,
Quality Gate, medición privada ni interfaz verificada.
