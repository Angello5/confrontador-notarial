# Checklist Nielsen y accesibilidad: F12 · Persona ampliada

**Feature**: [contracts/ui.md](../contracts/ui.md) y [spec.md](../spec.md).
`[X]` exige contrato claro o prueba ejecutada; la revisión visual y las reglas
siguientes no se adelantan.

## Tabla de extracción: ronda actual

- [X] CHK001 ¿Cada persona tiene una fila con cuatro valores y cuatro procedencias independientes? [FR-008; tests de servicio/HTML]
- [X] CHK002 ¿Una lectura ausente dice «No detectado/a» y «No ubicada» sin inventar valor? [contracts §Tabla; plantilla]
- [X] CHK003 ¿La tabla usa nombres comprensibles, encabezados de columna y contenedor adaptable? [contracts §Tabla; plantilla]
- [X] CHK004 ¿La procedencia muestra solo nombre de archivo y página, con escape de HTML? [contracts §Tabla; servicio/plantilla]
- [X] CHK005 ¿Solo se muestra tras autorización y el sondeo no contiene campos F12? [contracts §Privacidad; vista existente]
- [X] CHK006 ¿Se conserva `<details>`, teclado, foco, retorno, POST y CSRF? [contracts §Tabla/Privacidad; vista existente]
- [ ] CHK007 ¿Se revisó visualmente la tabla ampliada en pantalla estrecha y con teclado? [pendiente de revisión visual]

## Observaciones: siguiente ronda

- [X] CHK008 ¿US1 especifica borrador y cláusula de la persona? [spec §Clarifications]
- [X] CHK009 ¿US2 exige edad cumplida y fecha de hoy visible? [spec US2]
- [X] CHK010 ¿US3 define variantes equivalentes y evita observarlas? [spec US3]
- [ ] CHK011 ¿Los mensajes nuevos muestran persona, fuente, hallazgo, archivo/página y ubicación segura? [siguiente ronda]
- [ ] CHK012 ¿El conflicto entre consultas RENIEC tiene aviso textual y revisión manual? [siguiente ronda]
- [ ] CHK013 ¿Los recuentos y el estado sin observaciones siguen siendo coherentes tras añadir las reglas? [siguiente ronda]

## Evidencia

Pruebas focalizadas de tabla y núcleo, más suite completa local (294 aprobadas,
13 excluidas). Revisión visual, reglas nuevas, medición privada y Quality Gate
remoto pendientes.
