# Plan · F31

## Contexto técnico y arquitectura

Python/Django/PostgreSQL; RapidOCR, Pillow y PyMuPDF ya instalados. Añadir `adaptadores/calidad_ocr.py` para interpretar cajas y puntajes y seleccionar lectura; conservar `leer`/`leer_paginas`. Nueva interfaz `leer_con_calidad` y JSON de calidad en `TextoExtraido`, con migración de valor vacío. El servicio acepta también callbacks de texto de las pruebas históricas.

## Constitution Check

Núcleo determinista sin cambios de reglas jurídicas; sin nuevas dependencias ni modelos remotos. Datos privados excluidos. Configuración OCR sujeta a batería sintética antes/después. Permisos y retención de originales sin ampliación. Spec y tareas preceden código. Esta copia sigue sin `.git`: integración por PR, CI en Python 3.13 y gate remoto pendientes; trabajo local autorizado por el usuario.

## Orden

1. Capturar baseline, escribir tests de fallos reproducibles.
2. Reconstrucción de filas con dirección dominante; calidad de capa PDF y reintentos acotados.
3. Invalidación de cachés, metadatos y migración; avisos de lectura independientes de las reglas.
4. Medir, ejecutar regresión, verificar pantalla y documentar límites.

## Complejidad

Un módulo de adaptación, un campo JSON y una migración; no nuevo motor ni infraestructura. Coordenadas referidas a la imagen analizada con giro/escala explícitos; no se promete superposición sobre originales que se eliminan por política.
