# Quickstart de F5 · Confrontación

Antes de poner el servicio en marcha, aprovisione localmente el diccionario
Hunspell `es_PE` en `~/.cache/notaria-ocr/es_PE.aff` y
`~/.cache/notaria-ocr/es_PE.dic`. Use el commit y los hashes fijados en
`specs/001-base-devsecops/quickstart.md` y en el paso `Verify public test
resources` de `.github/workflows/ci.yml`.

La confrontación no descarga recursos durante una petición web. Si falta alguno
de los dos archivos, devuelve un mensaje seguro indicando que el diccionario
debe aprovisionarse antes de iniciar el servicio, sin mostrar una traza ni
contenido de documentos.
