# Verificación local

Usar el entorno y PostgreSQL descritos en `docs/auditoria-2026-10-02.md`. Modelos OCR locales requeridos.

1. Aplicar migraciones con `python manage.py migrate`.
2. Ejecutar `python -m pytest tests/test_calidad_ocr.py tests/test_calidad_lectura.py -q`.
3. Ejecutar la medición con `python scripts/medir_ocr_sintetico.py --help` para las opciones disponibles; comparar baseline y versión candidata sobre la misma batería.
4. Ejecutar suite ordinaria con cobertura, Ruff y auditoría de dependencias.
5. Subir un ejemplo ficticio de lectura dudosa, confrontar y reabrir: el aviso debe seguir visible.
