# Contrato de interfaz: F14 · Rediseño de interfaz

Rutas, métodos, permisos, CSRF, formularios, mensajes, textos de estado y el
JSON de `expediente_estado` no cambian (FR-005). Todas las pantallas
autenticadas extienden `core/base.html`. Estilos solo en `static/css/erp.css`.

## Shell (`core/base.html`) — todas las pantallas autenticadas

| Bloque | Cambio | Contexto |
|---|---|---|
| Menú lateral | Navy, marca «CN · CONFRONTADOR / ERP NOTARIAL», sección «Menú principal» con Inicio y Expedientes; sección «Administración» con «Usuarios y permisos» → `/admin/` solo si `es_administrador`. Ítem activo con `aria-current="page"` (Expedientes activo en lista, detalle y confrontación). Pie: `username` y rol. | Existente: `user`, `es_administrador`, `es_usuario`, `request.resolver_match`. |
| Barra superior | ☰ (`aria-expanded`, solo < lg), `{% block breadcrumb %}` dentro de `nav[aria-label="Migas de pan"]`, avatar con dos iniciales, «Cerrar sesión». | Existente. |
| Cabecera de página | Bloques `eyebrow`, `heading`, `subtitle`, `actions`. | — |
| Cambio de clave obligatorio | Sin marca, menú, migas ni ☰ (como hoy). | `user.force_password_change`. |

Tests: `tests/test_shell.py` (roles, ítem activo, pie, CSS local, pendiente).

## Fragmentos (`templates/core/`)

- `_chip.html`: `estado` (VACIO, PENDIENTE, PROCESANDO, LISTO, ERROR, o tipo
  de observación) → `<span class="chip" data-estado=…>` con el texto actual
  («Sin documentos», «Pendiente», «Procesando», «Listo», «No se pudo
  procesar») o `texto`. Con `sondeo_id`, Alpine actualiza `data-estado` y el
  texto desde `documentos` del sondeo.
- `_metrica.html`: `etiqueta`, `valor`, `apoyo`, `tono`.
- `_riel.html`: `actual` (1–4) y, opcional, `x_actual` (expresión Alpine).
  Lista ordenada «Fuentes → Borrador → Procesamiento → Resultado» con texto
  oculto «Paso actual: …».
- `_zona_arrastre.html`: `campo` (el input de archivos), `titulo`, `ayuda`.
  El input real cubre la zona: se puede arrastrar o pulsar; teclado y lector
  usan el input nativo.

## Ingreso (`registration/login.html`)

Fondo navy con marca; tarjeta blanca con el mismo formulario crispy, mensajes
y errores. Carga `erp.css`. Tests: `tests/test_shell.py`, `tests/test_login.py`.

## Inicio (`core/home.html`) — único contexto nuevo

| Clave | Valor |
|---|---|
| `metricas` | `{"total", "procesando", "listos", "errores"}` enteros, sobre `expedientes_con_resumen(request.user)`. |
| `ultimos` | Los 5 primeros `(expediente, resumen)` de esa misma lista (orden `-actualizado_el, -pk`). La plantilla usa solo `codigo`, `pk`, `actualizado_el` y `resumen.estado`. |

Pantalla: eyebrow «Inicio», título «Resumen general»; cuatro tarjetas
(«Expedientes», «Procesando», «Listos para confrontar», «Con error»); tabla
«Últimos expedientes» (código, estado en chip, actualizado, Abrir) o, sin
expedientes, ayuda con enlace a crear el primero; tarjeta navy «Nueva
confrontación» con tres pasos y botón «Comenzar» → Expedientes, o para
`es_administrador` «Control administrativo» con «Administrar» → `/admin/`.
Tests: `tests/test_shell.py` (métricas ficticias, visibilidad por usuario,
sin texto/hash/ruta en contexto ni HTML, variante administrador, vacío).

## Expedientes (`expedientes/lista.html`)

Cabecera «Expedientes» con botón «+ Nuevo expediente» que muestra el
formulario actual (Alpine; visible de entrada si hay errores). Tabla: código,
estado en chip, documentos (`resumen.total`), actualizado, Abrir, con
`caption`. Contexto: el mismo, construido con `expedientes_con_resumen()`.
Tests: `tests/test_expedientes_ui.py` (chip por estado, formulario con error
visible).

## Expediente (`expedientes/detalle.html`, `_zona_carga.html`)

Cabecera con el código; riel con paso actual; estado del expediente con los
textos actuales (`aria-live`); panel izquierdo «Documentos del expediente»
(zonas Cliente y Minuta), panel derecho «Borrador a confrontar» (zona Borrador
y botones «Confrontar borrador» navy por borrador, habilitados solo cuando el
sondeo lo permite); línea de privacidad. Cada zona: título, descripción,
«Obligatorio», zona de arrastre con el input `multiple`, «Cargar …», errores;
filas de archivo con ✓, chip de estado del sondeo y «Eliminar» con
confirmación. Sin contexto nuevo. Tests: `tests/test_expedientes_ui.py`
(paso del riel por estado, tres zonas, chips, privacidad).

## Resultado (`expedientes/confrontacion.html`)

Cabecera «Resultado de la confrontación», subtítulo código · nombre del
borrador. En `RESULTADO`: tres tarjetas de métrica (Personas, Regla,
Ortografía) y las tablas actuales con chip de conteo; `details` de extracción
sin cambios de contenido. `NO_DISPONIBLE`, `ADVERTENCIA_CORRESPONDENCIA`,
`ERROR_SEGURO`: mismos textos y roles con la paleta. Sin contexto nuevo.
Tests: `tests/test_expedientes_confrontacion_ui.py`.

## Transversal

Ninguna plantilla contiene «IA», «AI» como palabra, ni nombres comerciales.
Tests: `tests/test_shell.py`.
