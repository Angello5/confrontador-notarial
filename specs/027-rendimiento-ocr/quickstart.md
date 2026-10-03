# Verificación local

Entorno y PostgreSQL según `docs/auditoria-2026-10-02.md`; modelos OCR locales y LibreOffice en el `PATH`.

1. `python -m pytest tests/test_calidad_ocr.py test_extraer.py -q`: regresiones de F33 en verde.
2. `python scripts/medir_tiempos_ingesta.py --solo casos`: página al revés con ≤ 2 lecturas, página de lado con similitud ≥ 0,99, hoja blanca con 0 lecturas, resto de casos con la misma exactitud que en `docs/ocr-tiempos.json` de F33 previo.
3. Muestra privada antes/después (solo agregados): mismo texto por página y tiempo total menor (SC-001).
4. Suite completa con cobertura, Ruff y `manage.py check`.
