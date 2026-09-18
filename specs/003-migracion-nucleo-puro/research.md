# Research: Migración del núcleo puro

## Decisiones

### Paquete común y adaptadores

- **Decisión**: colocar verificación, léxico y ortografía en `nucleo/`; dejar extracción de archivos/OCR y aprovisionamiento del diccionario en adaptadores.
- **Rationale**: responde a Clarifications y al principio II. Actualmente `verificar.py` y `lexico.py` importan `extraer.py`; `ortografia.py` descarga el diccionario y lee/escribe la lista de términos. Estos son los bordes de E/S que impiden que las reglas sean puras.
- **Alternativas consideradas**: mover todo el código a una capa nueva; descartada porque aumenta el diff y las reglas deben conservarse casi como están. Mantener todo junto; descartada porque deja E/S en el núcleo.

### Interfaces durante F3

- **Decisión**: adaptar los imports de `app.py` y `app_ortografia.py` y conservar ambas aplicaciones hasta paridad ERP en F4/F5. Mover `revisor_llm.py` y `bench_llm.py` a `experimental/`; el ERP no los importa.
- **Rationale**: respuesta aclarada por el usuario y principio I. Las pruebas de prosa existentes permanecen aisladas y sin llamadas a modelos.
- **Alternativas consideradas**: retirar Streamlit en F3; descartada porque no hay paridad ERP. Mantener la capa de prosa en el flujo productivo; descartada por la constitución.

### Comparación OCR

- **Decisión**: comparar la configuración actual RapidOCR 3.4.3/PP-OCRv4 ch con PP-OCRv5 latin y `use_cls=False`. No cambiar versión ni modelos antes de fijar por hash los archivos de ambas configuraciones y preparar el test sintético. Elegir un RapidOCR compatible con PP-OCRv5 si 3.4.3 no expone esa configuración.
- **Rationale**: el quickstart F1 identifica modelos PP-OCRv4 y hashes; la documentación oficial de RapidOCR indica soporte de PP-OCRv5 con RapidOCR 3.5.0 o posterior y enumera el reconocedor `latin_PP-OCRv5_rec_mobile`. La versión exacta y hashes del paquete/modelos candidatos se fijan en la etapa OCR, antes de ejecutar la comparación, para evitar depender de modelos descargados por defecto.
- **Alternativas consideradas**: actualizar RapidOCR directamente a una versión flotante; descartada porque no sería reproducible. Conservar v4 sin medir; no responde a la decisión solicitada. La medición no se ejecuta en CI ni con datos versionados.
- **Fuentes primarias**: [RapidOCR model list](https://github.com/RapidAI/RapidOCRDocs/blob/main/docs/model_list.md), [RapidOCR default model manifest](https://github.com/RapidAI/RapidOCR/blob/main/python/rapidocr/default_models.yaml).
- **Criterio de selección**: cambiar a v5 solo si `local_reference` produce 8 observaciones, las cinco salidas son idénticas, la escritura correcta produce cero observaciones y el test OCR sintético conserva todas las líneas y acentos/Ñ. Si falla un criterio, retener PP-OCRv4 y documentar la medición; el destino del PR #11 queda condicionado al resultado.

### Deuda técnica

- **Decisión**: revisar los diez IDs Sonar individualmente según `docs/deuda-f3.md`, priorizando tests sintéticos antes de cambios de comportamiento. Resolver cada hallazgo con cambio mínimo o registrar razón/riesgo residual por escrito. Revisar antlr4 con una instalación bloqueada de `setuptools` y `--no-build-isolation`, validar hash y registrar resultado. La llamada de `revisor_llm.py` debe pasar la API key fuera de la query URL.
- **Rationale**: el inventario y la propuesta para antlr4 ya están documentados; no se debe diluir el requisito por tratarse de un plan de migración.
- **Alternativas consideradas**: corregir olores de forma masiva o justificar todo sin revisar; ambas descartan evidencia por ID y dejan riesgos sin evaluación.

## Límites pendientes de ejecución

- El usuario ejecuta `local_reference` desde su entorno autorizado; nadie incorpora ni comunica contenido documental. La tarea debe devolver solo los agregados requeridos y el resultado de aprobación.
- La versión exacta de RapidOCR v5 compatible y sus hashes se fijan antes de cualquier benchmark/cambio de lock; no se asume que el manifest `main` sea inmutable.
- No se ejecuta aquí ninguna medición, test de implementación, actualización de dependencia ni acción sobre el PR #11.
