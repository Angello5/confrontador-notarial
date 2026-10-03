# Contrato

- `leer`, `leer_paginas` y `leer_con_calidad` no cambian de firma ni de separador de página.
- `ocr_informe(fuente, tol=9, reintentar=True)` acepta `Path`, `bytes` o una matriz `numpy` BGR de alto × ancho × 3, y devuelve el mismo informe de F31.
- `calidad_ocr.horizontal(informe) -> float`: proporción entre 0 y 1 de cajas aceptadas más anchas que altas; 0 sin cajas.
- Pantalla, impresión y Word: sin cambios. Una hoja blanca aparece como página con lectura dudosa, igual que hoy.
