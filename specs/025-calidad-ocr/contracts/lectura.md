# Contrato

- `leer(Path) -> str` y `leer_paginas(Path) -> tuple[str,...]` permanecen disponibles.
- `leer_con_calidad(Path) -> {texto: str, calidad: dict}` conserva el mismo separador de página.
- Resultados: sección accesible de calidad de lectura para documentos con advertencias o medición histórica ausente; no incrementa contadores de discrepancias ni crea sustituciones.
- Medición sintética: salida JSON agregada de campos esperados, aciertos y tiempos; las etiquetas reales pendientes no entran en el denominador.
