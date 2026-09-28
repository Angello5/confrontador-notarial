# Implementation Plan: F26 · Confrontación automática al terminar la carga

**Branch**: `f26-confrontacion-automatica` | **Date**: 2026-09-28 | **Sources**: [spec.md](spec.md)

## Summary and scope

- `expedientes/models.py`: `Corrida.origen`, `Corrida.presentacion`; migración `0004`.
- `expedientes/services.py`: `registrar_corrida(..., origen)` guarda la presentación;
  `corrida_vigente()`, `estado_borrador()`, `confrontar_automaticamente()`, `resultado_de_corrida()`.
- `procesar_documentos`: llama a `confrontar_automaticamente()` tras vaciar la cola.
- `views.py`/`urls.py`: `documento_resultado`; detalle y sondeo usan `estado_borrador()`.
- `detalle.html`: estados del botón con Alpine; el sondeo sigue mientras falte un resultado.

## Contrato

```text
corrida_vigente(expediente, borrador) -> Corrida | None
estado_borrador(expediente, borrador, fuentes) -> {disponible, mensaje, resultado_listo}
confrontar_automaticamente() -> int   corridas creadas
resultado_de_corrida(corrida) -> dict resultado para confrontacion.html
```

## Constitution Check

| Principio | Comprobación |
|---|---|
| I. Determinismo | Misma confrontación; solo cambia cuándo se ejecuta. |
| II. Núcleo puro | El núcleo no cambia; el worker orquesta. |
| III. Tests primero | Pruebas rojas ficticias antes de implementar. |
| IV. Privacidad | El JSON solo añade un booleano; nada en logs. |
| V. Simplicidad | Sin colas nuevas ni dependencias; reutiliza la corrida de F20. |
| VI. Seguridad | La vista nueva exige rol y visibilidad del expediente. |
| VII. DevSecOps | Suite, Ruff, `check`, `makemigrations --check`, `git diff --check`. |

## Complexity Tracking

Ninguna violación.
