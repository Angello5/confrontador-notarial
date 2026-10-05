# F36 · Interfaz con lenguaje notarial

**Fecha**: 2026-10-05  
**Estado**: implementado en plantillas, mensajes y estilos; cobertura con las pruebas de interfaz existentes.  
**Alcance**: `templates/`, `static/css/erp.css`, `static/js/reporte-docx.js`, mensajes de `expedientes/` y la etiqueta del rol `CLIENTE`.

## Origen

El usuario pidió el 2026-10-05:

- usar «Kardex» en lugar de «Expedientes»;
- poner el nombre y el logo de la notaría, con el nombre más grande;
- poner «Confrontador Notarial» como subtítulo;
- agrandar un poco la letra;
- usar en general el lenguaje técnico de un abogado.

## Comportamiento implementado

- **Marca**:
  - El subtítulo de la barra lateral y del ingreso dice «Confrontador Notarial», con logo o sin él.
  - El logo ocupa el ancho útil de la barra (212 px).
  - El nombre sin logo pasa de 17 a 21 px.
  - El nombre y el logo reales siguen fuera del repositorio: se configuran con `ERP_NOMBRE` y `ERP_LOGO` (F28, F29).
- **Tamaño de letra**: el texto base pasa de 15 a 16 px, el menú lateral de 15 a 16 px y los títulos de sección del menú de 11 a 12 px.
- **Glosario aplicado en la interfaz**:

| Antes | Ahora |
|---|---|
| Expediente(s) | Kardex (invariable en plural) |
| Código del expediente | Número de kardex / N.° de kardex |
| Fuentes, documentos del cliente | Recaudos |
| Valor (o documento) hallado / esperado | Dice / Debe decir |
| Corrida | Confrontación |
| Reporte | Informe |
| Hallazgos | Observaciones |

  El glosario se aplica a:
  - las plantillas;
  - los mensajes de las vistas y formularios;
  - el informe Word y el CSV.

- **Etiqueta del rol `CLIENTE`**: pasa a ser «Recaudos». La migración `0010_rol_recaudos` solo cambia la etiqueta y no altera datos.
- **Sin cambios internos**: las URL (`/expedientes/`), los modelos, los nombres de variables, los eventos y las clases CSS no cambian, para no romper enlaces ni el historial.

## Límites

- Los textos de auditoría y los mensajes técnicos del registro (catálogo de reglas, versión del extractor) siguen igual.
- Las observaciones del núcleo conservan su formato («debe decir»).

## Verificación

Las pruebas de interfaz existentes se actualizaron al nuevo texto:

- `test_expedientes_ui.py`
- `test_shell.py`
- `test_codigo_y_marca.py`
- `test_panel_expedientes.py`
- `test_expedientes_upload.py`
- `test_expedientes_confrontacion.py`

`makemigrations --check` no detecta cambios pendientes.
