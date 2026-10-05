# F38 · Lectura del borrador y persona sin ficha

**Fecha**: 2026-10-05  
**Estado**: implementado en el núcleo; cobertura con datos ficticios.  
**Alcance**: `nucleo/verificar.py`, traducción de observaciones en `expedientes/services.py` y catálogo de reglas.

## Origen

De los 12 falsos positivos que quedaban en los 10 expedientes de prueba, cuatro eran errores de lectura del borrador o de una fuente, y dos eran personas sin ficha RENIEC en los recaudos. El usuario decidió el 2026-10-05 que, cuando la información del cliente no está en los recaudos, la app diga «Sin ficha RENIEC en los recaudos» como aviso MEDIA. Recordó además que el DNI siempre tiene 8 dígitos.

## Comportamiento implementado

- **Persona sin ficha** (`SIN_FICHA`, MEDIA): un nombre o un DNI de 8 dígitos del borrador que no se parece a ninguno de los recaudos ya no sale como «no coincide con ninguna fuente» (ALTA). Ahora sale como «Sin ficha RENIEC en los recaudos»: no se puede verificar, así que es aviso, no error.
- **DNI de otra longitud**: si no hay uno cercano en las fuentes, dice «Debe tener 8 dígitos» (ALTA) en lugar de «no coincide».
- **Estado civil de cada persona**: cuando una línea del borrador presenta a varias personas, vale el estado civil que sigue al nombre de la persona, no el primero de la línea. Si la persona aparece como cónyuge de otro («CASADO CON LA SEÑORA …»), está casada.
- **Domicilio en cuadros**: además de la línea con el nombre o el DNI, se miran hasta dos filas siguientes si empiezan por «DOMICILIO» o «DIRECCIÓN» y no traen otro DNI. Así, el domicilio de otra persona sigue sin dar por bueno el de esta.
- **Oficina y provincia registral**: un nombre que en el certificado se pegó a la línea siguiente («LIMA SUPERINTENDENCIA NACIONAL») coincide con el del borrador («LIMA») si uno es el comienzo del otro.
- **Traducción de observaciones**: la app reconoce las frases «Sin ficha RENIEC en los recaudos» y «Debe tener 8 dígitos». Antes de este cambio se habrían mostrado como formato desconocido.

Catálogo de reglas `2026.10.05-5`, con `SIN_FICHA` de severidad MEDIA.

## Medición

Confrontación en memoria de los 10 expedientes de prueba:

- desaparecen 3 falsos positivos: oficina registral, domicilio en el cuadro del anexo y estado civil de una cónyuge;
- 4 alertas de personas sin ficha bajan de ALTA a MEDIA;
- un DNI de 6 dígitos ahora dice «Debe tener 8 dígitos»;
- no hay hallazgos nuevos;
- el expediente con errores sembrados sigue con 8 de 8.

## Límites

- **Ñ de la marca de agua**: la marca de agua puede convertir una N en Ñ en un nombre leído por OCR de una ficha escaneada. Queda pendiente de una decisión del usuario.
- **Cónyuge con «bien propio»**: no se avisa la falta de cónyuge cuando el borrador dice que el otorgante interviene sin su cónyuge por ser bien propio. Queda pendiente de una decisión del usuario.

## Verificación

`tests/test_lectura_borrador.py` usa datos inventados. Cubre:

- la persona sin ficha;
- el DNI de 6 dígitos;
- el estado civil con varias personas en la línea y el de una cónyuge;
- el domicilio en un cuadro;
- la oficina pegada a la línea siguiente.

`tests/test_errores_borrador.py` actualiza el mensaje del DNI de otra longitud.
