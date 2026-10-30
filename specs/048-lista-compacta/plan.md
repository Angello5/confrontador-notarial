# Implementation Plan: F65 · Lista de observaciones compacta

**Branch**: `feat/f65-lista-compacta` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Solo presentación. Se quita la `<section>` de detalle de `templates/expedientes/confrontacion.html` y su `x-ref`; la lista pasa a mostrar lo que el panel decía:

- `_obs_cambio.html` muestra «Dice» y «Debe decir» (o «En el borrador», «Qué verificar» y «Se sugiere») en líneas pequeñas, con las palabras distintas en `<mark>`.
- `partes_distintas` (en `expedientes/services.py`) parte dos textos en tramos iguales y distintos: prefijo y sufijo de palabras comunes, el medio es lo distinto. `resultado_de_corrida` lo deja en `cambio` de cada fila; «No aparece en el borrador» no se resalta.
- `aviso_de` devuelve también `sugerencia` (F64) para que la fila la ponga en su propia línea.
- La casilla de `_obs_correccion.html` pasa a la fila, fuera del botón de la fila (no se anidan controles).
- La línea del borrador (`_obs_borrador.html`) se muestra en la fila elegida solo si no hay vista del documento.
- CSS: la columna lateral se ensancha; `.sev-pref` se oculta por debajo de 1 280 px; estilos de las líneas pequeñas y del resaltado.
- `_marca.html`: el sello queda oculto detrás del logo y se muestra si la imagen falla (`onerror`), sin depender de Alpine (también en el admin).

## Constitution Check

| Principio | Cómo se cumple |
|---|---|
| I. Determinismo | Sin cambios en el núcleo ni en la corrida. |
| II. Núcleo puro | El resaltado es presentación, en `expedientes/services.py`; el núcleo no cambia. |
| III. Pruebas primero | Pruebas del filtro, de `aviso_de` y de la pantalla antes del cambio. |
| IV. Privacidad | Datos ficticios. |
| V. Simplicidad | Se quita un panel; una función de unas 20 líneas; sin dependencias. |
| VIII. Usabilidad | Ver UX de la spec. |

## Pruebas

- `tests/test_lista_compacta.py`: `partes_distintas`, `aviso_de` con `sugerencia` y la pantalla (con base de datos: corre en el CI y en local con PostgreSQL sobre la copia de `b611879`, cuyo `services.py` y plantillas son iguales a `main`).
- Revisión visual en la demo ficticia (`erp-f64-demo`, puerto 8064) a 1 024 y 1 440 px.
