# F31 · Calidad de lectura y medición de discrepancias

**Created**: 2026-10-02
**Status**: Implementado y verificado localmente; integración por CI/SonarQube pendiente.
**Input**: Mejorar OCR a partir de los 12 casos auditados y distinguir lectura dudosa de discrepancia.

## User Scenarios & Testing

### US1 · Leer escaneos inclinados y capas defectuosas (P1)

El usuario recibe texto utilizable aunque el escaneo tenga una inclinación moderada. Una marca diagonal aislada no debe sustituir al contenido del documento. Una capa de texto con caracteres inválidos activa lectura de imagen aunque supere 50 caracteres. Las páginas con texto normal conservan su ruta rápida.

Prueba independiente: ejemplos ficticios horizontales, inclinados, con marca diagonal y PDF de capa corrupta; comparar campos exactos antes y después.

### US2 · Saber qué lectura revisar (P1)

El usuario ve qué documentos y páginas tienen una lectura dudosa. La ausencia de observaciones no equivale a una lectura fiable. Los resultados guardados conservan el aviso. Los datos históricos sin metadatos no se califican como fiables.

Prueba independiente: resultado con una página de baja confianza, reabrirlo y comprobar el aviso; no cambia el número de discrepancias jurídicas.

### US3 · Medir efectividad sin inventar respuestas (P2)

Se compara una batería ficticia de respuestas conocidas, registrando aciertos de campos y tiempo. Se prepara una referencia privada de los casos reales con estado pendiente de revisión, sin contar esos casos como aciertos o errores confirmados.

## Requirements

- FR-001: conservar la agrupación de texto inclinado cuando hay una dirección dominante respaldada por varias líneas; seguir excluyendo marcas diagonales aisladas.
- FR-002: detectar caracteres de sustitución/control y capas PDF corruptas; intentar OCR conservando texto legible si el reintento no aporta lectura.
- FR-003: limitar reintentos a imágenes de lectura insuficiente, con un máximo de cuatro lecturas. Una caja de baja confianza aislada no activa giros si la confianza global es suficiente; mantiene el aviso. Mantener modelos locales y la resolución inicial; activar transformaciones solo con medición favorable.
- FR-004: conservar por página método, confianza cuando existe, causas de revisión, intentos y posición de las cajas OCR respecto de la imagen analizada. No inventar confianza para extracción nativa o datos históricos.
- FR-005: guardar el resumen de calidad con el texto y la corrida. Mostrar avisos persistentes en resultados y en el reporte impreso, sin convertirlos en discrepancias ni propuestas de sustitución.
- FR-006: invalidar las cachés de archivo y base de datos al cambiar el algoritmo; conservar las interfaces de texto existentes y los manifiestos anteriores.
- FR-007: publicar métricas sintéticas separadas de los resultados reales sin etiquetar; preparar una plantilla local para revisión con fuente, página, campo, sujeto, rol, bien, moneda, concepto, fecha y valor esperado.
- FR-008: no modificar umbrales de correspondencia, cuotas ni criterios jurídicos sin referencia validada. No sustituir dígitos ambiguos por conjeturas.

## Seguridad y privacidad

Procesamiento local, mismos permisos de expediente, sin servicios externos ni nuevas dependencias. Metadatos con texto OCR reciben la misma protección y supresión que el texto extraído. No se conserva la imagen fuente fuera de la retención ya autorizada. Ejemplos, logs e informes compartibles usan datos ficticios o métricas agregadas.

## UX

Aviso en español, separado de las observaciones: identifica documento/página y pide revisar la lectura o subir una copia más clara. La confianza del motor no se muestra como probabilidad de verdad jurídica. Los archivos históricos sin medición se identifican explícitamente.

## Success Criteria

- SC-001: recuperar al menos un campo ficticio antes perdido por inclinación sin perder los campos del control horizontal.
- SC-002: no añadir llamadas OCR en la ruta de texto PDF normal; máximo cuatro lecturas por imagen problemática.
- SC-003: cada lectura dudosa guardada aparece al reabrir su corrida.
- SC-004: suite ordinaria sin regresiones, datos reales fuera de artefactos compartibles, medición reproducible con tiempos y límites.

## Clarifications y supuestos

La autorización «Procede» se aplica a las mejoras técnicas descritas. No hay ambigüedades que bloqueen ese alcance. El etiquetado jurídico de casos reales requiere revisión de la notaría y no se suplanta con los resultados actuales del motor. Las reglas de persona, rol, bien y concepto se preparan como variables de la referencia, sin inferir obligaciones nuevas. Revisión de precisión real pendiente; no impide medir mejoras sintéticas.

## Edge cases

Página vacía, marca diagonal sin cuerpo, página girada, extracción histórica, confianza ausente, fallo del reintento, distintas monedas y datos contradictorios. Ante duda se conserva el aviso; una lectura alternativa no se mezcla carácter a carácter con otra.
