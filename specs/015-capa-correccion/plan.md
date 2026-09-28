# Implementation Plan: F21 · Capa de corrección y documento corregido

**Branch**: `Angello5/capa-de-corrección-y-documento-corregido-f21-correccion` | **Date**: 2026-09-28 | **Sources**: [spec.md](spec.md)

## Summary and scope

- `nucleo/correccion.py` (puro): `correcciones()`, `coincidencias()`.
- `adaptadores/docx_corregido.py`: aplica la carga útil a un `.docx` con `zipfile`.
- `expedientes`: conservación del original del borrador, `AplicacionCorreccion`
  (migraciones 0003 y 0004 `apariciones`), servicio `aplicar_correcciones`, vistas aplicar/descargar,
  parcial `_correcciones.html` incluido en `confrontacion.html`.
- `config/settings.py`: `EXPEDIENTES_ORIGINALES_DIR`.
- Constitución 1.6.0 → 1.7.0 (principio IV).

## Contrato

```text
correcciones(salidas, fuentes) -> [{id, campo, erroneo, correcto, fuente:{archivo,pagina}}]   un par erróneo→correcto, una fila
coincidencias(texto, valor) -> [(inicio, fin)]   índices del texto crudo, límites de palabra
apariciones(origen, correcciones) -> {id: n}   apariciones aplicables (vista)
aplicar(origen, destino, correcciones) -> ({id: n}, no_aplicadas)   todas las apariciones
aplicar_correcciones(expediente, borrador, huella, ids, usuario) -> AplicacionCorreccion
```

## Integración con F20 (Corrida / DecisionCorreccion)

F20 crea `Corrida` y `DecisionCorreccion` en paralelo. F21 guarda la huella de la
corrida como texto (`AplicacionCorreccion.huella_corrida`). Al integrar, el
revisor añade `corrida = ForeignKey(Corrida)` a `AplicacionCorreccion` (o la
sustituye por `DecisionCorreccion`), rellenándola por huella en una migración
de datos, y retira el campo de texto si sobra.

## Constitution Check

| Principio | Comprobación |
|---|---|
| I. Determinismo | ids por SHA-256; fuente = primera página en orden fijo. |
| II. Núcleo puro | `nucleo/correccion.py` sin Django ni E/S; el `.docx` en `adaptadores/`. |
| III. Tests primero | Pruebas rojas ficticias antes del código. |
| IV. Privacidad | **Enmienda 1.7.0**: se conserva el `.docx` del borrador (motivo: Anexo A del contrato). Resto igual. |
| V. Simplicidad | Sin dependencias: `zipfile` + `re`, como la extracción. |
| VI. Seguridad | Login, rol, permiso de expediente, CSRF, descarga por vista, permisos 0400/0700. |
| VII. DevSecOps | Suite, Ruff, `check`, `makemigrations --check`, `git diff --check`. |
| VIII. Usabilidad | Casillas marcadas por defecto, confirmación, mensajes claros. |

## Complexity Tracking

| Violación | Justificación |
|---|---|
| Conservar un archivo subido (IV) | Exigido por el Anexo A.3; enmienda MINOR 1.7.0 limitada al borrador `.docx`. |
