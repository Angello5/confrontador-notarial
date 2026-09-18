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
| **Prosa** | Concordancia y sintaxis | Modelo de lenguaje, con validación mecánica posterior | No |

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

Para la capa de prosa, copia `.env.example` a `.env` y pon tu clave, o exporta
`GEMINI_API_KEY`. Sin clave, todo lo demás sigue funcionando.

## Uso

Dos interfaces, según la vía:

```bash
streamlit run app.py --server.port 8502            # reglas + prosa con Gemini
streamlit run app_ortografia.py --server.port 8503 # reglas + diccionario, sin nube
```

Y por línea de comandos:

```bash
python3 verificar.py <fuentes...> -d <borrador>   # datos duros
python3 extraer.py <archivo|carpeta>              # solo el texto extraído
python3 ortografia.py <documento>                 # solo ortografía
python3 lexico.py <escrituras firmadas> -d <borrador>
python3 bench_llm.py [modelo...]                  # compara modelos de prosa
```

## Formatos que lee

`.docx` · `.doc` · `.rtf` · `.odt` · `.pdf` (con y sin capa de texto) · `.xlsx`
· `.txt` · `.csv` · imágenes con OCR

Notas de implementación que cuestan caro descubrir:

- El `.docx` se lee del XML en crudo, no con `python-docx`: `document.paragraphs`
  no entra a los cuadros de texto ni a los encabezados, y en un caso real ahí
  vivían dos notas al notario con una errata. También se descarta `mc:Fallback`,
  que guarda cada cuadro de texto por duplicado.
- El `.doc` binario va por `textutil`, que viene con macOS. **En Linux hay que
  sustituirlo** por LibreOffice headless; el código lo detecta y falla con un
  mensaje claro en vez de devolver texto corrupto.
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
python3 test_extraer.py && python3 test_verificar.py && python3 test_lexico.py \
  && python3 test_ortografia.py && python3 test_revisor_llm.py
```

> **Necesitan los fixtures sintéticos de la etapa 2**, que no están en este repositorio
> (todavía no generados). En un clon limpio fallan por archivo no encontrado: es
> esperado. `test_ortografia.py` y `test_revisor_llm.py` sí corren solos —
> el segundo no llama a la API, solo ejercita los filtros.

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
> `tests/fixtures/`; su generador se implementará en la etapa 2. El historial
> anterior permanece privado: publicar el repositorio exige limpiarlo en otra fase.

## Estado

Prueba de concepto validada sobre **dos expedientes reales**, de los cuales solo
uno tiene versión corregida contra la cual medir cobertura. Eso significa que
sabemos qué encuentra, no qué se le escapa.

Lo que falta para llamarlo MVP: medir cobertura sobre 10 expedientes cerrados,
un catálogo declarativo de campos por tipo de acto (hoy las reglas están
escritas a mano para donación y mutuo), persistencia, informe exportable y
control de accesos.
