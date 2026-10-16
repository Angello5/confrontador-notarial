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
