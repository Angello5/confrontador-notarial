# Contrato de interfaz: F12 · Persona ampliada

Interfaz interna de la confrontación F5/F11. Se conservan la ruta, POST, CSRF,
permisos de creador o Administrador y el texto de estados existentes. El
navegador no envía personas, fechas de referencia, fuentes ni umbrales.

## Datos visibles tras autorización

En «Qué se extrajo de los documentos», la tabla «Personas extraídas» conserva
Nombre, Documento, Procedencia y Estado. Añade:

| Columna | Valor | Procedencia visible |
|---|---|---|
| Estado civil | SOLTERO, CASADO, VIUDO o DIVORCIADO; o «No detectado». | Archivo y página del estado civil, o «No ubicada». |
| Fecha de nacimiento | Fecha ISO `aaaa-mm-dd`; o «No detectada». | Archivo y página de la fecha, o «No ubicada». |
| Domicilio | Dirección leída; o «No detectado». | Archivo y página del domicilio, o «No ubicada». |
| Distrito | Distrito del domicilio; o «No detectado». | Archivo y página del distrito, o «No ubicada». |

El archivo se muestra solo como nombre original autorizado, escapado por la
plantilla, nunca como ruta. Las celdas proceden del valor elegido por
`unificar_personas()`, no de la procedencia general de identidad. Si RENIEC y
BIOMETRICA discrepan en estado civil, se muestra RENIEC y un aviso textual de
revisión manual que identifica el campo (`REVISION_MANUAL_ESTADO_CIVIL` en el
núcleo); el color no es la única señal.
La tabla sigue plegada por defecto en `<details>` y conserva encabezados
`<th scope="col">`; en pantallas estrechas se usa el contenedor adaptable.

## Observaciones de regla

Las reglas nuevas aparecen en la sección existente **Regla**, después de las
observaciones históricas. Cada fila indica persona, fuente y archivo/página,
hallazgo del borrador o ausencia, valor esperado, motivo y ubicación cuando
pueda situarse. Nunca muestra el texto completo del documento. Tipos previstos:

| Tipo estructurado del núcleo | Mensaje claro |
|---|---|
| `ESTADO_CIVIL_DISCREPANTE` | La persona figura con otro estado civil en la fuente y en el texto comparado. |
| `CONYUGE_NO_MENCIONADO` | La fuente indica persona casada y el texto comparado no menciona cónyuge en el contexto aprobado. |
| `MENOR_DE_EDAD` | Indica edad cumplida, fecha de nacimiento y fecha de referencia aprobada. |
| `DOMICILIO_NO_ENCONTRADO` | Indica domicilio de la fuente que no aparece tras la normalización aprobada. |
| `CONFLICTO_ESTADO_CIVIL_FUENTES` | RENIEC y biométrica difieren; se conserva RENIEC y se pide revisión manual. |

El alcance de «texto comparado», la fecha de referencia y las abreviaturas
siguen sujetos a las preguntas de [research.md](../research.md). No se emite
una observación que dependa de una respuesta aún ausente. Una fuente sin
lectura fiable produce «No detectado» en la tabla y ninguna afirmación de esa
regla. Una persona sin documento no participa en la regla de cónyuge. Ningún
estado «sin observaciones» se presenta como aprobación si hay conflicto de
fuentes pendiente de revisión.

Las filas históricas de `Regla`, `Personas` y `Ortografía` mantienen orden,
campos, texto y recuentos para las mismas entradas. Los diccionarios nuevos
del núcleo se convierten directamente en filas de presentación; el parser de
cadenas de `revisar()` solo trata cadenas antiguas. Un tipo no reconocido se
muestra como formato desconocido seguro, sin volcar el dict ni texto.

## Privacidad y estados

`expediente_estado` sigue enviando únicamente estado, recuentos, roles,
identificadores y disponibilidad. No se agregan estado civil, nacimiento,
domicilio, distrito, procedencia, observaciones ni fragmentos al JSON de
sondeo. Logs, trazas y errores genéricos tampoco incorporan estos datos.
Solo la respuesta HTML de confrontación, tras el control de acceso existente,
contiene los valores personales.

`NO_DISPONIBLE`, `ADVERTENCIA_CORRESPONDENCIA`, `ERROR_SEGURO`, `RESULTADO`
y el retorno al expediente conservan el comportamiento F11. El aviso de
conflicto usa texto y `role="alert"`; los resultados usan `role="status"`
o `aria-live="polite"`. Foco visible y teclado siguen el layout actual.
Para una fecha o valor ilegible se informa ausencia sin exponer OCR crudo ni
dar una instrucción técnica al usuario.
