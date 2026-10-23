# Tasks: F61 · Capa de sentido

## Fase 1 · Base

- [x] T001 Enmendar la constitución a 2.0.0 (principio I, VI y restricciones técnicas) y `AGENTS.md`.
- [x] T002 Manifiesto `adaptadores/modelos_sentido.toml` con origen, licencia y SHA-256 de los tres ONNX y sus tokenizadores.
- [x] T003 Dependencias opcionales `requirements-sentido.in/.txt` y `requirements-sentido-modelo.txt`, con hashes; `pip-audit` en el CI.

## Fase 2 · Núcleo (pruebas primero)

- [x] T010 Pruebas de `tests/test_sentido_nucleo.py`: texto, filtros, veredicto, flujo completo y concordancia, con modelos simulados.
- [x] T011 `nucleo/sentido.py`: limpieza, cuerpo y unidades del prototipo.
- [x] T012 Filtros: membrete, marcas de lista y rótulos, cifras en letras y minuta completa.
- [x] T013 Emparejamiento: exacto, y si no, e5 con coseno de 0,9 o 70 % de palabras en común. Clasificación en las dos direcciones, `combinar` y texto sin respaldo.
- [x] T014 Concordancia nominal (dos palabras o menos) y sujeto–verbo (tres o menos), sin los errores que ya trae la minuta.

## Fase 3 · Adaptador

- [x] T020 Pruebas de `tests/test_sentido_adaptador.py` con dobles de ONNX Runtime, tokenizers y spaCy.
- [x] T021 `adaptadores/modelos_sentido.py`: verificación SHA-256, sesiones de 3 hilos, media de e5 sin relleno y softmax NLI en orden implica/neutral/contradice.
- [x] T022 Paridad de tokenizers con transformers en los tres modelos (ids y máscaras iguales, truncado a 512).

## Fase 4 · ERP

- [x] T030 Modelo `AnalisisSentido` y migración 0013.
- [x] T031 `expedientes/sentido.py`: pendientes, análisis con bloqueo, registro de error sin texto y supresión.
- [x] T032 Paso en `procesar_documentos`: una corrida por vuelta, después de las reglas.
- [x] T033 Interruptor `SENTIDO_ACTIVO`, carpeta `SENTIDO_MODELOS_DIR` e hilos `SENTIDO_HILOS`.
- [x] T034 Sección «Sentido frente a la minuta», endpoint de estado y sondeo.
- [x] T035 Informe: PDF, Word (`reporte-docx.js`) y Excel.
- [x] T036 `suprimir_texto_expediente` borra las anotaciones y conserva la huella.
- [x] T037 Comando `verificar_modelos_sentido`.
- [x] T038 Pruebas de `tests/test_sentido_expedientes.py`:
  - interruptor apagado y encendido;
  - corrida intacta y reproducibilidad;
  - worker, error, modelos ausentes y sin cambios;
  - transferencia vehicular, supresión, sesión y carga única.

## Fase 5 · Medición y entrega

- [x] T040 Medición privada con los modelos reales (12 proyectos y la demostración): 5 de 5, 0 falsas alarmas y tres corridas idénticas.
- [x] T041 `scripts/exportar_modelos_sentido.py`, para reproducir la exportación a ONNX.
- [x] T042 `quickstart.md`: instalación, activación, medición en el servidor y guía de uso.
- [ ] T043 Instalación en SQLSERVER (26/10/2026):
  - tiempo real en x86;
  - efecto sobre SQL Server;
  - inspección del tráfico (P-09);
  - tiempo máximo por escrito (5.2 b).
- [ ] T044 Revisión legal de la licencia GPL-3.0 de `es_core_news_md` antes de activar en producción.
- [ ] T045 Validar con la notaría, en la demostración, el umbral de 0,60 y los dos niveles.
