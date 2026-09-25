# Contrato de interfaz: F12 · Persona ampliada

Se conserva la confrontación F5/F11: misma ruta, POST, CSRF, permisos de
creador o Administrador, estados y retorno al expediente. El navegador no
aporta personas ni modifica fuentes.

## Tabla de extracción autorizada

«Personas extraídas» sigue plegada en `<details>`, dentro de un contenedor
adaptable y con encabezados `<th scope="col">`. Conserva Nombre, Documento,
Procedencia y Estado. Añade una columna por campo:

| Columna | Valor | Procedencia inmediata |
|---|---|---|
| Estado civil | SOLTERO, CASADO, VIUDO, DIVORCIADO o «No detectado». | Nombre de archivo RENIEC y página, o «No ubicada». |
| Fecha de nacimiento | Fecha ISO `aaaa-mm-dd` o «No detectada». | Nombre de archivo RENIEC y página, o «No ubicada». |
| Domicilio | Dirección leída o «No detectado». | Nombre de archivo RENIEC y página, o «No ubicada». |
| Distrito | Distrito del domicilio o «No detectado». | Nombre de archivo RENIEC y página, o «No ubicada». |

Las cuatro procedencias pertenecen a los cuatro valores seleccionados, no a la
identidad en general. Los nombres de archivo se muestran escapados, sin ruta.
Una fecha dudosa y un campo sin etiqueta fiable se muestran como ausencia, sin
OCR crudo. Los valores vienen **solo de RENIEC**; biométrica, pie legal y
`DISTRITO DE NACIMIENTO` no los rellenan. Si dos consultas RENIEC discrepan,
la prioridad por fecha de emisión y el aviso de conflicto quedan pendientes de
la ronda siguiente.

## Observaciones de regla: ronda siguiente

Las tres reglas nuevas se añadirán a la sección «Regla» después de las
históricas, sin alterar las secciones «Personas» y «Ortografía». El núcleo
emitirá datos estructurados y la aplicación los adaptará a mensajes con
persona, valor esperado, hallazgo en borrador, archivo/página y ubicación
segura. Tipos previstos: `ESTADO_CIVIL_DISCREPANTE`,
`CONYUGE_NO_MENCIONADO`, `MENOR_DE_EDAD` y `DOMICILIO_NO_ENCONTRADO`.

US1 mira la cláusula de la persona en el **borrador**, según la frontera del
spec. US2 usa la fecha de hoy y muestra la fecha exacta de referencia. US3
compara las equivalencias aprobadas del spec sin puntos, tildes ni orden del
número. La implementación de estas reglas y del conflicto RENIEC queda para
la siguiente ronda; este corte conserva las observaciones históricas idénticas.

## Privacidad y estados

`expediente_estado` sigue limitado a estados, recuentos, roles,
identificadores y disponibilidad. No incluye valores F12, procedencias ni
observaciones. Tampoco aparecen en logs, trazas o errores. Solo la respuesta
HTML de confrontación, después del control de acceso, puede mostrarlos.
`NO_DISPONIBLE`, `ADVERTENCIA_CORRESPONDENCIA`, `ERROR_SEGURO` y `RESULTADO`
conservan su comportamiento. La tabla mantiene navegación por teclado y foco
visible del layout actual.
