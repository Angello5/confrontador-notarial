# Mediciones de OCR sobre expedientes reales

Decisiones tomadas midiendo, para no repetirlas de memoria. Todas las cifras
salen de los 10 expedientes reales de la notaría (75 archivos, 435 páginas),
procesados en local. No se conserva ningún dato personal en este documento.

## Qué modelo se usa hoy y por qué

| Etapa | Modelo | Nota |
|---|---|---|
| Detección (dónde hay texto) | `ch_PP-OCRv4_det_infer.onnx` | no depende del idioma |
| Reconocimiento (qué letras) | `latin_PP-OCRv5_rec_mobile_infer.onnx` | incluye ñ, Ñ y tildes |

El soporte de español vive en el **reconocedor**, y ese ya es PP-OCRv5 desde
F3. El detector solo localiza recuadros de texto; por eso el fabricante lo
publica como `ch_` sin variantes por idioma.

## Detector PP-OCRv5 frente al v4 actual

Sobre los 46 recaudos de `Sin_Block_Notas_Intencionados` (300 páginas), con
el mismo reconocedor y la misma tubería de F11:

| | v4 mobile (actual) | v5 mobile | v5 server |
|---|---|---|---|
| Tiempo, 300 páginas | 817 s | **700 s** | ≈ 3× más lento (medido en 3 pág.) |
| Caracteres leídos | 438 620 | 437 995 | — |
| Personas detectadas | 129 | 122 | — |
| Con documento | 83 | **87** | — |
| **Completas** (nombre + documento) | 46 | **50** | — |

El v5 mobile produce **menos fragmentos y más pares completos**, que es lo que
la confrontación necesita, y es un 14% más rápido. El v5 server no aportó nada
a cambio de triplicar el tiempo.

Reserva: estas cifras no saben si lo leído es correcto. Más pares completos
también podría ser más pares mal unidos. Solo el banco de casos con respuesta
conocida (expediente 72136) puede descartarlo.

Modelos verificados contra el sha256 que publica rapidocr:

```
ch_PP-OCRv5_mobile_det.onnx  4.8 MB  4d97c44a20d30a81aad087d6a396b08f786c4635742afc391f6621f5c6ae78ae
ch_PP-OCRv5_server_det.onnx 88.1 MB  0f8846b1d4bba223a2a2f9d9b44022fbc22cc019051a602b41a7fda9667e4cad
```

Decisión: **pendiente del propietario**. Los datos respaldan el cambio a v5
mobile; el coste es reprocesar el OCR guardado (la caché se invalida sola,
porque los modelos forman parte de su llave) y actualizar el aprovisionamiento
del CI.

## LiteParse frente a RapidOCR

Sobre `Recaudo.pdf` del expediente 72136 (8 páginas), extraído página a
página en los dos casos y pasado por la misma tubería:

| | LiteParse | RapidOCR (actual) |
|---|---|---|
| Tiempo | **17 s** | 27 s |
| Caracteres | **23 215** | 15 027 |
| Personas detectadas | 4 | **6** |
| Con documento | 1 | **3** |
| Completas | 1 | 1 |
| Tipos de página reconocidos | pierde RENIEC e IDENTIDAD | todos |

LiteParse lee más texto y más rápido, pero **no conserva la disposición en
columnas**. `ocr_lineas()` reconstruye filas por coordenadas y separa columnas
con dos espacios, que es lo que permite leer `Apellido Paterno: <valor>` en un
formulario a dos columnas. Sin eso, etiquetas y valores se mezclan y el
clasificador no reconoce el documento.

Además, LiteParse como bloque único (sin páginas) se clasifica entero como
SISGEN y se descarta: la segmentación por páginas de F11 es imprescindible para
cualquier motor.

Decisión: **se mantiene RapidOCR**. LiteParse sería mejor para prosa corrida;
peor para extraer campos de formularios.

## Códigos QR como fuente exacta del documento

La ficha de autenticación biométrica de RENIEC lleva un QR con
`nuDni=<8 dígitos>`: el documento del ciudadano, exacto, sin OCR de por medio.

Cobertura sobre las 435 páginas, según el lector:

| Lector | Páginas con QR | Con `nuDni` |
|---|---|---|
| OpenCV `QRCodeDetector` | 3 | 2 |
| zxing-cpp | **85** | **16** |

El lector de OpenCV detecta 28 veces menos códigos, y **empeora al subir la
resolución** (2/3 a 200 ppp, 0/3 a 400 y 600). La primera medición, hecha con
él, habría llevado a descartar la idea por error.

Con zxing-cpp: casi una de cada cinco páginas trae QR, pero solo 16 traen el
documento. El resto son códigos de trámite de SUNARP y de verificación.

Decisión: el QR sirve **como confirmación de máxima confianza cuando aparece**,
no como cimiento. El peso lo lleva el anclaje por plantilla: reconocer el
documento y leer sus campos por posición. Orden de confianza:

1. Código QR con `nuDni`: exacto.
2. Campo etiquetado dentro de una plantilla reconocida: alto.
3. Expresión regular sobre texto libre: bajo; es lo que mezclaba al operador
   y al notario con los comparecientes.

`zxing-cpp` no está en el ERP: es una dependencia nueva y su incorporación
requiere justificarla en la fase que la use.

## Resolución de las fichas RENIEC y biométricas

Medido el 2026-09-27 sobre las 55 fichas oficiales de los 10 expedientes (28 RENIEC, 27 biométricas), con el mismo OCR y el mismo núcleo, cambiando solo los puntos por pulgada al rasterizar. Solo recuentos.

| Medida | 150 | **200 (actual)** | 250 | 300 | 400 |
|---|---:|---:|---:|---:|---:|
| Fichas con persona completa | 44 | **49** | 44 | 45 | 41 |
| RENIEC con estado civil | 19 | **23** | 18 | 19 | 17 |
| RENIEC con fecha de nacimiento | 16 | **21** | 16 | 17 | 15 |
| RENIEC con domicilio | 16 | **18** | 18 | 18 | 16 |
| DNI con 2+ fichas y nombres idénticos | 15 | **15** | 12 | 10 | 10 |
| Segundos por página | 1,9 | ≈2 | 2,2 | 2,4 | 2,8 |

**Decisión:** se mantiene 200 ppp. Subir o bajar la resolución empeora la lectura: los modelos PP-OCR están ajustados a ese tamaño de letra y a más resolución el detector parte o pierde líneas. Mejorar la calidad pasa por el origen del documento (consulta RENIEC guardada como PDF digital, con capa de texto) y no por la resolución.

## Lecciones de método

Dos veces se estuvo a punto de concluir en falso por medir con un instrumento
roto:

- Verificar el arreglo de columnas con texto ya normalizado, que había perdido
  justamente las columnas.
- Medir la viabilidad del QR con un lector que detecta uno de cada veintiocho.

Un resultado limpio no significa nada si el instrumento está roto. Antes de
concluir, comprobar el instrumento contra un caso cuyo resultado se conoce.
