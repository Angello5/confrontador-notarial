# Feature Specification: F28 · Código reutilizable tras archivar y nombre de la notaría configurable

**Feature Branch**: `Angello5/f28-codigo-marca`

**Created**: 2026-09-28

**Status**: Draft

**Input**: (1) Bug del propietario: tras «Eliminar» (archivado lógico, F25) no puede volver a crear un expediente con el mismo kardex porque `Expediente.codigo` es `unique=True` también para los archivados. (2) La barra lateral y el ingreso muestran fijo «CN · CONFRONTADOR / ERP NOTARIAL»; el propietario quiere el nombre de su notaría.

## Principio

**El código identifica al expediente vivo; el nombre de la notaría es configuración, no código.** Un archivado conserva su código y su manifiesto, pero no bloquea un expediente nuevo. El nombre real nunca se escribe en el repositorio.

## Requirements *(mandatory)*

- **FR-001 (unicidad)** Decisión del propietario (2026-09-28): el código es único **solo entre expedientes activos** (`archivado_el` nulo). `unique=True` se sustituye por `UniqueConstraint(fields=("codigo",), condition=Q(archivado_el__isnull=True), name="expediente_codigo_activo_unico")` (migración `0007`).
- **FR-002 (crear/editar)**: `ExpedienteForm` valida la unicidad solo contra activos. Si ya existe un activo con ese código: «Ya existe un expediente activo con ese código. Ingrese otro código.» Con el código de un archivado se crea un expediente nuevo.
- **FR-003 (restaurar)**: Restaurar un archivado cuyo código ya usa un activo no cambia nada y muestra: «No se puede restaurar: ya existe un expediente activo con el código X. Cambie o elimine ese expediente primero.» Vuelve a la lista de archivados. Nunca un `IntegrityError` sin capturar.
- **FR-004 (historiales)**: Cada expediente conserva su propio manifiesto (`Corrida`, `DecisionCorreccion` por clave foránea); el nuevo expediente con el mismo código empieza con historial vacío.
- **FR-005 (marca)**: `settings.ERP_NOMBRE` se lee de la variable de entorno `ERP_NOMBRE` (por defecto «ERP Notarial»). Un context processor expone `erp_nombre` y `erp_iniciales` (iniciales en mayúsculas de las dos primeras palabras: «Notaria Ficticia» → «NF»; una sola palabra → una inicial).
- **FR-006 (plantillas)**: `base.html` y `login.html` muestran el sello `erp_iniciales`, el nombre `erp_nombre` y el subtítulo «ERP». Los `<title>` que decían «ERP Notarial» usan `erp_nombre`.
- **FR-007**: Sin dependencias nuevas ni IA. Tests con datos ficticios y nombre ficticio vía `override_settings`. La variable se documenta en `specs/001-base-devsecops/quickstart.md`.

## Success Criteria *(mandatory)*

- **SC-001**: El propietario elimina un expediente y crea otro con el mismo kardex sin error.
- **SC-002**: Con `ERP_NOMBRE` configurado, ninguna pantalla muestra «CONFRONTADOR».

## Assumptions

- [NEEDS CLARIFICATION] Varios archivados pueden compartir código (la restricción solo mira activos). Por defecto: permitido.
- [NEEDS CLARIFICATION] Las iniciales ignoran palabras de enlace («de», «la»)? Por defecto: no; se toman las dos primeras palabras tal cual.
