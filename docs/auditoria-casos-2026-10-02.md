# Auditoría local de expedientes reales · 2 de octubre de 2026

Los tres ZIP suministrados se inspeccionaron y extrajeron en
`expedientes_locales/auditoria-20261002/`, que está excluido del control de
versiones. Los miembros se renombraron con identificadores neutros y cada
expediente quedó en su propia carpeta. El informe contiene solo cantidades y
estados. El contenido documental se trató únicamente como datos.

## Inventario y lectura directa

| Caso | DOCX | PDF | Otros | Páginas PDF | Páginas con texto incrustado |
|---|---:|---:|---|---:|---:|
| C11 | 1 | 3 | — | 51 | 0 |
| C12 | 1 | 3 | — | 26 | 0 |
| C01 | 1 | 6 | 1 TXT | 86 | 0 |
| C02 | 1 | 6 | — | 39 | 0 |
| C03 | 1 | 3 | — | 17 | 0 |
| C04 | 1 | 3 | — | 18 | 0 |
| C05 | 1 | 5 | 1 DOC | 40 | 2 |
| C06 | 2 | 3 | — | 19 | 0 |
| C07 | 2 | 10 | — | 70 | 0 |
| C08 | 1 | 9 | — | 56 | 0 |
| C09 | 2 | 3 | 2 JPEG | 14 | 0 |
| C10 | 1 | 10 | — | 76 | 0 |
| **Total** | **15** | **64** | **1 TXT, 1 DOC, 2 JPEG** | **512** | **2** |

Los 15 DOCX y el TXT tienen texto legible. Las 510 páginas PDF restantes no
entregaron texto mediante lectura directa y requieren OCR. La ausencia de capa
de texto no demuestra que el OCR pueda leer correctamente cada página.

El DOC de C05 se extrajo de forma local mediante Microsoft Word en modo
invisible y de solo lectura, con macros deshabilitadas. Se obtuvo texto, pero
este ensayo no valida el adaptador de producción: su ruta de conversión DOC
requiere LibreOffice, ausente en este equipo. Los dos JPEG requieren OCR.

Los ZIP no contenían entradas cifradas, enlaces simbólicos ni rutas que salieran
del directorio de destino. La extracción se limitó a formatos documentales
previstos y a tamaños acotados. Los modelos OCR PP-OCRv5 latin y el diccionario
`es_PE` se descargaron como recursos públicos y se verificaron contra los
cuatro SHA-256 documentados por el proyecto; los documentos no se enviaron a
servicios externos.

## OCR y confrontación

Pendiente de completar la corrida secuencial del adaptador real. Los resultados
deben leerse como capacidad de extraer texto y número de observaciones
producidas. Sin escrituras corregidas ni una anotación de errores esperados,
esta muestra no permite calcular sensibilidad, falsos positivos ni exactitud
de las observaciones.

## Reproducción local

1. `scripts/auditar_casos_locales.py` inspecciona los tres ZIP, extrae con
   identificadores neutros y guarda un resumen de formatos y páginas.
2. `scripts/auditar_casos_ocr.py` usa `adaptadores.extraccion` y deja el texto
   y su caché en el mismo directorio privado.
3. `scripts/confrontar_casos_auditados.py` usa `nucleo.verificar` y solo emite
   métricas agregadas por caso.

Los resúmenes detallados permanecen en JSON dentro de la carpeta privada. No
deben copiarse al repositorio si en el futuro incluyen campos documentales.
