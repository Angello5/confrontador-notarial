# Implementation Plan: F14 · Rediseño de interfaz

**Branch**: `feature/f14-rediseno-ui` | **Date**: 2026-09-27 |
**Sources**: [spec.md](spec.md), [contracts/ui.md](contracts/ui.md), capturas
del diseño fuera del repositorio (`~/pruebas-confrontador/figma/`, no se copian).

## Summary and scope

Cambia la piel, no la aplicación. Una hoja `static/css/erp.css` con los tokens
de la spec y la redefinición de variables Bootstrap/AdminLTE; el shell en
`templates/core/base.html`; cuatro fragmentos reutilizables en
`templates/core/_*.html`; las seis pantallas se visten con ellos. Solo Inicio
recibe contexto nuevo. Sin migraciones, dependencias, fuentes remotas, IA ni
cambio del sondeo JSON.

## Technical context

Django 5 + AdminLTE 4 / Bootstrap 5.3 / Alpine 3 ya empaquetados en
`static/vendor/`. Se reutilizan `expedientes_visibles()` y
`resumen_expediente()`; la lista y el Inicio comparten una sola función
`expedientes_con_resumen(usuario)` en `expedientes/services.py` (la consulta
no se duplica, FR-004). La navegación (`es_administrador`) se sigue calculando
como hoy en cada vista; el nombre, rol e iniciales salen de `user` y
`es_administrador` en la plantilla.

## Constitution Check

| Principio | Comprobación |
|---|---|
| I. Determinismo | Sin cambio de núcleo. Chips, métricas y riel se derivan del estado existente (FR-006). |
| II. Núcleo puro | Sin cambio. `services.py` gana una función de lectura que reúne dos existentes; las vistas siguen delgadas. |
| III. Tests primero | Tests de plantilla rojos antes de cada pantalla; los existentes solo se adaptan en marcado. |
| IV. Privacidad | Inicio expone solo código, estado, contadores y fecha; nunca texto, hash ni ruta. Datos ficticios. |
| V. Simplicidad | Un CSS, cuatro fragmentos de plantilla, una función de servicio. Sin dependencias, sin JS nuevo fuera de expresiones Alpine en línea. |
| VI. Seguridad | Mismas rutas, métodos, permisos y CSRF. El menú muestra solo lo que el rol puede usar. Assets locales. |
| VII. DevSecOps | Suite con cobertura, Ruff, `check`, `makemigrations --check`, `git diff --check`. Quality Gate remoto pendiente sin push. |
| VIII. Usabilidad | Contraste AA, foco visible, `aria-current`, `caption`, `aria-expanded`, texto equivalente del riel, responsivo a 390 px. |

## Diseño

```text
base.html
  body (Alpine: menuAbierto)
    aside.app-sidebar[data-bs-theme=dark]  marca CN · CONFRONTADOR / ERP NOTARIAL
      sección «Menú principal»: Inicio, Expedientes (según rol)
      sección «Administración» (solo es_administrador): Usuarios y permisos → /admin/
      pie: username + rol
    header.app-header  ☰ (solo < lg) · {% block breadcrumb %} · avatar · Cerrar sesión
    main  cabecera de página: {% block eyebrow %} {% block heading %}
          {% block subtitle %} {% block actions %} · mensajes · {% block content %}
core/_chip.html     estado → píldora (data-estado); opcional sondeo por id
core/_metrica.html  etiqueta con punto · valor · apoyo
core/_riel.html     4 pasos; data-actual en la lista, CSS marca hecho/actual/pendiente
core/_zona_arrastre.html  label punteado con «+», título, ayuda y el input real
```

Paso actual del riel (US4, en la plantilla del detalle, sin contexto nuevo):
falta cliente o minuta → 1 Fuentes; falta borrador → 2 Borrador; `LISTO` →
4 Resultado; resto (`PROCESANDO`, `ERROR`) → 3 Procesamiento. Los pasos 3/4
se recalculan en Alpine desde `estado` del sondeo actual.

## Verificación y entrega

1. Tests de plantilla rojos (tasks.md), luego plantillas y CSS.
2. `python manage.py check`, `makemigrations --check`, Ruff check/format,
   suite con cobertura (código nuevo ≥ 80 %), `git diff --check`.
3. Render real en `127.0.0.1:8001` a 1440 y 390 px de las seis pantallas.
4. Commits locales en `feature/f14-rediseno-ui`, sin push ni PR.

## Complexity Tracking

Ninguna violación. `expedientes_con_resumen()` evita duplicar la consulta de
visibilidad entre lista e Inicio; los fragmentos existen porque cada uno se
usa en al menos dos lugares.
