# Feature Specification: F25 · Panel de expedientes: abrir, editar y eliminar

**Feature Branch**: `Angello5/panel-de-expedientes-abrir-editar-eliminar-f25-panel-expedientes`

**Created**: 2026-09-28

**Status**: Draft

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
- Archivar no cambia el código: un código archivado sigue ocupado (unicidad global).
