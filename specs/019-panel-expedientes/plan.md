# Implementation Plan: F25 · Panel de expedientes: abrir, editar y eliminar

**Branch**: `Angello5/panel-de-expedientes-abrir-editar-eliminar-f25-panel-expedientes` | **Date**: 2026-09-28 | **Sources**: [spec.md](spec.md)

## Summary and scope

- `expedientes/models.py`: `archivado_el`, `archivado_por` (nulos) + migración `0005`.
- `expedientes/services.py`: `expedientes_visibles()` excluye archivados (lista, inicio y métricas pasan por ahí); las vistas del expediente buscan solo no archivados (404).
- `expedientes/views.py`: `expediente_editar`, `expediente_eliminar` (GET confirma, POST archiva), `expediente_restaurar` (POST, Administrador); filtro `?archivados=1` en la lista.
- Plantillas: botones en `lista.html` y `detalle.html`; nuevas `editar.html` y `eliminar.html`.

## Contrato

```text
GET/POST /expedientes/<pk>/editar/     ExpedienteForm(instance=…)
GET/POST /expedientes/<pk>/eliminar/   confirma con el código / archiva
POST     /expedientes/<pk>/restaurar/  solo Administrador
GET      /expedientes/?archivados=1    solo Administrador: lista de archivados
```

## Constitution Check

| Principio | Comprobación |
|---|---|
| I. Determinismo | Sin cambios en el núcleo. |
| II. Núcleo puro | Solo vistas, servicio de visibilidad y plantillas. |
| III. Tests primero | Pruebas rojas de permisos, CSRF, unicidad, archivado y restauración. |
| IV. Privacidad | Nada se borra; la supresión sigue en el comando legal. |
| V. Simplicidad | Dos campos, tres vistas, sin dependencias. |
| VI. Seguridad | Mismos permisos; POST con CSRF; restaurar solo Administrador. |
| VII. DevSecOps | Suite, Ruff, `check`, `makemigrations --check`, `git diff --check`. |

## Complexity Tracking

Ninguna violación.
