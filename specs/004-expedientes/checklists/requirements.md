# Specification Quality Checklist: F4 · Expedientes

**Purpose**: revisar la calidad, completitud y trazabilidad de los requisitos
antes de implementar; no valida que el código exista.
**Created**: 2026-09-20
**Feature**: [spec.md](../spec.md)
**Review Ownership**: cada ítem queda sin marcar hasta que un revisor evalúe la
redacción. `[x]` significará calidad de requisitos satisfecha, no implementación
terminada.

## Completitud y trazabilidad

- [ ] CHK001 ¿Cada historia de usuario tiene un criterio independiente y escenarios que cubren su resultado observable? [Completitud, Spec §User Scenarios & Testing]
- [ ] CHK002 ¿FR-001 a FR-012 están vinculados a escenarios o criterios de éxito que permitan una evaluación objetiva? [Trazabilidad, Spec §Requirements/Success Criteria]
- [ ] CHK003 ¿Está definido qué documentos mínimos necesita un expediente antes de considerarse listo para F5, o se declara explícitamente que F4 no impone ese mínimo? [Gap, Spec §Assumptions]
- [ ] CHK004 ¿El límite de F4 frente a F5, F6 y F9 está expresado sin dejar funciones implícitas? [Consistencia, Spec §Assumptions]
- [ ] CHK005 ¿La retención indefinida, la supresión por comando y la persistencia mínima describen el mismo conjunto de datos? [Consistencia, Spec §Clarifications/Requirements]

## Claridad y medibilidad

- [ ] CHK006 ¿“Tamaño máximo configurado” tiene un valor, unidad, fuente de configuración y comportamiento cuando falta? [Ambigüedad, Spec §FR-011]
- [ ] CHK007 ¿“Versión del extractor” define qué cambio exacto invalida la caché y cómo se comunica la identidad sin duplicar fuentes? [Claridad, Spec §FR-006]
- [ ] CHK008 ¿“Contenido real” define criterios verificables para cada formato admitido, separados de la validación por extensión? [Claridad, Spec §FR-011]
- [ ] CHK009 ¿“Motivo entendible” está acotado a categorías o mensajes que no filtren rutas, trazas, nombres ni contenido? [Medibilidad, Spec §US2/FR-008]
- [ ] CHK010 ¿El tiempo de recuperación de un documento `PROCESANDO` está cuantificado y es distinguible de una extracción lenta? [Gap, data-model §Transiciones]
- [ ] CHK011 ¿“Sin intervención del usuario” define el intervalo máximo de actualización y el comportamiento ante fallo de consulta? [Medibilidad, Spec §FR-007]

## Consistencia de estados y concurrencia

- [ ] CHK012 ¿Las transiciones de `Documento` y `Expediente` son consistentes entre spec, modelo y diagramas, incluyendo `CERRADO`? [Consistencia, data-model §Transiciones]
- [ ] CHK013 ¿La regla de duplicado dentro del expediente especifica si cambia según rol y qué ocurre ante dos peticiones simultáneas? [Claridad, data-model §Documento]
- [ ] CHK014 ¿El comportamiento de dos subidas simultáneas del mismo hash queda definido tanto para la caché como para la restricción documental? [Cobertura, Spec §Edge Cases]
- [ ] CHK015 ¿La semántica de supresión de un `TextoExtraido` compartido evita el conflicto entre “borrar” y “no romper el otro expediente”? [Conflicto, Spec §US4/data-model §TextoExtraido]
- [ ] CHK016 ¿Se especifica qué sucede con el texto, `ultimo_uso_el` y los documentos cuando una supresión ya fue solicitada? [Gap, Spec §FR-009]

## Privacidad y seguridad

- [ ] CHK017 ¿Los requisitos distinguen con precisión nombre original visible, nombre no confiable y datos que nunca deben aparecer en logs o mensajes? [Seguridad, Spec §Requisitos de seguridad y privacidad]
- [ ] CHK018 ¿La ubicación temporal, la ausencia de servicio estático y la eliminación en `finally` son requisitos independientes y verificables? [Completitud, Spec §FR-004/FR-012]
- [ ] CHK019 ¿Cada ruta, endpoint y operación de reintento tiene una regla explícita para Usuario, Administrador, creador y expediente ajeno? [Cobertura, Spec §Requisitos de seguridad]
- [ ] CHK020 ¿La validación server-side define el resultado para archivos vacíos, corruptos, ilegibles y con extensión engañosa? [Edge Case, Spec §Edge Cases]
- [ ] CHK021 ¿La tarea de huérfanos define cómo identifica un temporal huérfano sin borrar un archivo que un worker sigue usando? [Claridad, Spec §FR-010/Edge Cases]

## Dependencias, límites y ambigüedades

- [ ] CHK022 ¿La ejecución programada del comando define responsable, frecuencia y reintento sin convertirlo en una dependencia de infraestructura nueva? [Gap, Spec §Clarifications]
- [ ] CHK023 ¿La frase sobre confirmar la eliminación de un documento corresponde a una función definida o está marcada para otra fase? [Conflicto, Spec §Requisitos de usabilidad]
- [ ] CHK024 ¿La existencia de `CERRADO` tiene actor, permiso, transición y mensaje, o queda explícitamente fuera de F4? [Gap, data-model §Expediente]
- [ ] CHK025 ¿Los criterios de éxito pueden comprobarse con fixtures sintéticos y evidencia agregada sin usar expedientes reales? [Privacidad, Spec §SC-002–SC-004]
- [ ] CHK026 ¿Se declara qué validaciones son obligatorias antes de persistir y cuáles pueden fallar durante la extracción? [Claridad, Spec §FR-004/FR-011]
