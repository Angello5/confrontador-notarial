# Feature Specification: F26 · Confrontación automática al terminar la carga

**Feature Branch**: `f26-confrontacion-automatica`

**Created**: 2026-09-28

**Status**: Draft

**Input**: Pedido del propietario: «la confrontación debe hacerse al mismo tiempo que la carga de archivos, ya que si no es un tiempo extendido que dice confrontar y ya debería estar hecho; que no se pinte de azul el botón si no están confrontados con anterioridad». Hoy el usuario pulsa «Confrontar borrador» y espera el cálculo completo.

## Principio

**El resultado se calcula una vez, en el worker, y la pantalla solo lo muestra.** La corrida del manifiesto (F20) es la única fuente del resultado guardado.

## Requirements *(mandatory)*

- **FR-001 (worker)**: Al final de cada vuelta de `procesar_documentos`, cada borrador `LISTO` cuya confrontación esté disponible (`estado_confrontacion`) y que no tenga corrida para sus entradas actuales se confronta y registra una `Corrida` con `origen = AUTOMATICA` y `usuario = Documento.subido_por` del borrador.
- **FR-002 (entradas actuales)**: Una corrida corresponde a las entradas actuales si es del mismo borrador, con la versión actual del catálogo y las mismas entradas (rol, nombre, hash del archivo, `version_extractor`, estado, en el orden de `registrar_corrida`). El hash del texto no se recalcula para esta comparación: el texto queda determinado por hash del archivo + `version_extractor`.
- **FR-003 (no repetir)**: Si ya existe una corrida (de cualquier origen y estado) para las entradas actuales, el worker no confronta. Si se sube o elimina un documento, las entradas cambian y la siguiente vuelta vuelve a confrontar; si vuelven a ser idénticas a las de una corrida anterior, esa corrida se reutiliza (misma entrada, mismo resultado; Principio I).
- **FR-004 (origen)**: `Corrida.origen` (`AUTOMATICA` / `MANUAL`, por defecto `MANUAL`) con migración. La corrida sigue inmutable; la huella no cambia (sigue cubriendo solo los hallazgos).
- **FR-005 (presentación)**: `Corrida.presentacion` (JSON) guarda el resumen de extracción y el aviso lingüístico para mostrar el resultado sin recalcular. No forma parte de la huella ni de la reconstrucción.
- **FR-006 (botón)**: En la pantalla del expediente, por borrador:
  - corrida vigente no ERROR → enlace azul (`btn-primary`) «Ver resultado» que abre el resultado guardado, y acción secundaria «Volver a confrontar» (POST manual, corrida `MANUAL`);
  - documentos en proceso, o confrontación disponible sin corrida → botón gris deshabilitado «Confrontando…»;
  - corrida vigente ERROR → botón secundario «Volver a confrontar» habilitado y el mensaje de error;
  - confrontación no disponible por otro motivo (falta un rol, documento con error) → botón gris deshabilitado con el mensaje actual.
- **FR-007 (sondeo)**: El JSON de estado añade solo `resultado_listo` (booleano) por borrador; ni hallazgos, ni rutas, ni identificadores de corrida. El sondeo continúa mientras haya un borrador confrontable sin corrida.
- **FR-008 (ver resultado)**: `GET /expedientes/<pk>/documentos/<doc_id>/resultado/` renderiza la pantalla de confrontación desde la corrida vigente (hallazgos + presentación) sin llamar al núcleo. Sin corrida vigente, vuelve al expediente con un aviso. Mismos permisos que el expediente.
- **FR-009 (error)**: Un fallo del núcleo en la confrontación automática deja una corrida `ERROR` (F20 FR-009), sin reintentos automáticos para las mismas entradas; el usuario reintenta con «Volver a confrontar».
- **FR-010 (F21)**: La vista consolidada de correcciones de F21 no está en `main`. Gancho: la vista de resultado recibe `corrida` en el contexto; F21 la usa al fusionarse.

## Success Criteria *(mandatory)*

- **SC-001**: Al quedar todos los documentos LISTOS, una vuelta del worker deja una corrida AUTOMATICA por borrador; una segunda vuelta no crea otra.
- **SC-002**: Subir o eliminar un documento hace que la siguiente vuelta cree una corrida nueva.
- **SC-003**: «Ver resultado» muestra los mismos hallazgos sin invocar el núcleo.
- **SC-004**: El JSON de estado no contiene hallazgos, huellas ni rutas.

## Clarifications

- [NEEDS CLARIFICATION] Corrida ERROR y botón. Por defecto: no se muestra «Ver resultado» azul; se ofrece «Volver a confrontar» y el worker no reintenta solo (evita bucles con un fallo persistente).
- [NEEDS CLARIFICATION] Borrador subido por un usuario desactivado. Por defecto se registra igual con ese usuario (el FK es `PROTECT`; la cuenta no se borra).
- [NEEDS CLARIFICATION] «Volver a confrontar» manual. Por defecto crea siempre una corrida `MANUAL` nueva aunque ya exista una para las mismas entradas (acción explícita del usuario, como hoy).

## Assumptions

- Sin dependencias nuevas.
- Un solo servidor; varios workers se coordinan con `select_for_update(skip_locked=True)` sobre el borrador.
- El recorrido del worker revisa todos los borradores LISTOS; con corrida vigente la comprobación solo consulta metadatos (sin cargar textos).
