# Tiempos de ingesta y OCR · 2 de octubre de 2026

Análisis de cuánto tarda el ERP en leer cada tipo de documento que entrega el
cliente y qué se puede acelerar sin perder exactitud. Las secciones siguientes
describen el estado previo; las mejoras 1, 2, 3 (solo hojas totalmente blancas)
y 5 se aplicaron en F33 y su resultado está en «Resultado de F33».

## Resumen

- Un documento con texto propio (DOCX, TXT o PDF en el que se puede seleccionar
  el texto) se lee en menos de 0,05 s. **El coste está en los escaneos**: entre
  4,5 s (mediana) y 8,7 s (percentil 90) por página real, y hasta 24 s cuando la
  página viene girada.
- En la auditoría, 510 de 512 páginas PDF eran escaneos sin texto. Un
  expediente de 14 a 86 páginas tarda hoy de **1 a 6,5 minutos** solo en OCR
  (estimado con la mediana por página).
- Más del 80 % del tiempo de una página es el motor (detectar 24 %, reconocer 58 %
  de las ~65 líneas). Los ajustes finos del motor dan poco; lo que más rinde es
  **no repetir trabajo** y **procesar en paralelo**.

| Mejora | Ahorro medido | Exactitud | Esfuerzo |
|---|---|---|---|
| Activar la reserva de memoria de ONNX Runtime y no pasar por PNG | −18 % en páginas reales | Texto idéntico | Bajo |
| Corregir los reintentos de páginas giradas | −50 % en página al revés; corrige el orden en página de lado | Mejora | Bajo |
| Detectar página en blanco antes del OCR | −1 a −2 s por página en blanco | Igual | Bajo |
| Dos procesos de extracción en paralelo | +22 % de páginas por minuto | Igual | Bajo (requiere ajustar el tiempo límite) |
| Perfil fijo de LibreOffice para `.doc`/`.rtf` | −51 % (6,7 → 3,3 s) | Igual | Bajo |
| Bajar resolución a 170 o 150 dpi | −5 a −13 % | **Cambia campos**: descartado | — |
| Hilos, lote de reconocimiento, lado máximo 1600 | Dentro del ruido | Igual | Descartado |

## Cómo se procesa hoy

El usuario sube el archivo y la petición termina; el comando
`procesar_documentos` toma los pendientes **de uno en uno** y lee sus páginas
**en serie**. Por cada página de PDF:

1. Si trae capa de texto válida, se usa directamente.
2. Si no (escaneo) o la capa es dudosa, se rasteriza a 200 dpi, se codifica a
   PNG y pasa por RapidOCR (detección + reconocimiento, modelos PP-OCRv5 en CPU).
3. Si la lectura es escasa o de baja confianza, se reintenta girando 180°, 90°
   y 270°: hasta 4 lecturas.

El resultado se guarda por hash del archivo; volver a subir el mismo archivo es
instantáneo.

## Tiempos por tipo de ingesta (de mejor a peor)

Documentos ficticios generados por `scripts/medir_tiempos_ingesta.py`, caché
vacía, mediana de 2 repeticiones, equipo enchufado. Exactitud contra el texto
conocido de cada documento.

| Caso | Tiempo | Lecturas OCR | Exactitud |
|---|---:|---:|---|
| TXT | < 0,01 s | 0 | 14/14 campos |
| DOCX | < 0,01 s | 0 | 14/14 |
| PDF con texto, 10 páginas | 0,02 s (0,002 s/pág.) | 0 | 140/140 |
| PDF con texto, 1 página | 0,01 s | 0 | 14/14 |
| Página en blanco escaneada | 2,4 s | 1 | — (marcada para revisión) |
| PDF escaneado limpio, 10 páginas | 59,8 s (6,0 s/pág.) | 10 | 137/140 |
| PDF escaneado limpio, 1 página | 5,9 s | 1 | 14/14 |
| Escaneo de bajo contraste | 6,2 s | 1 | 14/14 |
| Escaneo inclinado 4° | 6,6 s | 1 | 14/14 |
| `.rtf`/`.doc` vía LibreOffice | 6,9 s | 0 | 14/14 |
| Capa de texto corrupta | 7,0 s | 1 | 14/14 |
| Foto JPEG de 12 MP | 7,1 s | 1 | 14/14 |
| Página al revés (180°) | 21,4 s | 4 | 14/14, aviso falso de lecturas divergentes |
| Página de lado (90°) | 24,4 s | 4 | 14/14, **líneas desordenadas** (33 % de similitud) |

Las páginas reales son más densas que las ficticias (~65 líneas frente a 42).

## Páginas reales (muestra privada)

Página central de cada uno de los 12 expedientes auditados. Solo se publican
tiempos agregados; textos y campos quedan en `expedientes_locales/`. No hay
etiquetas humanas: la exactitud de cada variante se compara contra la lectura
actual, no contra la verdad.

| Variante | Mediana/pág. | P90/pág. | Total 12 pág. | Igual a la lectura actual |
|---|---:|---:|---:|---|
| Actual | 4,53 s | 8,73 s | 56,2 s | — |
| Sin PNG | 4,49 s | 8,78 s | 55,1 s | Sí (12/12 campos) |
| Reserva de memoria (arena) | 3,72 s | 7,24 s | 49,0 s | Sí |
| **Arena + sin PNG** | **3,72 s** | **7,08 s** | **46,3 s (−18 %)** | **Sí** |

Reparto de la variante actual por página: rasterizar y codificar 0,35 s,
detectar 1,09 s, reconocer 2,63 s.

En una ronda anterior (7 variantes cargadas a la vez):

- 170 dpi y 150 dpi conservaron solo 9 de 12 campos y produjeron 3 y 5 campos
  distintos. Sin etiquetas no se sabe cuál es correcto, pero cambiar la lectura
  real sin validarla no es aceptable: se descarta.
- Lote de reconocimiento 16, 8 hilos y lado máximo 1600 no mejoraron la mediana.

Paralelismo sobre las mismas 12 páginas:

| Procesos × hilos | s/página | Rendimiento |
|---|---:|---:|
| 1 × todos | 5,26 | base |
| 2 × 8 | 4,10 | +22 % |
| 4 × 4 | 4,06 | +23 % |

ONNX Runtime ya usa todos los núcleos dentro de una página; más de dos procesos
no aporta en este portátil (4 núcleos de alto rendimiento y 8 de eficiencia). En
un servidor con más núcleos físicos el beneficio puede ser mayor.

## Hallazgos

### 1. Errores en los reintentos (precisión y tiempo)

En `adaptadores/extraccion.py`, `ocr_informe`:

- **Página al revés.** Si la primera lectura sale vacía, cualquier alternativa
  se marca como `lecturas_divergentes`, porque sus números «difieren» de una
  lectura vacía. El bucle no se detiene en el primer giro correcto: hace 4
  lecturas en vez de 2 y deja un aviso de revisión falso.
- **Página de lado.** El primer giro probado (180°) deja el texto vertical;
  RapidOCR reconoce igualmente cada línea, así que gana con la misma puntuación
  que el giro correcto. El texto sale con las líneas desordenadas, lo que puede
  romper la asociación nombre–DNI–monto, que se hace por línea.

Prototipo medido (no aplicado): tratar `sin_texto` como `lectura_escasa` en la
comparación de números y desempatar a favor de cajas horizontales.

| Caso | Hoy | Prototipo |
|---|---|---|
| Página al revés | 20,6 s, 4 lecturas, aviso falso | 10,3 s, 2 lecturas, sin aviso |
| Página de lado | 19,5 s, 33 % de similitud | 19,3 s, 100 % de similitud |
| Página en blanco | 2,2 s, 1 lectura | 1,2 s, 0 lecturas |
| Escaneo normal / inclinado | sin cambio | sin cambio |

En la muestra real ninguna página necesitó reintentos; el ahorro se concentra
en lotes con hojas giradas, pero la corrección del orden afecta a la exactitud.

### 2. Página en blanco

El filtro de hoja casi vacía solo se aplica después de una lectura fallida.
Aplicado antes evita el OCR: 33 de las 512 páginas reales estaban
prácticamente vacías.

### 3. Conversión a PNG

Cada página se rasteriza, se comprime a PNG y RapidOCR la descomprime. En
escaneos con ruido cuesta hasta 1,2 s por página (ficticias). En las reales,
0,28 s. Pasar la imagen en memoria lo elimina sin cambiar el texto.

### 4. Reserva de memoria de ONNX Runtime

RapidOCR la desactiva por defecto (`enable_cpu_mem_arena: false`). El
reconocimiento procesa líneas de anchos distintos y, sin reserva, pide y libera
memoria en cada lote. Activarla bajó la mediana real un 18 % con texto idéntico.

### 5. Un solo proceso de extracción

El comando ya admite varios consumidores (`select_for_update(skip_locked=True)`):
lanzar dos procesos no requiere código. **Riesgo**: con dos procesos, un
documento que tarde más de `EXPEDIENTES_PROCESSING_TIMEOUT` (15 min: entre 100 y
200 páginas según la densidad) vuelve a la cola y otro proceso lo repite.
Conviene subir el límite o renovar `procesando_el` por página antes de
activarlo. Con un solo proceso este riesgo no existe.

### 6. LibreOffice

Cada conversión crea un perfil temporal nuevo: 6,7 s. Con un perfil fijo por
proceso, 3,3 s. Debe ser uno por proceso, porque LibreOffice bloquea su perfil.

### 7. Arranque

Django arranca en 0,55 s y los modelos cargan en ~1 s por proceso. Si
`worker.sh` (fuera del repositorio) relanza el comando en bucle, cada vuelta
paga ese coste más la pausa entre vueltas. Revisar ese script.

## Propuestas que necesitan decisión

- **[NEEDS CLARIFICATION]** Prioridad de procesamiento: leer primero minuta y
  borrador para que la confrontación empiece antes. Cambia el orden de la cola.
- **[NEEDS CLARIFICATION]** Progreso visible por página («página 12 de 40») y
  tiempo estimado. No acelera, pero reduce la espera percibida; requiere guardar
  avance por página.
- **Motor OpenVINO** (RapidOCR lo soporta) suele ser más rápido en CPU Intel,
  pero añade una dependencia de ~50 MB y no se ha medido. Requiere aprobar su
  instalación.
- Clasificador de orientación de RapidOCR: evitaría probar giros a ciegas, pero
  añade un modelo nuevo que habría que aprovisionar y fijar por hash.

## Resultado de F33 · 3 de octubre de 2026

Aplicadas: reserva de memoria y entrada sin PNG (1), corrección de reintentos
(2), hoja totalmente blanca sin OCR con umbral 0,001 % (3) y perfil de
LibreOffice por proceso (5). Spec en `specs/027-rendimiento-ocr/`. Medición
antes/después alternando ambos extractores página a página, equipo enchufado.

| Conjunto | Texto idéntico | Antes | Después | Ahorro |
|---|---|---:|---:|---:|
| 12 páginas reales (2 rondas, mediana) | 12/12 | 52,5 s | 41,9 s | −20 % |
| 7 páginas ficticias normales | 7/7 | 6,2 s/pág. | 3,7 s/pág. | −40 % |
| Página al revés | sí | 21,4 s, 4 lecturas | 7,6 s, 2 lecturas, sin aviso falso | −64 % |
| Página de lado | no: ahora en orden (similitud 0,33 → 1,0) | 20,3 s | 15,2 s | −25 % |
| Hoja en blanco | sí | 2,2 s | 0,09 s | −96 % |
| `.rtf` vía LibreOffice, 2.ª conversión del proceso | sí | 10,2 s | 4,9 s | −52 % |

La página de lado sigue necesitando 4 lecturas y queda marcada para revisión:
la lectura vertical y la correcta tienen los mismos números en distinto orden.
La primera conversión de LibreOffice de cada proceso cuesta lo mismo que antes.
Casos completos con el extractor nuevo en `ocr-tiempos-f33.json`.

Memoria: la reserva de ONNX Runtime eleva el pico del proceso de extracción de
1,0 a 1,7 GB y la memoria retenida tras 6 páginas de 0,6 a 1,6 GB (medido en
Windows). Con dos procesos en paralelo superaría 3 GB: comprobar la RAM del
servidor en F8 antes de activar la reserva o el paralelismo.

## Límites

- Portátil Intel i7-1360P (12 núcleos, 16 hilos), Windows, Python 3.12. El
  servidor de la notaría puede dar cifras distintas: repetir la medición allí.
- El equipo trabajó parte del tiempo con batería; las variantes se intercalan
  en orden aleatorio por página para que eso no favorezca a ninguna, pero los
  valores absolutos varían entre rondas (la misma variante midió 4,5 y 9,1 s por
  página en dos rondas distintas).
- 12 páginas reales y documentos ficticios simples; los ahorros son
  indicativos, no garantizados.
- La exactitud real sigue sin etiquetas validadas por la notaría.

## Reproducción

```powershell
.venv/Scripts/python.exe scripts/medir_tiempos_ingesta.py --solo casos --repeticiones 2
.venv/Scripts/python.exe scripts/medir_tiempos_ingesta.py --solo variantes
.venv/Scripts/python.exe scripts/medir_tiempos_ingesta.py --solo paralelo
.venv/Scripts/python.exe scripts/medir_tiempos_ingesta.py --privado
```

Los tres primeros escriben `docs/ocr-tiempos.json` con datos ficticios. El
último requiere el corpus local y solo escribe agregados en
`expedientes_locales/auditoria-20261002/tiempos/`. LibreOffice debe estar en el
`PATH` para el caso `.rtf`.
