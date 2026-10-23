# Confrontador de documentos notariales

Compara el proyecto de escritura pública contra la minuta y los documentos del
cliente, y señala las diferencias. Corre en local, sobre CPU.

El objetivo de diseño es la **reproducibilidad**: los datos con una única
respuesta correcta —DNI, partida registral, montos, nombres— los decide el
código por igualdad exacta contra la fuente, nunca un modelo de lenguaje. La
misma entrada da siempre la misma salida.

## Las tres capas

| Capa | De qué responde | Cómo decide | ¿Reproducible? |
|---|---|---|---|
| **Regla** | DNI, partida, montos, nombres | Igualdad exacta contra la fuente | Sí |
| **Léxico** | Erratas de vocabulario | Palabra ausente del corpus de escrituras firmadas | Sí |
| **Ortografía** | Palabras que no son castellano | hunspell `es_PE` + lista de la casa | Sí |
| **Sentido** (F61, opcional) | Cambios de sentido frente a la minuta y concordancia | spaCy y clasificadores NLI locales en ONNX Runtime; solo anota, sin autoridad | Sí, con versiones fijas e hilos fijos |
| **Prosa** | Concordancia y sintaxis | Modelo de lenguaje, con validación mecánica posterior | No (solo `experimental/`) |

Ningún hallazgo del modelo llega al informe sin pasar cuatro filtros mecánicos:
que el texto señalado exista literalmente en el documento, que la corrección
difiera del error, que no invada un dato duro, y que no sea una tilde añadida
sobre mayúsculas (convención notarial peruana, no error).

## Instalación

```bash
python3 -m pip install -r requirements.txt
```

El diccionario `es_PE` (0.8 MB) se descarga solo la primera vez a
`~/.cache/notaria-ocr/`. Los modelos de OCR los descarga RapidOCR igual.

Para la capa de prosa experimental (`experimental/`, fuera del ERP), copia
`.env.example` a `.env` y pon tu clave, o exporta `GEMINI_API_KEY`. Sin clave,
todo lo demás sigue funcionando.

## Uso

### ERP (Django)

```bash
python manage.py migrate
python manage.py bootstrap_admin                 # primera vez: crea la cuenta local
python manage.py runserver 127.0.0.1:8000
python manage.py procesar_documentos             # worker de extracción, en otra terminal
```

Requiere `DJANGO_SECRET_KEY` y la conexión PostgreSQL (`POSTGRES_*`) fuera del
repositorio. El worker procesa la cola y termina: prográmalo cada minuto o
ejecútalo en bucle. Detalle en [la guía F4](specs/004-expedientes/quickstart.md).

### Línea de comandos

La prueba de concepto en Streamlit (`app.py`, `app_ortografia.py`) se eliminó
el 2026-10-20: el ERP la supera (constitución 1.7.1).

```bash
python3 verificar.py <fuentes...> -d <borrador>   # datos duros
python3 extraer.py <archivo|carpeta>              # solo el texto extraído
python3 ortografia.py <documento>                 # solo ortografía
python3 lexico.py <escrituras firmadas> -d <borrador>
python -m experimental.bench_llm [modelo...]      # compara modelos de prosa
```

## Formatos que lee

`.docx` · `.doc` · `.rtf` · `.odt` · `.pdf` (con y sin capa de texto) · `.xlsx`
· `.txt` · `.csv` · imágenes con OCR

Notas de implementación que cuestan caro descubrir:

- El `.docx` se lee del XML en crudo, no con `python-docx`: `document.paragraphs`
  no entra a los cuadros de texto ni a los encabezados, y en un caso real ahí
  vivían dos notas al notario con una errata. También se descarta `mc:Fallback`,
  que guarda cada cuadro de texto por duplicado.
- El `.doc` binario va por `textutil` en macOS y por LibreOffice headless
  (`soffice` en PATH) en Linux, con perfil temporal propio y timeout; si falta
  o falla, el error es claro y no incluye contenido ni rutas.
- El OCR se cachea por SHA-1 del contenido del archivo, no por ruta.

## Resultados medidos

Sobre el único expediente con verdad verificable (borrador defectuoso contra la
escritura firmada):

```
datos duros              8 de 8 errores · 0 falsos positivos
reproducibilidad         5 corridas, salida idéntica (mismo hash)
tiempo                   19 s en frío · 0.3 s con caché de OCR
```

Frente al enfoque anterior, que delegaba todo al modelo: tres corridas con
entrada idéntica devolvieron **19, 22 y 27** discrepancias.

## Pruebas

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python scripts/generar_fixtures.py
python -m pytest --cov --cov-report=term --cov-report=xml:coverage.xml
```

Usar Python 3.13. El generador crea los fixtures ficticios localmente, sin
expedientes ni dependencias adicionales. El aprovisionamiento de OCR y
diccionario está en [la guía F1](specs/001-base-devsecops/quickstart.md).
El test del filtro no llama a la API. En Linux, los tests legacy requieren
LibreOffice (`soffice`).

## Datos personales

**Los expedientes no se versionan.** Contienen DNI, nombres, domicilios y
escrituras públicas de personas reales. `.gitignore` bloquea las carpetas
`Cliente/`, `Proyecto*/`, `Resultado/` y las extensiones de documento.

Para trabajar, coloca cada expediente en su **propia carpeta** junto al código.
Uno por carpeta: si se mezclan dos, el catálogo junta los DNI de ambos y las
comprobaciones dejan de tener sentido.

```
confrontador-notarial/
   Cliente/  Proyecto(borrador)/  Resultado/   ← expediente de referencia
   expediente-00001/
      Cliente/  Proyecto(borrador)/  Plantilla/
```

Todo eso queda ignorado por git automáticamente. La copia de seguridad de los
expedientes es responsabilidad de la notaría, fuera de este repositorio.

> **Saneamiento F1:** los tests usan datos ficticios y rutas bajo
> `tests/fixtures/`; se regeneran con el script anterior. El historial
> anterior permanece privado: publicar el repositorio exige limpiarlo en otra fase.

## Estado

ERP en desarrollo, integrado en `main` hasta la fase F45 (PR #88,
2026-10-09). Ya tiene control de accesos por rol (F2), kardex con extracción en
segundo plano (F4), historial de corridas (F20), corrección del `.docx` (F21),
informe Word (F29) y flujo de transferencia vehicular (F43–F45). El detalle por
fase está en [docs/roadmap.md](docs/roadmap.md).

Lo que falta para llamarlo MVP: medir cobertura sobre 10 expedientes cerrados,
el despliegue en el servidor de la notaría con respaldo diario (F8) y un
catálogo declarativo de campos por tipo de acto (F9).
