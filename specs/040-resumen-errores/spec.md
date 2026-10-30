# F48 · Total de observaciones al aplicar correcciones

**Fecha**: 2026-10-16  
**Estado**: implementado en la pantalla de resultado; cobertura con datos ficticios.  
**Alcance**: `templates/expedientes/confrontacion.html` y `static/css/erp.css`.

## Origen

Pedido del usuario (2026-10-16): «Cuando te da el resultado abajo del numero de kardex te dice una corrida, borra eso y los errores señalados deben ser los totales, en el momento que le doy a generar el word cambiando los errores la cantidad de errores que aparece en ese recuadro no es el total, quiero que sea el total y las que no se pueden cambiar se encuentren bloqueadas».

## Diagnóstico

- El resumen («N observaciones para revisar») y los filtros por severidad cuentan todas las observaciones de la pantalla: generales de ley, datos y texto.
- El recuadro de «Aplicar correcciones» (la barra fija y su ventana de confirmación) contaba otra cosa: las correcciones propuestas de F21 (`resultado.correcciones`). Las dos cifras se separan por dos motivos:
  - Muchas observaciones no tienen corrección propuesta y no aparecían en el recuadro. Son las personas, los datos que faltan, los que no coinciden con ninguna fuente y los que no tienen ficha. También el número en letras, el área y las demás reglas de F21 FR-005, las de la persona ampliada, las que no tienen fuente localizable y las lingüísticas, que solo informan.
  - Un mismo par erróneo → correcto que aparece varias veces es una sola corrección (F21 FR-001), aplicada a todas sus apariciones.
- Ejemplo ficticio: un nombre mal escrito, un DNI erróneo repetido y un documento sin titular dan 4 observaciones. El recuadro decía «2 de 2 correcciones marcadas» y «¿Aplicar 2 correcciones?».

## Comportamiento implementado

- **Cabecera**: ya no muestra «Revisión N» bajo el kardex. El número de corrida se conserva donde da trazabilidad (F20): el informe imprimible («Confrontación N»), los metadatos del informe Word, el formulario de aplicación y el visor del borrador.
- **Ventana de confirmación**:
  - Muestra una fila por observación, en el orden de la lista. El total coincide con el resumen: «4 observaciones señaladas: 3 marcadas para corregir · 1 bloqueada».
  - **Fila corregible**: casilla marcada por defecto, ligada a su corrección con el mismo emparejamiento de F29. Si dos observaciones comparten corrección, marcar o desmarcar una cambia las dos, porque es el mismo reemplazo.
  - **Fila bloqueada**: casilla deshabilitada, fila atenuada y el texto «No admite corrección automática». La casilla enlaza el motivo con `aria-describedby`: «no tienen un valor que pueda reemplazarse con seguridad en el Word. Corríjalas a mano».
  - Una propuesta sin observación compatible se lista igual como fila corregible. Si no, se registraría como excluida sin que el usuario la viera.
  - El botón dice «Aplicar correcciones», sin número.
- **Barra**: «3 de 4 observaciones marcadas para corregir» y «1 no admite corrección automática».
- **No cambia**:
  - qué es corregible ni cómo se calculan las propuestas (F21);
  - el envío, la verificación de la corrida y el registro de la decisión;
  - las cifras finales de la ventana de avance (F40): aplicadas, excluidas y no aplicadas siguen contando correcciones;
  - el borrador que no es Word: la barra sigue informando las correcciones propuestas y no ofrece aplicar.

## [NEEDS CLARIFICATION]

- **Qué es «el total»**: se toma el número de «N observaciones para revisar», que incluye las lingüísticas (severidad baja). La otra lectura posible es contar solo generales de ley y datos.
- **Cifras finales**: tras aplicar, «2 aplicadas» cuenta correcciones, no observaciones. Si el usuario quiere verlas también por observación, el servidor debe devolver qué correcciones aplicó.
- **Motivo del bloqueo**: es uno solo para todas las bloqueadas. Dar el motivo de cada regla exigiría que la confrontación lo guardara.

## Límites

- El emparejamiento de F29 solo normaliza mayúsculas y espacios. Una observación que difiere de su propuesta solo en las tildes aparece bloqueada, aunque el reemplazo también la corrige.

## Requisitos de seguridad

- Sin cambios: mismos roles y permisos, POST con CSRF, corrida y huella verificadas en el servidor.
- Las casillas deshabilitadas no se envían, y el servidor sigue ignorando cualquier identificador que no esté entre las propuestas recalculadas.

## Requisitos de UX (principio VIII)

- Visibilidad: el recuadro muestra el mismo total que el resumen y cuántas quedan bloqueadas.
- Prevención de errores: una observación que no se puede corregir no se puede marcar.
- Accesibilidad: cada casilla tiene una etiqueta, las bloqueadas enlazan su motivo y el estilo atenuado reutiliza los colores de `erp.css`.

## Verificación

- `tests/test_correccion_expedientes.py`: cabecera sin «Revisión», corrida conservada en el formulario, el visor y el informe; recuadro con una fila por observación, casilla deshabilitada y motivo enlazado.
- `tests/confrontacion_frontend.test.cjs` (`node --test`): total igual al número de observaciones, filas bloqueadas, corrección compartida por dos observaciones y propuesta sin observación compatible.
- Captura con Firefox headless del expediente ficticio en un servidor propio: recuadro a 1280 px y 390 px.

## F56 · Observaciones con el dato a la vista y una sola pestaña «Todas»

**Fecha**: 2026-10-20  
**Estado**: implementado en la pantalla de resultado; cobertura con datos ficticios.  
**Alcance**: panel de observaciones de `templates/expedientes/confrontacion.html` (pestañas, lista e ítems) y sus estilos en `static/css/erp.css`.

### Origen

Pedido del usuario (2026-10-20): «Panel de observaciones: mostrar el dato concreto (nombre o DNI) sin tener que hacer clic» y «dejar solo la pestaña "Todas"». Premisa: el sistema tiene que ahorrar tiempo.

### Diagnóstico

- Cada ítem ya traía lo hallado y lo correcto en el HTML, pero desde F34 la hoja de estilos lo ocultaba (`.revision-documento .obs-item .cambio { display: none; }`). El ítem mostraba solo el rótulo («Nombre», «DNI», «Persona sin ficha») o el nombre de la persona, y para ver el dato había que abrir el detalle.
- Las pestañas «Generales de ley», «Datos» y «Texto» repetían la etiqueta de capa que ya lleva cada ítem y obligaban a cambiar de pestaña para ver todo. Además la pestaña decía «Datos» y el ítem, «Regla».

### Comportamiento implementado

- **Ítem**: bajo el rótulo, lo hallado tachado → lo correcto en negrita, por ejemplo «Partida registral» / ~~80000002~~ → **80000001**. Vale igual para generales de ley, datos, lingüísticas y transferencia vehicular.
  - Si los dos valores caben, van en una línea. Si no, lo correcto pasa a la línea siguiente con su flecha, para que se vea dónde difieren dos nombres o dos direcciones parecidos.
  - Solo un valor más ancho que el panel se recorta con elipsis. El valor completo está en el detalle y en el texto emergente («Dice: X · Debe decir: Y»).
  - La flecha es decorativa. Para el lector de pantalla, el ítem dice «Dice: X, debe decir: Y» (en las lingüísticas, «Texto: X, sugerencia: Y»), con las mismas palabras del detalle.
  - El tachado y la negrita acompañan al color: el dato no depende solo de él.
  - Se conservan la severidad, la etiqueta de capa («Generales de ley», «Regla», «Lingüístico»), la línea y la marca «Marcada para corregir».
  - El título de las lingüísticas empieza en mayúscula («No existe en castellano»).
- **Una sola lista**: queda «Todas» con su contador, como rótulo de la lista (un `h2`), no como pestaña: un control único que no cambia nada no es una pestaña. Se retiraron las otras tres pestañas, el estado `capa` y su lógica (`contar`, el `$watch`). El aviso lingüístico ya no depende de la pestaña y se muestra siempre que existe.
- **No cambia**:
  - los filtros por severidad (alta, media, baja), que siguen filtrando la lista y la cuentan entera;
  - el contador de «Todas», que sigue al filtro de severidad, como antes;
  - el detalle («Dice» / «Debe decir»), la navegación con ↑/↓ y el visor del borrador (F32, F52);
  - los totales de F48 y la ventana de aplicar correcciones;
  - el informe, que sigue separando por capa (`contarCapa`).

### [NEEDS CLARIFICATION]

- **Frases como valor**: algunas observaciones traen una frase en lugar de un valor, como «No aparece en el borrador» (tachada) o «Sin documento conocido», «Sin ficha RENIEC en los recaudos» y «Sin sugerencia» (en negrita, como si fueran lo correcto). Es lo mismo que muestra el detalle. Distinguirlas exigiría que la confrontación marcara qué es frase y qué es valor.
- **Etiqueta «Regla»**: con las pestañas fuera, el ítem dice «Regla» como el informe. La pestaña decía «Datos». Si se prefiere «Datos», se cambia también en el informe.
- **Altura de la lista**: la lista del lateral mantiene su alto de F34 (32 % de la pantalla). Con el dato a la vista cada ítem ocupa una o dos líneas más, y entran unos tres o cuatro ítems sin desplazarse.

### Requisitos de seguridad

- Sin cambios: misma vista y mismos permisos. El ítem y su texto emergente repiten valores que ya estaban en la página; no se expone ningún dato nuevo.

### Requisitos de UX (principio VIII)

- Ahorro de tiempo: el dato concreto se lee sin abrir cada observación. La lista se recorre con ↑/↓ sin cambiar de pestaña.
- Accesibilidad: texto alternativo para la flecha, contraste ≥ 7,9:1 de lo hallado y lo correcto sobre el fondo del ítem (también el seleccionado), sin `!important` y con `position: relative` para que el texto oculto no desborde la lista.

### Verificación

- `tests/test_expedientes_confrontacion_ui.py`:
  - cada ítem muestra lo hallado y lo correcto, con el texto para el lector de pantalla y el texto emergente (personas, nombre, partida y lingüística);
  - no queda ninguna pestaña, «Todas» queda como rótulo, el aviso lingüístico no depende de la capa y siguen los tres filtros de severidad;
  - la hoja de estilos ya no oculta el dato y lo recorta con elipsis.
- `tests/test_vehicular_ui.py`: el ítem «Placa» de una confrontación vehicular muestra la placa hallada y la correcta.
- `tests/test_generales_de_ley.py`: la etiqueta «Generales de ley» pasa de la pestaña al ítem.
- `tests/confrontacion_frontend.test.cjs` (`node --test`): sin estado `capa`, la lista se filtra solo por severidad, los contadores cuentan la lista entera y ↑/↓ recorre todas.
- Capturas con Firefox headless, antes y después, del kardex y de la transferencia vehicular ficticios en un servidor propio, a 1280 px y 390 px.

## F60 · Los avisos se entienden sin interpretar «Dice / Debe decir»

**Fecha**: 2026-10-21  
**Estado**: implementado en la pantalla de resultado, sus exportaciones y la vista de la corrida; cobertura con datos ficticios.  
**Alcance**: presentación. `aviso_de` en `expedientes/services.py` (aplicado al mostrar en `resultado_de_corrida` y `filas_corrida`), `templates/expedientes/confrontacion.html`, `templates/expedientes/_obs_cambio.html`, `templates/expedientes/corrida.html`, `static/js/reporte-docx.js` y `static/css/erp.css`.

### Origen

Revisión del usuario de la pantalla de resultado (2026-10-21). Desde F56 la lista muestra ~~hallado~~ → **esperado** y el detalle «Dice» / «Debe decir», como si toda observación fuera una corrección. Con tres avisos eso confundía (ejemplos ficticios):

- **Cónyuge con bien propio**: «Dice: ALBA ZURBELIA LUMARIA: Interviene sin su cónyuge por ser bien propio» / «Debe decir: RENIEC: CASADO». El usuario: «esa parte no me queda muy claro». No hay nada que «deba decir»: hay que confirmar que el bien es propio.
- **Número en letras**: ~~2,50 (DOS MIL QUINIENTOS CON 00/100 SOLES)~~ → **2,50** parecía decir «reemplace todo por 2,50». La regla solo sabe que la cifra y las letras no valen lo mismo, no cuál está mal, y no es corregible en el Word (F21 FR-005).
- **Domicilio no encontrado**: «ALBA ZURBELIA LUMARIA: No aparece en el borrador» se leyó como «la persona no aparece», cuando lo que falta es su domicilio de RENIEC.

### Comportamiento implementado

- **Qué es un aviso**: una observación en la que «Debe decir» no tiene sentido. Para cada una, `aviso_de` arma tres textos a partir de lo que ya guardó la corrida: qué hay en el borrador, qué verificar y la línea de la lista.

| Observación | En el borrador | Qué verificar | Línea de la lista |
|---|---|---|---|
| Cónyuge con bien propio | lo hallado | «RENIEC indica CASADO. Confirme que el bien es propio; si no lo es, debe intervenir el cónyuge.» | «ALBA ZURBELIA LUMARIA: casado según RENIEC · confirme bien propio» |
| Número en letras / Área | lo hallado | «La cifra y las letras (del área) no valen lo mismo. Corrija la que no corresponda.» | «Cifra y letras no coinciden: …» |
| Copropiedad | lo hallado | «Las cuotas de copropiedad no suman 100 %. Corrija la que no corresponda.» | «Las cuotas no suman 100 %: …» |
| Domicilio no encontrado | «ALBA ZURBELIA LUMARIA: su domicilio de RENIEC no aparece en el borrador» | «Domicilio según RENIEC: CALLE FICTICIA 123. Verifique el domicilio que el borrador indica para esta persona.» | «ALBA ZURBELIA LUMARIA: su domicilio de RENIEC no aparece · CALLE FICTICIA 123» |
| Menor de edad | el nombre | «Es menor de edad: 16 años al 2026-10-20. Fecha de nacimiento: 2010-05-01. Verifique cómo interviene.» | «ALBA ZURBELIA LUMARIA: 16 años al 2026-10-20» |
| Persona sin ficha | lo hallado | «Sin ficha RENIEC (o RUC) en los recaudos[; la minuta dice «…»]. No se pudo verificar: revíselo a mano o cargue la ficha.» | «Sin ficha RENIEC en los recaudos: …» |
| Ñ por marca de agua | lo hallado | «La ficha escaneada muestra una Ñ que puede ser la marca de agua. Verifique el nombre con el DNI.» | «Posible Ñ por marca de agua: …» |
| Documento sin titular | el documento | «Ninguna persona de los recaudos tiene este documento. Verifique el número.» | «Sin titular en los recaudos: …» |
| «No coincide con ninguna fuente» (partida, RUC, dato registral…) | lo hallado | «No coincide con ninguna fuente. Verifique el dato en los documentos.» | «No coincide con ninguna fuente: …» |
| DNI de longitud incorrecta | lo hallado | «Debe tener 8 dígitos. Verifique el número.» | «Debe tener 8 dígitos: …» |
| Anexo omitido | «No aparece en el borrador» | «La minuta incluye «ANEXO 1 - HOJA RESUMEN». Verifique que el borrador lo incluya.» | «Falta en el borrador: …» |
| Precio (transferencia vehicular) | «No aparece en el borrador» | «El acta no indica el precio de la transferencia. Verifique que lo incluya.» | «El acta no indica el precio de la transferencia» |

Desde F64 (`specs/047-sugerencias-cifras/`), los avisos de número en letras, área y copropiedad dicen además lo que trae la minuta y la sugerencia («Se sugiere …») cuando hay con qué desempatar; si la minuta no trae el dato, lo dicen sin elegir. Las confrontaciones anteriores a F64 se ven con el texto de esta tabla.

- **Lista**: el aviso es una línea sin tachar, en el color de texto secundario y sin flecha. Si no cabe, se parte en varias líneas (no se recorta), porque la acción va al final. El texto emergente dice «En el borrador: … · Qué verificar: …».
- **Detalle**: los rótulos son «En el borrador» y «Qué verificar», sin el rojo de lo hallado ni el verde de lo correcto. El texto de «Qué verificar» va sin negrita, porque es una frase.
- **Informe imprimible, informe Word, tabla exportada (CSV) y vista de la corrida**: conservan sus columnas «Dice» y «Debe decir». En un aviso, «Dice» lleva el texto de «En el borrador» y la otra columna, «Qué verificar: …». Ninguno dice ya «Debe decir: RENIEC: CASADO». En el Word, el aviso va sin rojo, verde ni tachado, también en «Atención prioritaria».
- **Ventana de aplicar correcciones (F48)**: la fila bloqueada de un aviso muestra su línea de la lista, sin tachar.
- **Confrontaciones ya guardadas**: se ven igual, porque el aviso se arma al mostrar. No hace falta recalcularlas.
- **No cambia**:
  - las reglas, sus severidades, el catálogo ni su versión;
  - qué es corregible (F21) ni el emparejamiento de las correcciones (F29). Un aviso nunca tiene corrección, y en la página su «esperado» queda vacío;
  - el texto guardado en la corrida ni su huella;
  - las marcas del visor del borrador (F32, F52), que siguen ubicando lo hallado;
  - las correcciones de verdad (nombre, DNI, partida, estado civil discrepante, cónyuge no mencionado, habilitación del domicilio, género, correlativo, domicilio fiscal, «falta» con un valor): siguen con ~~hallado~~ → **esperado** y «Dice» / «Debe decir».

### [NEEDS CLARIFICATION]

- **Textos de «Qué verificar»**: los de bien propio y número en letras siguen la propuesta de la revisión. Los demás son de presentación y no deciden nada de negocio: los debe confirmar la notaría. Son el de menor de edad («Verifique cómo interviene»), persona sin ficha («cargue la ficha»), anexo y precio.
- **Cónyuge no mencionado**: se dejó como corrección («Debe decir: RENIEC: CASADO»), porque el borrador no indica el estado civil. Si la notaría lo considera un aviso, pasa a la tabla con un texto suyo.
- **Encabezados de columna**: los informes y la exportación siguen diciendo «Dice» / «Debe decir». En un aviso, la celda empieza con «Qué verificar:». Otra opción es renombrar la columna («Debe decir o qué verificar»).

### Requisitos de seguridad

- Sin cambios: misma vista y mismos permisos. Los textos se arman con valores que ya estaban en la página y no exponen ningún dato nuevo. Se escapan igual que antes, porque son variables de la plantilla.

### Requisitos de UX (principio VIII)

- Coincidencia con el mundo real: el aviso dice qué hay que confirmar, no un reemplazo que no existe.
- Reconocer antes que recordar: la línea de la lista ya dice qué verificar, sin abrir el detalle.
- Accesibilidad: el lector de pantalla oye «Qué verificar: …» en la lista, con los mismos rótulos del detalle. El aviso no depende del color: no lleva tachado ni flecha. Sin `!important`.

### Verificación

- `tests/test_expedientes_confrontacion_ui.py`:
  - `aviso_de` da los tres textos de cada aviso de la tabla y devuelve `None` en las correcciones (partida, documento cruzado, estado civil, «falta» con valor, ortografía);
  - en la pantalla, bien propio, número en letras y domicilio salen sin tachar, con «Qué verificar» para el lector de pantalla. El detalle dice «En el borrador» / «Qué verificar» y la partida sigue con «Dice» / «Debe decir»;
  - los datos del informe Word y de la tabla exportada, el informe imprimible y la vista de la corrida no dicen «RENIEC: CASADO». La corrida guardada sí lo conserva.
- `tests/confrontacion_frontend.test.cjs` (`node --test`): el Word escribe «Qué verificar: …» sin tachado. La ventana de aplicar recibe la línea del aviso, y el CSV escribe «Qué verificar: …» y conserva la corrección de la partida.
- Capturas con Firefox headless de kardex ficticios en un servidor propio (puerto 8012): número en letras, bien propio y domicilio a 1280 px, bien propio a 390 px y la vista de la corrida.
