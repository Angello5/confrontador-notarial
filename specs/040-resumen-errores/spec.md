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
