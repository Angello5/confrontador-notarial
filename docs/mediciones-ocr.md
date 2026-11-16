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

## Vías de velocidad · 2026-11-16

Medido sobre los escaneos de la muestra privada (70 PDF, 546 páginas), en un
portátil Intel i7-1360P (núcleos mezclados, 16 hilos) y Python 3.14. Solo
tiempos y recuentos. El servidor de la notaría (Xeon Bronze 3204, 6 núcleos sin
Hyper-Threading) dará cifras distintas: estas son indicativas.

Qué se sube: 544 de 546 páginas son escaneos sin texto digital, cada una una
sola imagen incrustada, casi todas a 200 ppp (418) y el resto entre 275 y 300.

| Vía | Resultado | Decisión |
|---|---|---|
| OpenVINO como motor de ejecución, varios procesos | 58 a 69 páginas/min en cuatro mediciones (3×2, 6×1, 4×4 y 2×3 procesos × hilos) | **Adoptar** tras medir en el servidor (F76) |
| OpenVINO, un proceso | 12 a 30 páginas/min con hilos por defecto; 52 con 4 hilos | Parte de lo anterior |
| ONNX Runtime (actual), varios procesos | 9 a 33 páginas/min; la misma variante (3×2) dio 33 y 15 en rondas seguidas | Solo si se rechaza OpenVINO |
| ONNX Runtime, un proceso (como hoy) | 8 a 21 páginas/min según la ronda | Línea base |
| Caché por página | 14 de 544 páginas repetidas (2,6 %), ninguna entre expedientes | **Descartar** |
| Clasificador de orientación | De 80 páginas, 74 se leen una vez, 5 dos veces y 1 cuatro; solo 1 venía girada. Las relecturas son el 16 % del tiempo | **Descartar**: ahorraría cerca del 5 % |

Texto: idéntico en las 18 páginas comparadas (28 902 caracteres, ninguno
distinto) en todas las variantes, con los mismos modelos y la misma resolución.

Reservas:

- 18 páginas por variante y un equipo cuyas cifras con ONNX Runtime varían
  mucho entre rondas. Las de OpenVINO fueron estables.
- Se comparó el texto, no las confianzas: falta comprobar que los avisos de
  calidad no cambian.
- Se midió el motor directamente, sin las relecturas por giro ni por marca de
  agua, y no se midió la memoria con OpenVINO.
- Con varios procesos y los hilos por defecto, cada página tardó 37 s dentro de
  su proceso: sin fijar los hilos, los procesos se estorban.

Flujo completo, ya implementado (`scripts/medir_lectura_paralela.py`, 75
páginas de la muestra, relecturas incluidas): 13,9 páginas/min con el motor
actual en serie; 17,0 con OpenVINO y 3 procesos de 1 hilo (6,4 GB); 10,7 con el
motor actual en 3 procesos. Los avisos de calidad coinciden en las 75 páginas,
pero **el texto de 1 página cambia con OpenVINO: 2 letras de una línea**, ningún
dígito. La medición directa del motor, sobre 18 páginas, no lo había visto. Por
eso la lectura rápida queda apagada por defecto hasta medir en el servidor y
decidir sobre esa diferencia.

Decisión: **del propietario, 2026-11-16: adoptar OpenVINO**, dimensionado para
el servidor y validado midiendo en él. Alcance en `specs/057-lectura-paralela/`.

## Lecciones de método

Dos veces se estuvo a punto de concluir en falso por medir con un instrumento
roto:

- Verificar el arreglo de columnas con texto ya normalizado, que había perdido
  justamente las columnas.
- Medir la viabilidad del QR con un lector que detecta uno de cada veintiocho.

Un resultado limpio no significa nada si el instrumento está roto. Antes de
concluir, comprobar el instrumento contra un caso cuyo resultado se conoce.
