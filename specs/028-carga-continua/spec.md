# F34 · Carga continua y revisión centrada en el documento

**Created**: 2026-10-03
**Status**: Especificación aprobada mediante «Okey procede a implementar todo» sobre la propuesta del diagnóstico.
**Input**: Adjuntar sin interrupciones, adelantar lectura, concentrar espera en Confrontar, reutilizar trabajo y simplificar resultados.

## User Scenarios & Testing

### US1 · Adjuntar sin esperar a la lectura (P1)
El usuario sigue incorporando minuta, borrador y recaudos mientras se reciben y leen otros archivos.
Prueba independiente: adjuntar archivos de tres roles consecutivamente, con una lectura lenta simulada; ninguna selección recarga la página ni espera al OCR.
Aceptación: cada archivo aparece una sola vez con estado real; errores individuales no descartan los otros; se puede cancelar una transferencia y reintentar.

### US2 · Confrontar una sola vez y volver después (P1)
El usuario pulsa Confrontar con lectura pendiente; la solicitud se conserva, muestra su etapa y permite salir y volver. Si existe resultado vigente, se abre sin recalcular.
Prueba: doble solicitud, ejecución repetida y reapertura producen una sola corrida vigente. Un expediente listo avanza aunque otro tenga documentos pendientes.
Aceptación: cancelar impide publicar una nueva corrida de esa solicitud; cambios documentales durante el cálculo impiden publicar resultados con entradas incorrectas; errores admiten reintento explícito.

### US3 · Revisar el original y corregir propuestas (P1)
La página original y la observación seleccionada dominan la vista; la información de apoyo se expande bajo demanda. Se puede incluir o excluir una corrección desde la marca y generar un DOCX distinto.
Prueba: seleccionar marca, revisar fuente y alcance, confirmar propuestas y descargar copia; el hash del original no cambia.
Aceptación: se conserva la lista cuando el visor no está disponible; se explica si una propuesta afecta varias apariciones; no se confunde lectura dudosa con discrepancia.

### US4 · Medir y procesar sin trabajo duplicado (P2)
La operación distingue recepción, espera en cola, lectura, análisis y preparación visual. Dos consumidores no procesan simultáneamente una misma entrada ni recuperan trabajo que sigue vivo.
Prueba: consumidores concurrentes, entrada repetida y proceso abandonado; resultados iguales, una extracción para la misma identidad y recuperación del abandonado.

### Edge Cases
Sesión vencida, red interrumpida tras recepción, archivo inválido o repetido, borrador eliminado, expediente archivado, cambios durante confrontación, fallo del OCR, fallo de conversión, lectura histórica sin medición, solicitud cancelada y reintentada, navegador sin JavaScript y cierre de página.

## Requirements

- FR-001: Carga continua sin navegación ni dependencia del OCR; validación de formato y tamaño, respuesta individual y alternativa sin JavaScript.
- FR-002: Confrontar espera las transferencias seleccionadas; un fallo de transferencia impide iniciar silenciosamente una comparación incompleta.
- FR-003: Confrontar reutiliza resultado vigente y es idempotente; las solicitudes pendientes sobreviven a la navegación. Puede seguir adelantándose una confrontación automática cuando todos los documentos están listos.
- FR-004: Los estados distinguen recepción, lectura, comparación, resultado, error y cancelación. No se presentan porcentajes ni subetapas inventadas.
- FR-005: La cancelación se confirma inmediatamente y el trabajo ya en curso no publica una nueva corrida; las lecturas compartidas útiles pueden terminar en segundo plano.
- FR-006: Cada resultado corresponde a las entradas comprobadas al inicio y al final del cálculo. Si cambian, se descarta el cálculo y se informa de que hay que confrontar el conjunto actualizado.
- FR-007: Confrontaciones y vistas preparadas no esperan a vaciar toda la cola. La vista DOCX se solicita al recibir el borrador y se prepara en segundo plano.
- FR-008: La lectura guardada se reutiliza por archivo y versión; dos consumidores no duplican la extracción simultánea y una tarea viva no vence por tardar mucho.
- FR-009: Una sola lista por rol; acciones secundarias discretas. En resultados, documento principal, observación y fuente lateral, detalles de extracción plegados.
- FR-010: El aviso de calidad identifica páginas y explica qué revisar; no es porcentaje de certeza jurídica ni altera las reglas.
- FR-011: Correcciones desde el visor reutilizan las propuestas actuales, muestran alcance y confirmación; no cambian el original ni permiten introducir valores sin fuente.
- FR-012: Duraciones operativas separadas y sin contenido personal; no presentar las mediciones de desarrollo como rendimiento del servidor de la notaría.

### Seguridad y UX
Mismos permisos de expediente y CSRF. Ninguna ruta, texto documental o secreto en telemetría o errores. Validación en servidor, originales DOCX fuera del repositorio, temporales y supresión existentes. Controles con etiquetas, teclado, foco visible y mensajes accesibles. Sin dependencias nuevas del producto, IA ni servicios externos. Los avisos de error indican recuperación y preservan las selecciones no enviadas.

### Key Entities
Documento recibido, texto reutilizable, estado persistente de solicitud por borrador, corrida inmutable y copia corregida.

## Success Criteria
- SC-001: Tres cargas sucesivas de distintos roles sin recarga de página y sin esperar la lectura.
- SC-002: Dos clics y dos aperturas con entradas idénticas no generan análisis adicionales.
- SC-003: Un expediente listo se confronta antes de procesar el siguiente documento ajeno.
- SC-004: Cancelación o cambios durante cálculo nunca publican una corrida del conjunto obsoleto.
- SC-005: Un caso ficticio permite llegar de marca a propuesta y descargar un corregido sin alterar el original.
- SC-006: Pruebas Python y JavaScript, lint, formatos y controles Django pasan; CI y SonarQube siguen siendo obligatorios para integrar.

## Clarifications · 2026-10-03
La autorización abarca el flujo propuesto y su implementación. Se mantiene la corrección DOCX existente por todas las apariciones compatibles, informando el alcance. La edición libre, corrección exclusiva de una aparición y edición de escaneos se evalúan posteriormente; no se inventan reglas. No se activa la conservación de otros formatos: la constitución indica aprobación pendiente en el PR. La elección y medición en los servidores queda para F8, sin acceso remoto en esta sesión. No se cambian los modelos, resolución ni umbrales OCR.

Diseño del expediente · 2026-10-03: el usuario pidió volver al diseño anterior de la pantalla del expediente (estado en la cabecera, riel de pasos, aviso con recuento, fuentes y borrador en dos columnas, ayuda de formatos en cada zona) conservando la carga continua, la solicitud persistente y la cancelación de F34.

## Assumptions
Máximo diez usuarios. Se conserva la preparación automática existente como optimización; Confrontar expresa la intención y espera lo que falta. Un error se reintenta explícitamente, no en bucle. Se prueban dos consumidores en PostgreSQL de prueba antes de recomendar su activación. Esta copia no tiene Git: implementación local y evidencia, integración pendiente en checkout autorizado.
