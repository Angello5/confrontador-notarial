# Quickstart de F5 · Confrontación

Antes de poner el servicio en marcha, aprovisione localmente el diccionario
Hunspell `es_PE` con este bloque (commit inmutable y hashes verificados):

```bash
mkdir -p ~/.cache/notaria-ocr
curl --fail --location --proto '=https' --tlsv1.2 \
  'https://raw.githubusercontent.com/LibreOffice/dictionaries/32b006a2c22a4ac7e8ed3f03346f7b3d85a970a4/es/es_PE.aff' \
  --output ~/.cache/notaria-ocr/es_PE.aff
curl --fail --location --proto '=https' --tlsv1.2 \
  'https://raw.githubusercontent.com/LibreOffice/dictionaries/32b006a2c22a4ac7e8ed3f03346f7b3d85a970a4/es/es_PE.dic' \
  --output ~/.cache/notaria-ocr/es_PE.dic
printf '%s  %s\n' \
  d966cb748e4a688ed75ec84b50c0835ac438e5325ee4fce703a093794f9cba7e \
  ~/.cache/notaria-ocr/es_PE.aff | sha256sum --check
printf '%s  %s\n' \
  1d810a0a319fee329000538cf4df76621bb71228172558b87490f8b9c19b9d75 \
  ~/.cache/notaria-ocr/es_PE.dic | sha256sum --check
```

La confrontación no descarga recursos durante una petición web. Si falta alguno
de los dos archivos, devuelve un mensaje seguro indicando que el diccionario
debe aprovisionarse antes de iniciar el servicio, sin mostrar una traza ni
contenido de documentos.
