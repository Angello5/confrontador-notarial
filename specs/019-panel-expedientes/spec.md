# Feature Specification: F25 · Panel de expedientes: abrir, editar y eliminar

**Feature Branch**: `Angello5/panel-de-expedientes-abrir-editar-eliminar-f25-panel-expedientes`

**Created**: 2026-09-28

**Status**: Implementado e integrado (PR #55)

**Input**: «Cuando estoy en el panel de expediente se debe poder abrir, editar y eliminar con botones». Hoy la lista (estilo F14) solo tiene «Abrir».

## Principio

**Eliminar no destruye la auditoría.** El manifiesto (`Corrida`, `DecisionCorreccion`) es inmutable por contrato (Anexo A capa 7, Anexo B P-08) y protege al expediente (`on_delete=PROTECT`); «Eliminar» archiva.

## Requirements *(mandatory)*

- **FR-001 (botones)**: Cada fila de la lista y la cabecera del detalle muestran Abrir (solo en la lista), Editar y Eliminar: botones Bootstrap con icono `aria-hidden` y texto visible. Sin CSS en línea.
- **FR-002 (permisos)**: Editar, eliminar y ver exigen los permisos actuales: creador del expediente (rol Usuario) o Administrador. Otro usuario recibe 403.
- **FR-003 (editar)**: `GET /expedientes/<pk>/editar/` muestra el formulario de creación (`ExpedienteForm`) con el código actual; `POST` con CSRF valida igual que al crear (obligatorio, sin espacios sobrantes, único) y vuelve al detalle.
- **FR-004 (eliminar)**: `GET /expedientes/<pk>/eliminar/` pide confirmación explícita mostrando el código; `POST` con CSRF archiva el expediente.
- **FR-005 (archivar)** Decisión del propietario (2026-09-28): eliminar es solo lógico, nunca físico. Archivar guarda `archivado_el` y `archivado_por` (migración `0005`). Un expediente archivado desaparece de la lista, el inicio y sus métricas; su detalle, cargas, estado, confrontaciones e historial responden 404. El manifiesto y los documentos se conservan intactos.
- **FR-006 (restaurar)**: Un Administrador ve los archivados con el filtro «Archivados» (`?archivados=1`) de la lista y los restaura con `POST /expedientes/<pk>/restaurar/` (CSRF). Otro rol recibe 403 y el filtro no le muestra archivados.
- **FR-007**: La supresión definitiva de datos personales sigue siendo el comando `suprimir_texto_expediente`, fuera de la interfaz.
- **FR-008**: Sin dependencias nuevas ni IA. Tests con datos ficticios.

## Success Criteria *(mandatory)*

- **SC-001**: Desde la lista, un usuario abre, edita y elimina su expediente con un clic más la confirmación.
- **SC-002**: Tras archivar, `Corrida` y `DecisionCorreccion` del expediente siguen existiendo sin cambios.

## Assumptions

- El worker sigue procesando documentos ya en cola de un expediente archivado: no se pierden datos y nadie los ve hasta restaurar.
- Archivar no cambia el código. Desde F28 el código es único solo entre activos: un archivado no bloquea crear otro con el mismo código (`specs/022-codigo-y-marca`).

## F59 · Total de errores y hora real de actualización en la lista

**Fecha**: 2026-10-20  
**Estado**: implementado en «Mis kardex», «Mis TV» y «Archivados»; cobertura con datos ficticios.  
**Alcance**: `expedientes_con_resumen` y `observaciones_vigentes` en `expedientes/services.py`, `templates/expedientes/lista.html` y la fecha de «Últimos kardex» en `templates/core/home.html`.

### Origen

Pedido del usuario (2026-10-20): ver en la lista de kardex el total de errores y la hora en que de verdad cambió el kardex, «para tener el dato más rápido», sin abrir cada uno.

### Comportamiento implementado

- **Columna «Errores»**, entre «Documentos» y «Actualizado», con el número alineado como «Documentos».
  - Es el total de observaciones de la confrontación vigente del kardex: el mismo número que la pantalla de resultado muestra como «N observaciones para revisar» (F48), contado con la misma función que el ranking por digitadora (F57, `_observaciones`). Un kardex confrontado sin observaciones muestra 0.
  - La confrontación vigente es la de `corrida_vigente`: la última corrida del borrador con sus documentos actuales y el catálogo actual. Comparten la comparación (`_primera_vigente`).
  - Muestra «—» cuando no hay resultado: sin borrador, documentos pendientes o con error, documentos cambiados desde la última confrontación, o una confrontación que no llegó a comparar (advertencia de correspondencia, no disponible o error). En esos casos la pantalla de resultado tampoco da un total.
- **«Actualizado»** es la fecha y hora en que se procesó el último documento del kardex (máximo de `procesado_el`). Si todavía no hay ningún documento procesado, se usa la fecha del kardex (`actualizado_el`), como antes.
  - El orden inicial (más reciente arriba), el atributo `data-t` y el botón «Actualizado» usan ese mismo valor.
  - «Últimos kardex» del Inicio de la usuaria sale de la misma lista: muestra y ordena por el mismo valor.
- **Consultas**: el total de toda la lista se resuelve en bloque con tres consultas (documentos, corridas candidatas y hallazgos de las vigentes), sin importar cuántas filas haya. La hora sale de la misma consulta de la lista.
- **No cambia**: el filtro por estado, la búsqueda, las acciones de cada fila, los permisos ni el Inicio del administrador.

### [NEEDS CLARIFICATION]

- **Varios borradores**: si un kardex tiene más de un borrador, la columna toma el último subido. Si el último aún no tiene resultado, muestra «—» aunque un borrador anterior sí lo tenga. La otra lectura sería sumar los de todos los borradores.

### Límites

- El conteo de «Documentos» sigue haciendo una consulta ligera por fila, como antes de F59.
- Un documento que se vuelve a leer reemplaza su `procesado_el`. Eliminar el último documento procesado devuelve «Actualizado» a la hora del anterior.

### Requisitos de seguridad

- Sin cambios: mismas vistas, roles y visibilidad (`expedientes_visibles`). La columna muestra un número que la usuaria ya podía ver en la pantalla de resultado; no expone texto ni nombres de archivo.

### Requisitos de UX (principio VIII)

- Ahorro de tiempo y reconocimiento antes que recuerdo: el total se lee en la lista sin abrir el kardex.
- Consistencia: el mismo total que la pantalla de resultado y el ranking, el mismo «—» que el historial de confrontaciones para «sin dato» y el estilo actual de la tabla (`erp.css` sin cambios).

### Verificación

- `tests/test_panel_expedientes.py`:
  - total correcto (4 con personas, datos y lingüísticas; 0 sin observaciones), igual al número de observaciones de la pantalla de resultado;
  - «—» sin documentos, con documentos cambiados después de confrontar y con advertencia de correspondencia;
  - el número de consultas a las corridas no crece con las filas;
  - «Mis TV» y «Archivados» muestran la columna y su total;
  - «Actualizado» con la hora del último documento procesado, la del kardex sin documentos procesados, `data-t` con el mismo valor y orden de la lista.
- Capturas con Firefox headless de «Mis kardex», «Mis TV» e Inicio con datos ficticios en un servidor propio, a 1280 px y 390 px; el botón «Actualizado» invierte el orden.
