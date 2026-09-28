# Implementation Plan: F28 · Código reutilizable tras archivar y marca configurable

**Branch**: `Angello5/f28-codigo-marca` | **Date**: 2026-09-28 | **Sources**: [spec.md](spec.md)

## Summary and scope

- `expedientes/models.py`: `UniqueConstraint` condicional; migración `0007`.
- `expedientes/forms.py`: el filtro de unicidad añade `archivado_el__isnull=True`.
- `expedientes/views.py`: mensajes de unicidad y restaurar con comprobación previa + `IntegrityError` capturado.
- `config/settings.py`: `ERP_NOMBRE` y el context processor `core.context_processors.marca`.
- Plantillas `base.html`, `login.html` y los `<title>` con «ERP Notarial».

## Constitution Check

| Principio | Comprobación |
|---|---|
| I. Determinismo | Sin cambios en el núcleo. |
| III. Tests primero | Pruebas rojas ficticias antes de la implementación. |
| IV. Privacidad | El nombre real vive solo en el entorno del servidor. |
| V. Simplicidad | Restricción nativa de PostgreSQL; context processor de pocas líneas. |
| VII. DevSecOps | Suite, Ruff, `check`, `makemigrations --check`, `git diff --check`. |

## Complexity Tracking

Ninguna violación.
