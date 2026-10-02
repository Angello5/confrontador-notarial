# Decisiones

- La auditoría previa leyó 83 archivos; 33 páginas PDF quedaron prácticamente vacías. No se consideran fallos demostrados de OCR.
- El filtro anterior descartaba cajas por inclinación absoluta. La dirección dominante respaldada por varias cajas recuperó los campos sintéticos de páginas inclinadas, conservando el filtro de marca de agua relativa.
- La longitud de la capa PDF no detecta caracteres de sustitución. Añadir examen de calidad antes de omitir OCR.
- La confianza es una señal de revisión y selección de reintentos, no una regla para corregir identidades. La medición privada rechazó los giros activados por una sola caja dudosa con confianza global alta; el algoritmo final conserva el aviso sin girar esas páginas.
- La alternativa girada requiere una mejora de puntuación superior al 10%; si dos lecturas extensas discrepan en sus números, se mantiene una advertencia. La puntuación es una heurística técnica, no una prueba de exactitud.
- La capa PDF se conserva cuando la alternativa recupera menos del 80% de sus caracteres alfanuméricos, o resulta dudosa frente a una capa con al menos 50 caracteres alfanuméricos. Ante una capa más corta, una alternativa dudosa solo la sustituye si recupera más caracteres alfanuméricos; así un escaneo con una capa residual se sigue leyendo, pero un dígito dudoso no reemplaza a uno legible. Los controles inválidos se sustituyen por el marcador de carácter desconocido, sin inferir dígitos.
- Las reglas jurídicas permanecen iguales. Una batería sintética permite medir campos exactos; la precisión real necesita etiquetas humanas.
