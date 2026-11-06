# F71 · Lista de observaciones sin fragmento y pruebas aisladas

**Fecha**: 2026-11-03
**Estado**: implementado; cobertura con datos ficticios.
**Alcance**: `templates/expedientes/confrontacion.html`, `_obs_correccion.html`, `static/css/erp.css` y `tests/settings.py`.

## Origen

- El usuario pidió eliminar de la lista el fragmento del borrador que aparecía bajo cada observación.
- Las pruebas usaban la carpeta real de originales y la temporal. Sus kardex tienen los mismos números que los reales y, en un equipo con datos, una corrida borró un original real.

## Comportamiento

- **FR-001**: La lista de observaciones ya no muestra el fragmento. Cada observación conserva su línea, lo que dice y lo que debe decir. Sin vista del documento (mientras se prepara o en borradores que no son `.docx`), esa es la referencia.
- **FR-002**: El informe impreso conserva línea y fragmento.
- **FR-003**: Una corrección sin conteo de apariciones (confrontación hecha sin el original) no muestra texto a medias. Al aplicarla se vuelve a contar.
- **FR-004**: `tests/settings.py` usa carpetas temporales propias para `EXPEDIENTES_ORIGINALES_DIR` y `EXPEDIENTES_TEMP_DIR`. Una prueba falla si vuelven a ser las reales.

## Seguridad

FR-004 protege los originales conservados (Anexo A.3) de las corridas de pruebas. Sin cambios de permisos.

## Verificación

- `tests/test_correccion_expedientes.py`: sin fragmento en pantalla, con él en el informe.
- `tests/test_preview_y_marca.py`: las pruebas no usan la carpeta real. Medido en local: la carpeta real queda idéntica tras la suite completa.
