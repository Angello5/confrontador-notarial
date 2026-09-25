# Checklist Nielsen y accesibilidad: F12 · Persona ampliada

**Propósito**: revisar la claridad, procedencia y privacidad de los cuatro
campos y las observaciones nuevas. `[X]` requiere evidencia de revisión;
todos los ítems quedan pendientes en esta etapa.

**Feature**: [contracts/ui.md](../contracts/ui.md) y [spec.md](../spec.md)

## Visibilidad y lenguaje

- [ ] CHK001 ¿Se definen mensajes diferenciados para resultado, falta de lectura, conflicto RENIEC/biométrica y revisión manual? [Completeness, Spec US4; Constitución VIII.1]
- [ ] CHK002 ¿La tabla de extracción especifica una fila por persona y procedencia distinta para cada valor nuevo? [Clarity, Spec FR-008; Constitución VIII.6]
- [ ] CHK003 ¿«No detectado» evita presentar un campo ausente como dato aprobado o igual a la fuente? [Clarity, Spec US4; Constitución VIII.9]
- [ ] CHK004 ¿Los textos visibles usan persona, estado civil, fecha de nacimiento, domicilio, distrito, fuente y página, sin términos internos? [Coverage, Constitución VIII.2]
- [ ] CHK005 ¿Se define un aviso específico de conflicto civil que no se esconda detrás del estado genérico de identidad? [Gap, Spec Edge Cases; Constitución VIII.1/9]

## Observaciones y control

- [ ] CHK006 ¿Cada observación civil especifica persona, hallazgo, valor de fuente, archivo y página y texto comparado aprobado? [Completeness, Spec Requisitos UX; US1]
- [ ] CHK007 ¿La observación de minoría de edad incluye edad cumplida, fecha de nacimiento y fecha de referencia aprobada? [Clarity, Spec Requisitos UX; US2]
- [ ] CHK008 ¿La observación de domicilio distingue ausencia real de variante equivalente y permite verificar la fuente? [Measurability, Spec US3]
- [ ] CHK009 ¿Se especifica cómo se muestra ubicación «No ubicada» sin inventar una línea del borrador? [Coverage, contracts §Observaciones]
- [ ] CHK010 ¿El contrato conserva retorno al expediente, POST/CSRF y disponibilidad de confrontación F11 sin nueva acción técnica? [Consistency, contracts §Privacidad y estados]
- [ ] CHK011 ¿El estado sin observaciones evita afirmar aprobación total si existe conflicto de fuentes para revisión manual? [Coverage, Spec Edge Cases]

## Accesibilidad y privacidad visible

- [ ] CHK012 ¿La tabla define encabezados, lectura ordenada de valor/procedencia y contenedor adaptable para cuatro campos adicionales? [Coverage, Constitución VIII accesibilidad; contracts §Datos]
- [ ] CHK013 ¿Los avisos especifican texto y `role="alert"`/`role="status"`, sin depender solo de color? [Coverage, Constitución VIII.1/8]
- [ ] CHK014 ¿Se preservan teclado, foco visible y semántica de `<details>` para la tabla ampliada? [Consistency, Constitución VIII accesibilidad]
- [ ] CHK015 ¿Solo la respuesta HTML tras autorización puede mostrar valores, mientras sondeo JSON, logs y errores quedan sin ellos? [Completeness, Spec Seguridad; contracts §Privacidad]
- [ ] CHK016 ¿Se exige escapar nombres de archivo y evitar rutas, hashes, OCR crudo y texto completo en la pantalla? [Coverage, Constitución IV; contracts §Datos]
- [ ] CHK017 ¿La UI se mantiene en las secciones F11 de Personas, Regla y Ortografía, con los recuentos coherentes tras añadir reglas? [Consistency, Spec FR-009; contracts §Observaciones]

## Evidencia

Pendiente de implementación y revisión visual. No se declaran pruebas UI,
capturas, accesibilidad verificada ni Quality Gate remoto.
