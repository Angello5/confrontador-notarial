# Evidencia F34 · Carga continua (2026-10-03)

Copia local sin Git; datos exclusivamente ficticios.

## Controles locales
- `pytest --cov`: 650 passed, 3 skipped, 13 deselected; cobertura total 93 %.
- `node --test tests/*.test.cjs`: 3 archivos, 19 pruebas, 0 fallos.
- `ruff check .` y `ruff format --check .`: sin hallazgos.
- `manage.py check` y `makemigrations --check --dry-run`: sin incidencias ni migraciones pendientes.
- Entorno: Python 3.12.14 (la versión del proyecto es 3.13; CI la valida) y PostgreSQL de prueba.

## Navegador (base de demostración aparte)
- Tres archivos de roles distintos adjuntados consecutivamente: sin recarga, cada uno una vez y «En cola» (SC-001).
- Confrontar con lectura pendiente: queda solicitada con «Cancelar confrontación»; la solicitud persiste al salir y volver.
- Tras una pasada del worker (`procesar_documentos`), la página abre el resultado sola. Sin errores de consola ni de servidor.

## Pendiente
- Recorrido marca → propuesta → copia DOCX en navegador (cubierto por `tests/test_correccion_expedientes.py`).
- Revisión de seguridad final, PR, CI y Quality Gate en un checkout con Git (T015/T016).
