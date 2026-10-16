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

## F51 · Una sola observación por persona sin ficha

**Fecha**: 2026-10-16  
**Alcance**: `nucleo/verificar.py` (`sin_ficha_por_persona`), `expedientes/services.py`, `templates/expedientes/_campo_nombre.html` y catálogo de reglas.

### Origen

En un kardex real, la representante de una empresa no tenía ficha RENIEC en los recaudos. Para ella salían tres observaciones en la misma línea: «Documento sin titular» (ALTA) con su DNI, y dos avisos `SIN_FICHA` (MEDIA), uno con su nombre y otro con su DNI. El usuario: «dice que no tiene documento pero más abajo hay un error que dice lo mismo». Además, algunos títulos mostraban el código interno (`SIN_FICHA`, `CONYUGE_BIEN_PROPIO`).

### Diagnóstico

- **Redundancia**: el núcleo da por separado la capa de personas (`comparar_personas`, F12), que emite `DOCUMENTO_SIN_TITULAR` para un DNI que no está en los recaudos, y la capa de reglas (`revisar`, F38), que emite un `SIN_FICHA` para el nombre y otro para el DNI. Nada las cruzaba.
- **Duplicado**: `revisar` emite un aviso por cada aparición del nombre o del DNI. Todos los avisos de un mismo valor se ubican en la primera línea donde aparece, así que en pantalla son idénticos.
- **Rótulos**: `_campo_nombre.html` no tenía entrada para siete campos del catálogo.

### Comportamiento implementado

- **Persona sin ficha** (`sin_ficha_por_persona`): si el nombre de una persona tiene el aviso `SIN_FICHA`, queda solo ese aviso (MEDIA). Se quitan su `DOCUMENTO_SIN_TITULAR` (ALTA) y el `SIN_FICHA` del DNI que el borrador le asigna. Un aviso repetido del mismo valor sale una sola vez.
- **Persona con ficha**: sin cambios. Un DNI que no es el suyo sigue saliendo como «Documento sin titular» (ALTA).
- **Rótulos**: «Persona sin ficha», «Ñ por marca de agua», «Razón social», «Domicilio fiscal», «Cónyuge con bien propio», «Habilitación del domicilio» y «Observación no reconocida». Se usa «Persona sin ficha» y no «Sin ficha RENIEC» porque el mismo campo marca también el RUC sin ficha de la transferencia vehicular (F45).
- El total de observaciones (F48) sigue igual que el resumen: las observaciones se quitan antes de mostrarse.
- Catálogo de reglas `2026.10.16-15`: las confrontaciones guardadas con el catálogo anterior se recalculan.

### [NEEDS CLARIFICATION]

- **Quitar la ALTA de documento**: la decisión de F38 («cuando la información del cliente no está en los recaudos, la app diga “Sin ficha RENIEC en los recaudos” como aviso MEDIA») se aplicó solo a la capa de reglas. No menciona `DOCUMENTO_SIN_TITULAR`. Se aplica por defecto a la persona marcada sin ficha, porque es el mismo hecho dicho como error. Falta que el usuario lo confirme.

### Límites

- La persona se reconoce por su nombre tal como aparece en la línea del borrador que lo empareja con el DNI. Si el borrador no los empareja, el nombre y el DNI siguen como dos avisos.
- Si el DNI de una persona sin ficha se parece al de otra persona de los recaudos, el «debe decir» del DNI (ALTA) se mantiene.
- Para una persona con ficha cuyo DNI no se parece a ninguno, siguen el `SIN_FICHA` del DNI (MEDIA) y el «Documento sin titular» (ALTA).

### Medición

Confrontación en memoria de los 10 kardex de prueba, main frente a esta rama:

- el kardex del reporte pasa de 9 a 7 observaciones de generales de ley y datos: −1 «Documento sin titular» y −1 `SIN_FICHA`;
- los otros 9 no cambian;
- el expediente con errores sembrados sigue con 8 de 8.

### Verificación

- `tests/test_lectura_borrador.py`: representante sin ficha con el nombre y el DNI repetidos, y DNI ajeno de una persona con ficha.
- `tests/test_expedientes_confrontacion.py`: la confrontación completa deja una sola observación para el representante sin ficha.
- `tests/test_expedientes_confrontacion_ui.py`: ningún campo del catálogo sale con su código interno.
