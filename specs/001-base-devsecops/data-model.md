# Data Model · F1 Base DevSecOps

Modelo conceptual de evidencia de desarrollo. No crea tablas, modelos Django ni persistencia nueva en el ERP.

| Entidad | Campos mínimos | Validación / relaciones |
|---|---|---|
| Revisión | SHA, evento, rama, PR opcional | Identifica exactamente el código probado; no reutilizar éxito de otra revisión. |
| Ejecución | ID, intento, revisión, estado | En PR 1 tiene cuatro controles; desde PR 2 tiene cinco controles y agregado de [contrato CI](contracts/ci.md). |
| Resultado de control | nombre estable, estado, enlace a ejecución | Solo `success` habilita agregado. Pendiente, fallo, cancelado, omitido, neutral o ausente bloquean. |
| Cobertura | revisión, rutas relativas, líneas válidas/cubiertas | XML parseable, al menos una línea productiva; corresponde al mismo intento. No guarda fragmentos de documentos. |
| Hallazgo | herramienta, regla/ID, ubicación saneada, resolución | Corregido o excepción individual escrita con motivo y enlace al PR; no desactiva el control ni reduce gate. |
| Expediente sintético | versión del script, archivos neutros, resultados esperados | Solo ficticio y regenerable; no deriva de expedientes reales. |
| Medición local | ejecución explícita, resultado agregado | Referencia archivos externos; nunca contenido real, nombres de cliente o rutas sensibles en informes. No sustituye a los tests CI. |

Transiciones de ejecución: pendiente → en curso → éxito / fallo / cancelado. Un reintento es una nueva evaluación ligada al mismo SHA e intento identificable. Un SHA nuevo invalida resultados anteriores para merge.

Transición de integración: bloqueado hasta que todos los controles del SHA actual sean exitosos y la rama esté actualizada. Con un mantenedor, no hay aprobación humana requerida por la protección; esto no elimina la justificación escrita de excepciones.

Ciclo de fixtures: generar → ejecutar casos → regenerar o eliminar salidas temporales. Los datos reales nunca entran en este ciclo. Los expedientes externos no se versionan ni se cargan en CI.

Excepción única de arranque: PR 1 admite integración con sus cuatro controles aprobados, sin sonar/ci-required. La enmienda de PR 2 formaliza esta decisión del usuario. Code smells existentes se registran como deuda F3; los demás hallazgos existentes requieren corrección o justificación escrita.
