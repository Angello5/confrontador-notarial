# Contrato de interfaz: F13 · Anclaje por ficha oficial

Se conserva la confrontación F5/F11/F12: misma ruta, POST, CSRF, permisos de
creador o Administrador, estados y retorno al expediente. El navegador no
aporta personas ni modifica fuentes.

## Personas con ficha

Dentro del `<details>` «Qué se extrajo de los documentos», la tabla actual pasa
a titularse **«Personas con ficha»** y lista solo anclas. Texto de ayuda:
«Cada ficha RENIEC o biométrica es una persona. Los demás documentos solo
añaden datos.» Se conservan todas las columnas F11/F12 y se añaden dos:

| Columna | Valor | Procedencia inmediata |
|---|---|---|
| Cónyuge | Nombre declarado o «No declarado». | Archivo y página de la declaración jurada, o «No ubicada». |
| Datos adjuntos | Lista: nombre (o «Sin nombre») · documento (o «Sin documento»). | Archivo y página de cada adjunto. «Ninguno» si no hay. |

`Estado` solo puede ser «Confirmada» o «Revisión manual»; la segunda indica
dos fichas de la misma persona que no coinciden. Un adjunto con nombre o
documento distinto del ancla **no** cambia el estado: manda la ficha.

Si no hay anclas, la tabla se sustituye por el aviso «Ninguna ficha RENIEC o
biométrica en el legajo.» y el catálogo agregado actual.

## Menciones sin ficha

Tabla aparte, debajo, **«Menciones sin ficha»**, solo si hay menciones. Texto
de ayuda: «Aparecen en los documentos pero no tienen ficha en el legajo. Se
verifican campo por campo, no como persona. Si es un compareciente, falta su
ficha.» Columnas: Nombre, Documento, Cónyuge, Origen (archivo y página de cada
aparición). Sin estado ni campos F12.

## Aporte por documento

Cada documento muestra «Personas con ficha: n» y «Menciones sin ficha: n»
cuando son mayores que cero; el resto no cambia.

## Observaciones

Secciones «Personas», «Regla» y «Ortografía» sin cambio de formato. «Personas»
puede tener menos filas: el documento cruzado exige un titular con ficha.

## Privacidad y estados

`expediente_estado` no cambia: sin adjuntos, cónyuge, menciones ni
procedencias. Nada de eso aparece en logs, trazas o errores. Nombres de
archivo sin ruta y escapados. `NO_DISPONIBLE`, `ADVERTENCIA_CORRESPONDENCIA`,
`ERROR_SEGURO` y `RESULTADO` conservan su comportamiento; la advertencia sigue
mostrando la extracción.
