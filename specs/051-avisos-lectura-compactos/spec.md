# F68 · Avisos de lectura compactos en el resultado

**Fecha**: 2026-11-02
**Estado**: implementado; cobertura con datos ficticios.
**Alcance**: `templates/expedientes/_calidad_lectura.html`, `_volver_a_subir.html`, `confrontacion.html`, `detalle.html` y `static/css/erp.css`.

## Origen

El usuario pidió reducir «Lectura que necesita revisión» porque ocupaba la parte alta del resultado sin ser lo más relevante. El aviso de versión anterior, justo debajo, ocupaba lo mismo y recibe el mismo trato.

## Comportamiento

- **FR-001**: En la pantalla de resultado, cada aviso es una línea desplegable, cerrada al abrir la página, con su título y el número de documentos. Dentro están las páginas, los archivos y la ayuda «¿Qué significa calidad de lectura?».
- **FR-002**: El informe impreso conserva completo el aviso de lectura (F31 FR-005). El de versión anterior (F50) también se colapsa en la pantalla del kardex, a pedido del usuario.
- **FR-003**: No cambia cómo se calcula ninguno de los dos avisos, ni se convierten en observaciones.

## Seguridad

Sin cambios de permisos ni de datos.

## Verificación

`tests/test_calidad_lectura.py` y `tests/test_confrontacion_automatica.py`: desplegable en el resultado y en el kardex; el aviso de lectura sigue completo en el informe.
