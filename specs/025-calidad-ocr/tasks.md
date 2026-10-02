# Tareas · F31

- [x] T001 Especificar alcance, supuestos y seguridad en `spec.md` y `plan.md` (FR-001 a FR-008).
- [x] T002 [US1] Capturar baseline en `scripts/medir_ocr_sintetico.py` y `docs/ocr-baseline.json` (FR-003, FR-007).
- [x] T003 [US1] Reproducir inclinación, marca aislada, capa corrupta y caché en `tests/test_calidad_ocr.py` (FR-001/002/006).
- [x] T004 [US1] Implementar adaptación y reintentos medidos en `adaptadores/calidad_ocr.py` y `adaptadores/extraccion.py` (FR-001/002/003/004/006).
- [x] T005 [US2] Persistir calidad y avisos con pruebas en `tests/test_calidad_lectura.py`, modelos, migración y servicios (FR-004/005).
- [x] T006 [US2] Mostrar avisos y comprobar interfaz y reporte en `templates/expedientes/confrontacion.html` (FR-005).
- [x] T007 [US3] Crear referencia privada pendiente y guía de revisión en `docs/ocr-mejoras-2026-10-02.md` (FR-007/008).
- [x] T008 Medir candidato, ejecutar regresión y documentar resultados en `docs/ocr-mejoras-2026-10-02.md` (SC-001 a SC-004).

Verificación local: 590 pruebas Python y 5 Node aprobadas; Ruff, migraciones y Django correctos. Integración por PR, CI Python 3.13 y Quality Gate de SonarQube pendientes. La revisión notarial de etiquetas reales sigue siendo un paso humano separado de estas tareas técnicas.

Dependencias: T001 → T002/T003 → T004 → T005 → T006 → T008. T007 puede avanzar junto con T004. Implementación incremental: primero lectura, después persistencia y aviso. La medición sintética puede ejecutarse en un agente separado con una copia del extractor previo; no modifica archivos productivos compartidos.
