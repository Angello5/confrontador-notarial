# Evidencia F34 · Carga continua (2026-10-03)

Copia local sin Git; datos exclusivamente ficticios.

## Controles locales
- `pytest --cov`: 672 passed, 3 skipped, 13 deselected tras fusionar main; cobertura total 93 %.
- `node --test tests/*.test.cjs`: 13 pruebas de carga y vista, 0 fallos.
- `ruff check .` y `ruff format --check .`: sin hallazgos.
- `manage.py check` y `makemigrations --check --dry-run`: sin incidencias ni migraciones pendientes.
- Entorno: Python 3.12.14 (la versión del proyecto es 3.13; CI la valida) y PostgreSQL de prueba.

## Navegador (base de demostración aparte)
- Tres archivos de roles distintos adjuntados consecutivamente: sin recarga, cada uno una vez y «En cola» (SC-001).
- Confrontar con lectura pendiente: queda solicitada con «Cancelar confrontación»; la solicitud persiste al salir y volver.
- Tras una pasada del worker (`procesar_documentos`), la página abre el resultado sola. Sin errores de consola ni de servidor.

- Marca → propuesta en un caso `.docx` ficticio: cada marca abre su observación con valor hallado, esperado y alcance («1 aparición»); la observación lingüística solo informa. Se excluyó una propuesta desde la marca (2 de 3), se confirmó y se descargó un `.docx` corregido distinto. El SHA-256 del original fue idéntico antes y después (FR-011, SC-005).

## Revisión de seguridad (T015)
- Endpoints nuevos (cancelar, vista y páginas) con sesión, rol y visibilidad del expediente; los archivados no son accesibles. Acciones solo por POST con CSRF (también en las peticiones de la cola de carga).
- Respuestas JSON y errores sin rutas, trazas ni texto documental; páginas del borrador con `Cache-Control: no-store` y `nosniff`.
- Las páginas se sirven solo si el SHA-256 del original coincide; los PDF de vista derivados se generan solo al abrir la vista y se borran con la supresión o eliminación (también si llega durante la conversión) y como huérfanos a las 24 h, junto con las carpetas de conversión cortadas (corrección de auditoría 2026-10-04).
- Métricas con números y booleanos únicamente.
- Coherencia: F26 anota que Confrontar reutiliza la corrida vigente; F32 se integra con F34. La constitución 1.8.0 queda fuera del PR.

## Integración
PR desde `feature/f34-carga-continua`, creada sobre main `61d06c9` y fusionada con main al día (#64–#67) sin conflictos: 672 tests de Python y 13 de JavaScript en verde. La barra de avance con porcentaje (experimento previo, sin uso tras F34 y contraria a FR-004) no se incluye.
