# Specification Quality Checklist: F5 · Confrontación

**Propósito**: verificar que el diseño sea trazable a `spec.md` y no declarar
implementación terminada. `[X]` significa que la definición está documentada;
las pruebas y el código quedan pendientes para la etapa de implementación.

**Feature**: [spec.md](../spec.md)

## Completitud y trazabilidad

- [X] CHK001 Cada una de las cuatro historias tiene criterio independiente y sus escenarios tienen una salida observable. [Spec §User Scenarios & Testing]
- [X] CHK002 FR-001 a FR-012 tienen correspondencia con una tarea, una prueba o un contrato UI. [Spec §Requirements, tasks.md]
- [X] CHK003 Se conserva el límite de F5: regla y ortografía sí; léxico, historial e informe exportable no. [Spec §FR-012, roadmap]
- [X] CHK004 Se declara que no hay entidades nuevas, migraciones ni persistencia de observaciones. [Spec §Key Entities/FR-011, plan]
- [X] CHK005 Se cubren varios borradores con resultado independiente. [Spec §Edge Cases, contracts §Disponibilidad]
- [X] CHK006 Se cubren fuentes imagen y documento, incluyendo la regla de minutas por extensión. [Spec §FR-003/FR-009, research]

## Claridad funcional y técnica

- [X] CHK007 El umbral 88 está fijado, no es entrada del usuario y no aparece como opción en la pantalla. [Spec §FR-008, research]
- [X] CHK008 La clave del diccionario de fuentes es el nombre original y no una ruta ni un identificador técnico. [Spec §FR-009, research]
- [X] CHK009 El diagnóstico se ejecuta antes de campos, párrafos y ortografía; el aviso bloquea la lista campo por campo. [Spec §FR-005, contracts §Estados]
- [X] CHK010 Los estados pendiente/procesando/error y texto suprimido tienen mensaje y acción siguiente definidos. [Spec §FR-010, contracts §Disponibilidad]
- [X] CHK011 El formato actual de la salida de regla está descrito y tiene adaptación determinista a campo, hallado, esperado y ubicación. [research, contracts §Agrupación]
- [X] CHK012 La salida de ortografía conserva palabra, motivo y sugerencia, y recibe nombres propios validados como palabras aceptadas. [Spec §FR-004, research]
- [X] CHK013 La ubicación se calcula en aplicación sobre el texto del borrador, no en el núcleo. [Spec §FR-007, plan]
- [X] CHK014 Las observaciones repetidas por valor se deduplican según el comportamiento aprobado. [Spec §Edge Cases, contracts §Agrupación]

## Seguridad, privacidad y límites

- [X] CHK015 La acción exige autenticación, grupo y creador/Administrador; se repite la autorización en servidor aunque el botón esté oculto. [Spec §Seguridad, contracts §Ruta]
- [X] CHK016 No se importan `experimental/`, modelos de lenguaje ni servicios externos. [Spec §FR-012, plan]
- [X] CHK017 El resultado no se escribe en base de datos, logs, temporales ni respaldos. [Spec §FR-011/Seguridad, plan]
- [X] CHK018 Los mensajes seguros excluyen datos personales, texto completo, rutas, hashes y trazas. [Spec §Seguridad, contracts §Mensajes]
- [X] CHK019 Se usan únicamente expedientes y textos ya guardados; F5 no reabre originales ni ejecuta OCR. [Spec §Seguridad, research]
- [X] CHK020 Se mantiene la dependencia y el comportamiento de `nucleo/`; no se autoriza una corrección implícita del núcleo. [Spec §Assumptions, research]

## Clarificaciones y contradicciones pendientes

- [NEEDS CLARIFICATION] CHK021 La sección `Input` de `spec.md` todavía enumera léxico, aunque la aclaración y FR-012 lo excluyen; debe corregirse por el propietario antes de cerrar la documentación de la fase. [Spec §Input/Clarifications]
- [NEEDS CLARIFICATION] CHK022 Si la notaría exige una ubicación concreta para un párrafo alterado sin coincidencia literal, debe definirla: el núcleo actual solo devuelve porcentaje y prefijo de fuente; el contrato usa «No ubicada». [Spec §US2/FR-007, research]
