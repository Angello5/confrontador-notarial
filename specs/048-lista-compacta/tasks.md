# Tasks: F65 · Lista de observaciones compacta

**Tests**: primero (principio III).

## Fase 1 · Base

- [X] T001 Roadmap: F65 en la «Continuación autorizada · 2026-10-30» de `docs/roadmap.md`.

## Fase 2 · Historia 1 · Lista sin panel de detalle (P1) 🎯 MVP

- [X] T010 [US1] Pruebas de `partes_distintas` en `tests/test_lista_compacta.py` (palabra distinta, sin palabras comunes, iguales, sin «debe decir»).
- [X] T011 [US1] Prueba de `aviso_de`: devuelve `sugerencia` cuando F64 la trae y no la trae en los demás avisos.
- [X] T012 [US1] Prueba de la pantalla: sin «Detalle de la observación»; la fila trae «Debe decir», el resaltado y la casilla de corrección.
- [X] T013 [US1] `partes_distintas` y el cambio resaltado de cada fila en `resultado_de_corrida` (`expedientes/services.py`; sin módulo de filtros nuevo).
- [X] T014 [US1] `aviso_de` con `sugerencia` en `expedientes/services.py`.
- [X] T015 [US1] `_obs_cambio.html`: líneas pequeñas con resaltado y «Se sugiere».
- [X] T016 [US1] `confrontacion.html`: quitar el panel y su `x-ref`; casilla y línea del borrador en la fila; ajustar `elegir()`.
- [X] T017 [US1] CSS de la lista ancha, las líneas pequeñas y el resaltado en `static/css/erp.css`.

## Fase 3 · Historia 2 · Contadores y logo (P2)

- [X] T020 [US2] Prueba: `_marca.html` con logo trae el sello de reemplazo oculto.
- [X] T021 [US2] `.sev-pref` oculto por debajo de 1 280 px en `static/css/erp.css`.
- [X] T022 [US2] `_marca.html`: sello de reemplazo si el logo falla.

## Fase 4 · Cierre

- [X] T030 Revisión visual en la demo ficticia a 1 024 y 1 440 px.
- [X] T031 Suite, Ruff y diff sin datos reales.
