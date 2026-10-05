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

- **Ñ por marca de agua** (`NOMBRE_MARCA_AGUA`, MEDIA): en la ficha escaneada, la marca de agua puede dibujar una tilde sobre una N («DAÑIEL»). Si la minuta y el borrador escriben el mismo nombre con N, sale «Posible Ñ por marca de agua; verifique el DNI», en lugar de «debe decir» o «falta» (ALTA), y sin corrección automática. Es una decisión del usuario del 2026-10-05.
- **Bien propio** (`CONYUGE_BIEN_PROPIO`, MEDIA): si una persona está casada según RENIEC, el borrador no nombra a su cónyuge y declara que interviene «sin la intervención de su cónyuge por ser bien propio», sale un aviso para confirmar que el bien es propio, en lugar de «cónyuge no mencionado». Es una decisión del usuario del 2026-10-05.

Catálogo de reglas `2026.10.05-6`. `SIN_FICHA`, `NOMBRE_MARCA_AGUA` y `CONYUGE_BIEN_PROPIO` tienen severidad MEDIA.

## Medición

Confrontación en memoria de los 10 expedientes de prueba:

- desaparecen 3 falsos positivos: oficina registral, domicilio en el cuadro del anexo y estado civil de una cónyuge;
- 4 alertas de personas sin ficha bajan de ALTA a MEDIA;
- un nombre con Ñ de marca de agua y un cónyuge con bien propio pasan a aviso MEDIA;
- un DNI de 6 dígitos ahora dice «Debe tener 8 dígitos»;
- no hay hallazgos nuevos;
- el expediente con errores sembrados sigue con 8 de 8.

## Límites

- **Ñ por marca de agua**: si la minuta trae la Ñ, el borrador que la omite sigue en error (ALTA). Si la minuta y el borrador omiten a la vez una Ñ real, solo queda el aviso; por eso pide verificar con el DNI.

## Verificación

`tests/test_lectura_borrador.py` usa datos inventados. Cubre:

- la persona sin ficha;
- el DNI de 6 dígitos;
- el estado civil con varias personas en la línea y el de una cónyuge;
- el domicilio en un cuadro;
- la oficina pegada a la línea siguiente;
- la Ñ de marca de agua;
- el bien propio.

`tests/test_errores_borrador.py` actualiza el mensaje del DNI de otra longitud.
