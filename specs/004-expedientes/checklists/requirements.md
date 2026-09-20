# Specification Quality Checklist: F4 · Expedientes

**Purpose**: revisar la calidad, completitud y trazabilidad de los requisitos
antes de implementar; no valida que el código exista.
**Created**: 2026-09-20
**Feature**: [spec.md](../spec.md)
**Review Ownership**: revisión completada el 2026-09-20 contra `spec.md`,
`data-model.md`, `research.md`, pruebas sintéticas y el contrato de UI. `[x]`
significa que el requisito está definido y es verificable; no declara el
Quality Gate remoto.

## Completitud y trazabilidad

- [X] CHK001 ¿Cada historia de usuario tiene un criterio independiente y escenarios que cubren su resultado observable? [Completitud, Spec §User Scenarios & Testing]
- [X] CHK002 ¿FR-001 a FR-015 están vinculados a escenarios o criterios de éxito que permitan una evaluación objetiva? [Trazabilidad, Spec §Requirements/Success Criteria]
- [X] CHK003 ¿Está definido qué documentos mínimos necesita un expediente antes de considerarse listo para F5, o se declara explícitamente que F4 no impone ese mínimo? [Gap, Spec §Assumptions]
- [X] CHK004 ¿El límite de F4 frente a F5, F6 y F9 está expresado sin dejar funciones implícitas? [Consistencia, Spec §Assumptions]
- [X] CHK005 ¿La retención indefinida, la supresión por comando y la persistencia mínima describen el mismo conjunto de datos? [Consistencia, Spec §Clarifications/Requirements]

## Claridad y medibilidad

- [X] CHK006 ¿El máximo por defecto de 25 MB tiene unidad, fuente de configuración y comportamiento cuando falta? [Claridad, Spec §FR-011]
- [X] CHK007 ¿“Versión del extractor” define qué cambio exacto invalida la caché y cómo se comunica la identidad sin duplicar fuentes? [Claridad, Spec §FR-006]
- [X] CHK008 ¿“Contenido real” define criterios verificables para cada formato admitido, separados de la validación por extensión? [Claridad, Spec §FR-011]
- [X] CHK009 ¿“Motivo entendible” está acotado a categorías o mensajes que no filtren rutas, trazas, nombres ni contenido? [Medibilidad, Spec §US2/FR-008]
- [X] CHK010 ¿El umbral configurable de 15 minutos para recuperar `PROCESANDO` es distinguible de una extracción lenta? [Medibilidad, data-model §Transiciones]
- [X] CHK011 ¿“Sin intervención del usuario” define el intervalo máximo de actualización y el comportamiento ante fallo de consulta? [Medibilidad, Spec §FR-007]

## Consistencia de estados y concurrencia

- [X] CHK012 ¿Las transiciones de `Documento` son consistentes y el resumen de `Expediente` se deriva sin estado almacenado? [Consistencia, data-model §Transiciones]
- [X] CHK013 ¿La regla de duplicado dentro del expediente especifica si cambia según rol y qué ocurre ante dos peticiones simultáneas? [Claridad, data-model §Documento]
- [X] CHK014 ¿El comportamiento de dos subidas simultáneas del mismo hash queda definido tanto para la caché como para la restricción documental? [Cobertura, Spec §Edge Cases]
- [X] CHK015 ¿La supresión de un `TextoExtraido` compartido lo vacía para todos e informa el conteo sin borrar documentos? [Consistencia, Spec §US5/FR-015]
- [X] CHK016 ¿Se especifica qué sucede con el texto, `ultimo_uso_el`, hashes y documentos cuando una supresión ya fue solicitada? [Claridad, Spec §FR-009/FR-015]

## Privacidad y seguridad

- [X] CHK017 ¿Los requisitos distinguen con precisión nombre original visible, nombre no confiable y datos que nunca deben aparecer en logs o mensajes? [Seguridad, Spec §Requisitos de seguridad y privacidad]
- [X] CHK018 ¿La ubicación temporal, la ausencia de servicio estático y la eliminación en `finally` son requisitos independientes y verificables? [Completitud, Spec §FR-004/FR-012]
- [X] CHK019 ¿Cada ruta y endpoint tiene una regla explícita para Usuario, Administrador, creador y expediente ajeno? [Cobertura, Spec §Requisitos de seguridad]
- [X] CHK020 ¿La validación server-side define el resultado para archivos vacíos, corruptos, ilegibles y con extensión engañosa? [Edge Case, Spec §Edge Cases]
- [X] CHK021 ¿La tarea de huérfanos define cómo identifica un temporal huérfano sin borrar un archivo que un worker sigue usando? [Claridad, Spec §FR-010/Edge Cases]

## Dependencias, límites y ambigüedades

- [X] CHK022 ¿La ejecución programada del comando define responsable y frecuencia sin convertirlo en una dependencia de infraestructura nueva? [Gap, Spec §Clarifications]
- [X] CHK023 ¿La confirmación de eliminación corresponde a la acción FR-013 y distingue cancelación de borrado? [Trazabilidad, Spec §US4/FR-013]
- [X] CHK024 ¿Está explícito que F4 no tiene cierre ni estado propio de `Expediente`, y que su resumen se deriva de documentos? [Consistencia, data-model §Expediente]
- [X] CHK025 ¿Los criterios de éxito pueden comprobarse con fixtures sintéticos y evidencia agregada sin usar expedientes reales? [Privacidad, Spec §SC-002–SC-004]
- [X] CHK026 ¿Se declara qué validaciones son obligatorias antes de persistir y cuáles pueden fallar durante la extracción? [Claridad, Spec §FR-004/FR-011]
- [X] CHK027 ¿FR-013 conserva siempre `TextoExtraido` al eliminar un documento? [Privacidad, Spec §FR-013/data-model §Persistencia]
- [X] CHK028 ¿FR-014 y FR-015 tienen pruebas observables para el retorno a `PENDIENTE` y el conteo de expedientes afectados? [Medibilidad, Spec §FR-014/FR-015]
