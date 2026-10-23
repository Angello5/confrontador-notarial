# Implementation Plan: F61 · Capa de sentido

**Branch**: `feat/f61-capa-sentido` | **Date**: 2026-10-22 | **Spec**: [spec.md](spec.md)

## Summary

Se lleva al ERP el verificador semántico local elegido en el CR-01 (Alternativa B), en la configuración para el servidor del Informe de Evaluación v1.1 (sección 7 y Anexo H):

- spaCy para la segmentación y la concordancia;
- e5-small para emparejar oraciones;
- mDeBERTa y MiniLM como clasificadores NLI.

Los tres modelos de red neuronal corren en ONNX Runtime en CPU, sin PyTorch. Se suman los cuatro filtros deterministas del plan de implementación del informe (sección 10):

- membrete repetido;
- marcas de lista y rótulos;
- cifras en letras;
- búsqueda en la minuta completa.

## Technical Context

- **Language/Version**: Python 3.13.
- **Primary Dependencies**:
  - ya instaladas: Django y ONNX Runtime 1.30 (OCR), rapidfuzz y numpy;
  - opcionales en `requirements-sentido.txt`: spaCy 3.8 y tokenizers 0.23;
  - aparte, en `requirements-sentido-modelo.txt`: `es_core_news_md` 3.8.0.
- **Storage**: PostgreSQL. Tabla nueva `expedientes_analisissentido` (migración 0013). Los modelos van en una carpeta local fuera del repositorio (`SENTIDO_MODELOS_DIR`).
- **Testing**:
  - pytest con datos ficticios y dobles de los modelos (en el CI no hay modelos);
  - `node --test` para el informe Word;
  - medición privada con los modelos reales sobre los kardex locales.
- **Target Platform**: SQLSERVER (Windows Server 2019, Xeon Bronze 3204, 64 GB, sin GPU).
- **Performance Goals**: el tiempo por expediente que las partes fijen por escrito (propuesta: 3 minutos). Memoria de la capa: unos 2,2 GB.
- **Constraints**: sin red, sin GPU, 32 bits (el 8 bits subió las falsas alarmas), 3 hilos y un expediente a la vez.

## Constitution Check

| Principio | Cómo se cumple |
|---|---|
| I. Determinismo | Enmienda 2.0.0: capa de sentido no generativa, sin autoridad, con versiones fijas e interruptor. La corrida y su huella no cambian: el análisis va en otra tabla. Tres corridas dan las mismas huellas. |
| II. Núcleo puro | `nucleo/sentido.py` no importa Django, la base de datos ni los modelos: recibe funciones. `adaptadores/modelos_sentido.py` carga los modelos. `expedientes/sentido.py` orquesta. |
| III. Pruebas primero | Las pruebas del núcleo se escribieron antes del código. Cada regla nueva (filtros, distancia sujeto–verbo) empezó con una prueba que fallaba. |
| IV. Privacidad | Sin red. Los logs no llevan texto. La supresión borra las oraciones guardadas. Las pruebas usan frases ficticias. |
| V. Simplicidad | Una tabla, un módulo por capa y un comando de verificación. Sin cola nueva: un paso más en el worker existente. Sin abstracciones: `Modelos` es la única implementación. |
| VI. Seguridad | Mismos permisos que la pantalla de confrontación. Modelos verificados por SHA-256. Endpoint `no-store`. |
| VII. DevSecOps | `pip-audit` audita `requirements-sentido.txt` en el CI. Dependencias con hashes. Cobertura de los archivos nuevos registrada en `tests/conftest.py`. |
| VIII. Usabilidad | Ver la sección UX de la spec. |

## Complexity Tracking

| Complejidad | Por qué | Alternativa descartada |
|---|---|---|
| Dependencias nuevas (spaCy, tokenizers, modelo de español) | spaCy es la pieza de segmentación y concordancia que pidió el usuario. tokenizers da los mismos ids que transformers sin PyTorch (paridad verificada en los tres modelos). | transformers + PyTorch: más de 1 GB adicional y un segundo motor junto a ONNX Runtime. |
| Archivo de requisitos aparte | La capa es opcional: el CI y los equipos sin la capa no instalan nada nuevo. | Meterlas en `requirements.txt`: más de 40 paquetes en todos los entornos. |
| Tabla mutable para el análisis | Las anotaciones guardan oraciones y la supresión debe poder borrarlas (Ley 29733). | Guardarlas en la corrida inmutable: no se podrían suprimir y cambiaría su huella. |

## Estructura

```text
nucleo/sentido.py                         # flujo puro: filtros, emparejamiento, veredicto, concordancia
adaptadores/modelos_sentido.py            # ONNX Runtime, tokenizers y spaCy; verificación SHA-256
adaptadores/modelos_sentido.toml          # manifiesto: origen, licencia y huella de cada modelo
expedientes/sentido.py                    # pendientes, análisis, supresión y datos de pantalla
expedientes/models.py                     # AnalisisSentido
expedientes/migrations/0013_analisis_sentido.py
expedientes/management/commands/verificar_modelos_sentido.py
templates/expedientes/_sentido.html       # sección y sondeo de estado
scripts/exportar_modelos_sentido.py       # cómo se produjeron los ONNX (equipo de desarrollo)
requirements-sentido.in/.txt, requirements-sentido-modelo.txt
```
