# Plan · F33

**Branch**: `feature/f33-rendimiento-ocr` | **Spec**: [spec.md](spec.md)

## Contexto técnico

Python 3.13 (CI) / 3.12 (local), RapidOCR 3.9 sobre ONNX Runtime 1.30, PyMuPDF, Pillow y NumPy, todos ya instalados. Todo el cambio vive en el adaptador `adaptadores/extraccion.py` y en `adaptadores/calidad_ocr.py`; el núcleo, los modelos de datos, las vistas y las plantillas no cambian.

| Cambio | Dónde | Requisito |
|---|---|---|
| `enable_cpu_mem_arena: true` al crear el motor | `extraccion._ocr` | FR-001 |
| Página PDF rasterizada como matriz BGR, sin PNG; los giros también se pasan como matriz | `extraccion._pdf_informe`, `ocr_informe` | FR-001, FR-002 |
| Hoja totalmente blanca (≤ 0,001 % de píxeles < 200) se resuelve sin OCR | `ocr_informe` | FR-006 |
| Lectura vacía o escasa no produce `lecturas_divergentes` | `ocr_informe` | FR-003 |
| Proporción de cajas horizontales; desempate y criterio de parada | `calidad_ocr.horizontal`, `ocr_informe` | FR-004, FR-005 |
| Perfil de LibreOffice por proceso bajo `CACHE`, descartado si falla y al salir | `extraccion._soffice` | FR-007 |
| `calidad_ocr.VERSION` 2 → 3 | `calidad_ocr` | FR-008 |

## Constitution Check

- **I. Determinismo**: misma entrada, misma salida; la versión del extractor sube porque cambian páginas giradas y blancas. Sin IA. ✅
- **II. Núcleo puro**: solo cambia el adaptador de extracción. ✅
- **III. Pruebas primero**: cada cambio empieza con una prueba ficticia que falla en `tests/test_calidad_ocr.py` o `test_extraer.py`. ✅
- **IV. Privacidad**: el perfil de LibreOffice no guarda contenido ni nombres de documentos (comprobado en research.md) y vive junto a la caché OCR existente; no se conserva ningún archivo nuevo de expediente. La muestra real solo produce agregados en `expedientes_locales/`. ✅
- **VII. DevSecOps**: sin dependencias nuevas; Ruff, cobertura y Quality Gate. ✅

Sin violaciones; no hay tabla de complejidad.

## Orden

1. Pruebas que fallan para FR-001 a FR-008 con motores falsos y documentos ficticios.
2. Motor con reserva de memoria y entrada en memoria; regresión de texto idéntico.
3. Reintentos (vacía, horizontales, parada) y hoja blanca.
4. Perfil de LibreOffice reutilizado.
5. Versión, suite completa, medición antes/después (ficticia y privada) y documentación.

## Re-evaluación tras el diseño

El diseño no añade modelos de datos, vistas ni dependencias; las comprobaciones siguen en verde.
