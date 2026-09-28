# Implementation Plan: F20 · Manifiesto de auditoría

**Branch**: `f20-manifiesto` | **Date**: 2026-09-28 | **Sources**: [spec.md](spec.md)

## Summary and scope

- `nucleo/catalogo_reglas.toml`: datos, sin código.
- `expedientes/services.py`: carga del catálogo, `severidad()`, `confrontar_y_registrar()` (envuelve `confrontar_borrador`, añade severidad y crea la `Corrida`), `hallazgos_canonicos()`, `reconstruir_corrida()`. `confrontar_borrador` gana `fecha` y `fuentes_documentos` opcionales.
- `expedientes/models.py`: `Corrida`, `DecisionCorreccion` y base abstracta `Inmutable` (dos implementaciones reales); migración `0003`.
- `expedientes/management/commands/reconstruir_corrida.py`.
- Vistas y plantillas `historial.html`, `corrida.html`; enlace desde el detalle; columna de severidad en el resultado.

## Contrato

```text
severidad(campo) -> "ALTA" | "MEDIA" | "BAJA"
confrontar_y_registrar(expediente, borrador, usuario) -> resultado   # siempre crea Corrida
hallazgos_canonicos(resultado) -> str                                # JSON canónico
reconstruir_corrida(corrida) -> dict(conforme, huella, total, mensajes)
```

## Constitution Check

| Principio | Comprobación |
|---|---|
| I. Determinismo | Huella SHA-256 de JSON canónico; fecha de referencia registrada. |
| II. Núcleo puro | El núcleo no cambia; el TOML lo lee `services.py`. |
| III. Tests primero | Pruebas rojas ficticias antes de implementar. |
| IV. Privacidad | Solo hallazgos ya mostrados; nada en el sondeo ni en logs. |
| V. Simplicidad | Stdlib; sin API ni dependencias. `Inmutable` tiene dos modelos. |
| VI. Seguridad | Auditoría de quién confrontó qué, cuándo y con qué hash; permisos del expediente. |
| VII. DevSecOps | Suite, Ruff, `check`, `makemigrations --check`, `git diff --check`. |

## Complexity Tracking

Ninguna violación.
