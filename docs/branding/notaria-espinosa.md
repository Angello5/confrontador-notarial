# Notaría Espinosa: guía de marca para UI

Extraída de https://www.notariaespinosa.com (Inicio, Nosotros, Servicios) el
2026-10-01. Los valores vienen del CSS computado y del tema Wix del sitio
(`--color_*`, `--font_*`, `--wst-*`), no de capturas a ojo. Los tokens listos
para usar están en [`tokens.css`](tokens.css) y el tablero visual en
[`brand-board.html`](brand-board.html).

---

## 1. Personalidad

| Atributo | Cómo se expresa en el sitio |
|---|---|
| **Confiable / institucional** | Azul marino profundo como color dominante; tipografía geométrica firme; esquinas rectas. |
| **Moderna / tecnológica** | Verde menta como acento; degradado marino→verde; ilustraciones vectoriales planas. El texto de Nosotros destaca "tecnología informática de última generación". |
| **Cercana** | Tuteo ("Contáctanos", "a tu Medida", "No te preocupes"), WhatsApp siempre visible. |
| **Ágil** | Valores declarados: *Experiencia · Servicio personalizado · Responsabilidad · Agilidad & eficiencia*. |

Mensajes clave: **seguridad, confianza, agilidad, servicio a la medida.**

---

## 2. Logotipo

- **Composición:** isotipo "E" a la izquierda + logotipo en dos líneas:
  `NOTARÍA` (pequeño, ~38 % de la altura de la segunda línea) sobre `ESPINOSA` (grande, bold).
- **Tipografía del logotipo:** sans geométrica bold, mayúsculas, tracking ajustado.
- **Color del texto:** marino `#0F2765`.
- **Isotipo "E":** una E construida con bloques y un corte diagonal, rellena con
  un **degradado diagonal 135°** (de arriba-izquierda hacia abajo-derecha):

  ```
  #48E4A6 → #44D880 → #1AA36A → #01835D → #0F6568 → #2C2E80
  menta     verde      esmeralda  bosque     petróleo  índigo
  ```
- **Archivo fuente:** PNG con transparencia, 800×181 px
  (`static.wixstatic.com/media/18564c_ecd10b3456db4f41bae8dcc17765985a~mv2.png`).
  Proporción ≈ **4,4 : 1**. Se muestra a 555×125 px en el header de escritorio.
- **No hay versión vectorial publicada** ni versión en negativo. Para fondos
  oscuros, pedir a la notaría un SVG o usar el isotipo solo sobre blanco.

**Reglas**
- Fondo: blanco o `#EDEFF8`. No ponerlo sobre el degradado ni sobre fotos.
- Zona de respeto: la altura de la palabra `NOTARÍA` alrededor de todo el logo.
- Tamaño mínimo: 140 px de ancho (pantalla). Por debajo, usar solo el isotipo "E" (favicon, avatar, sidebar colapsada).
- No recolorear la E en plano ni cambiar el ángulo del degradado.

---

## 3. Color

### 3.1 Paleta núcleo

| Token | HEX | RGB | Rol en el sitio | Rol Wix |
|---|---|---|---|---|
| `--ne-navy` | **`#0F2765`** | 15 39 101 | Títulos, texto principal, topbar, botón "Ver más servicios", bordes de inputs | `text-primary`, `title`, `subtitle`, `fill-base-2` |
| `--ne-ink` | **`#00112C`** | 0 17 44 | Texto sobre verde, botones oscuros, panel de contacto, inicio del degradado | `fill-accent-2` |
| `--ne-green` | **`#44D880`** | 68 216 128 | Acento/acción: CTA, nav activo, botón Send | `action`, `fill-accent-1`, botón primario |
| `--ne-slate` | **`#4B5D8C`** | 75 93 140 | Texto secundario, nav inactivo, líneas | `text-secondary`, `line`, `fill-base-shade-3` |
| `--ne-white` | **`#FFFFFF`** | 255 255 255 | Fondo principal | `background-primary` |

### 3.2 Escala de marino (fríos neutros)

| Token | HEX | Uso |
|---|---|---|
| `--ne-navy-50` | `#EDEFF8` | Fondo de banda/sección alterna (≈ `#B3BFE7` al 30 % sobre blanco = `#E8EBF7`) |
| `--ne-navy-100` | `#C3C9D9` | Fondo de tarjeta de servicio (al 80 % = `#CFD3E0`), bordes suaves |
| `--ne-navy-200` | `#B3BFE7` | Tinte lavanda (bandas) |
| `--ne-navy-300` | `#8999D0` | Acento frío decorativo |
| `--ne-navy-400` | `#8793B2` | Borde superior del footer, deshabilitados |
| `--ne-navy-500` | `#4B5D8C` | Texto secundario |
| `--ne-navy-600` | `#273B7B` | Hover de marino |
| `--ne-navy-700` | `#0F2765` | **Marca** |
| `--ne-navy-800` | `#141D3D` | Superficies muy oscuras |
| `--ne-navy-900` | `#00112C` | Tinta |

### 3.3 Escala de verde

| Token | HEX | Uso |
|---|---|---|
| `--ne-green-50` | `#E5FAED` | Fondo de estado "correcto" |
| `--ne-green-100` | `#C5FFCF` | Tinte menta (Wix `fill-accent-3`) |
| `--ne-green-300` | `#6AE29A` | Hover de botón verde |
| `--ne-green-400` | `#48E4A6` | Inicio del degradado del isotipo |
| `--ne-green-500` | `#44D880` | **Marca / acción** |
| `--ne-green-700` | `#01835D` | Verde para **texto** sobre blanco (4,77:1, AA) |
| `--ne-green-800` | `#0F6568` | Petróleo (degradado) |

### 3.4 Degradados

```css
/* Banda "Nuestros clientes corporativos" (valor exacto del sitio) */
--ne-gradient-band: linear-gradient(110deg, #00112C 12%, #0F2765 30%, #44D880 80%);

/* Isotipo E (aproximado por muestreo de píxeles) */
--ne-gradient-mark: linear-gradient(135deg, #48E4A6 0%, #44D880 15%, #1AA36A 45%,
                                    #01835D 62%, #0F6568 78%, #2C2E80 100%);
```

Úsalos con moderación: una banda por página como máximo, o como acento (barra
de 4 px, avatar, ilustración). Nunca detrás de texto pequeño.

### 3.5 Proporción de uso

Aproximadamente **60 % blanco / tintes fríos · 30 % marino · 10 % verde**. El
verde es acción y estado activo; no se usa en bloques grandes salvo en la banda
degradada.

### 3.6 Contraste (WCAG 2.1)

| Combinación | Ratio | Veredicto |
|---|---|---|
| `#0F2765` sobre blanco | 14,0 : 1 | AAA |
| `#00112C` sobre blanco | 18,8 : 1 | AAA |
| `#4B5D8C` sobre blanco | 6,5 : 1 | AA (texto normal) |
| `#8793B2` sobre blanco | 3,1 : 1 | Solo texto ≥ 24 px o iconos |
| `#44D880` sobre `#00112C` | 10,2 : 1 | AAA (CTA "Contáctanos") |
| `#44D880` sobre `#0F2765` | 7,6 : 1 | AAA (verde sobre marino) |
| **Blanco sobre `#44D880`** | **1,85 : 1** | **No pasa.** El sitio lo usa en "Ver más"; en nuestra UI, texto `#00112C` sobre verde |
| `#01835D` sobre blanco | 4,8 : 1 | AA. Usar este cuando el verde sea texto |

Hay colores del tema Wix que el sitio no usa (rojo `#ED1C24`, azul `#0088CB`,
amarillo `#FFCB05`, rampas burdeos y celeste). Son restos de la plantilla y no
forman parte de la marca. Para estados de error/aviso de la app, ver §8.

---

## 4. Tipografía

### 4.1 Familias

| Rol | Fuente del sitio | Sustituto libre recomendado | Notas |
|---|---|---|---|
| **Display / títulos** | **Prompt** (Google Fonts) | la misma | Sans geométrica tailandesa-latina, aperturas amplias. Pesos 400 y 700. |
| **Texto / UI** | **Avenir LT 35 Light** (licencia Linotype) | **Nunito Sans** 300/400 (o Figtree) | Avenir no es libre; si hay licencia, usarla. |
| **Énfasis / botones** | **Avenir LT 85 Heavy** | **Nunito Sans** 800 | Botones CTA y etiquetas de valores en mayúsculas. |
| **Etiquetas pequeñas** | **Poppins SemiBold** | la misma | Solo en la topbar ("E-mail:", "Teléfonos:"). |

Pila CSS:

```css
--ne-font-display: "Prompt", "Poppins", system-ui, sans-serif;
--ne-font-body: "Avenir LT W01 35 Light", "Avenir Next", "Avenir", "Nunito Sans", system-ui, sans-serif;
--ne-font-label: "Poppins", "Prompt", system-ui, sans-serif;
```

### 4.2 Escala observada en el sitio

| Estilo | Fuente | Tamaño / interlínea | Peso | Tracking | Ejemplo |
|---|---|---|---|---|---|
| Display XL (tema `font_3`) | Prompt | 90 / 1.4 | 400 | 0 | (reservado) |
| **Hero H1** | Prompt | **57 / 1.4** | **700** | 0 | "Servicios Notariales a tu Medida" (blanco sobre oscuro) |
| **Título de sección H2** | Prompt | **56 / 1.4** | 400 | 0 | "Servicios Recurrentes" (centrado) |
| Título de página | Prompt | 40 | 700 | 0.07em | "Notaría Espinosa" |
| Subtítulo H3 | Prompt | 38 / 1.4 | 400 | 0 | "¿Porqué elegirnos?" |
| Título de banda | Prompt | 33 / 1.4 | 400 | 0 | "Nuestros clientes corporativos" |
| **Título de bloque** | Prompt | **30** | **700** | **0.07em** | "Compra o Vende tu Auto…" |
| **Lead / intro** | Prompt | **20** | 400 | **0.07em** | párrafo de bienvenida |
| **Título de tarjeta** | Prompt | **20 / 28** | **700** | 0 | "Escrituras Públicas" |
| Etiqueta de valor | Avenir Heavy | 20 | 800 | **0.2em**, MAYÚS | "RESPONSABILIDAD" |
| Body L | Avenir Light | 18 / 25 | 400–700 | 0 | texto de bloque |
| **Body** | Avenir Light | **16 / 24** | 400 | 0 | descripción de tarjeta |
| Nav | Avenir Light | 16 / 27 | 400 | 0 | Inicio · Nosotros… |
| Body S / inputs / footer | Avenir Light | 14 | 400 | 0 | formularios, © |
| Topbar label | Poppins SemiBold | 13 | 600 | 0.01em | "Horarios de atención:" |
| Topbar valor | Avenir Light | 13 / 1.3 | 400 | 0 | "L-V de 9:00 am a 6:45 pm" |

### 4.3 Escala para la app (derivada, más compacta)

Las pantallas del sitio son de marketing; una herramienta de trabajo necesita
una escala más baja. Se mantiene la jerarquía (Prompt en títulos, Avenir/Nunito
en todo lo demás):

| Token | Tamaño / interlínea | Fuente · peso |
|---|---|---|
| `--ne-text-display` | 40 / 48 | Prompt 700 |
| `--ne-text-h1` | 30 / 38 | Prompt 700, +0.02em |
| `--ne-text-h2` | 24 / 32 | Prompt 400 |
| `--ne-text-h3` | 20 / 28 | Prompt 700 |
| `--ne-text-lead` | 18 / 28 | Prompt 400, +0.03em |
| `--ne-text-body` | 16 / 24 | Body 400 |
| `--ne-text-sm` | 14 / 20 | Body 400 |
| `--ne-text-xs` | 12 / 16 | Body 600, MAYÚS, +0.08em (cabeceras de tabla, overlines) |

**Reglas**
- Títulos en *Title Case* español como en el sitio ("Servicios Notariales a tu
  Medida"), o en oración en la app. No mezclar en la misma vista.
- Mayúsculas espaciadas (0.1–0.2em) solo para etiquetas cortas y botones CTA.
- El color de texto por defecto es marino `#0F2765`, no negro.

---

## 5. Forma, espacio y elevación

| Propiedad | Valor en el sitio | Recomendación app |
|---|---|---|
| **Radio** | **0** en botones, tarjetas, inputs, paneles | `0`–`2px`. La marca es **rectilínea**; no usar pills ni tarjetas muy redondeadas. Excepción: avatares/insignias circulares. |
| **Sombras** | Ninguna (solo el hero tiene `0 1px 3px rgba(0,0,0,.5)`) | Plano. Separar con color de fondo (`navy-50`, `navy-100`) o borde 1px `#C3C9D9`. Sombra solo en overlays: `0 8px 24px rgba(0,17,44,.16)`. |
| **Bordes** | 1px `#0F2765` (inputs), 1px `#8793B2` (footer) | Inputs 1px marino; divisores 1px `#C3C9D9`. |
| **Contenedor** | ≈ 1100–1180 px centrado; secciones a ancho completo | `max-width: 1200px`, gutter 24px (16px en móvil). |
| **Ritmo vertical** | Secciones de ~430–540 px, padding ~90–120 px | Base 8 px: 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96. |
| **Grillas** | 2 columnas de tarjetas (gap ~40 px); 4 columnas en Servicios; contacto 1/3 + 2/3 | 12 columnas; tarjetas 2/3/4 por fila. |
| **Movimiento** | `transition: background-color .4s, border-color .4s` y `.2s` en botones | 150–250 ms `ease-out` en hover/focus; nada de rebotes. |

---

## 6. Componentes

### 6.1 Topbar de contacto
- Fondo `#0F2765`, alto 105 px (escritorio), texto blanco.
- 4 columnas: **E-mail · Teléfonos · Dirección · Horarios de atención**.
  Etiqueta (Poppins SemiBold 13) arriba; valor (Avenir Light 13–14) con icono de línea blanco 16 px a la izquierda.
- A la derecha, botón WhatsApp verde con radio completo (único elemento redondeado de la marca).

### 6.2 Header / navegación
- Fondo blanco, alto ~153 px, logo a la izquierda (555 px), menú a la derecha.
- Ítems: Avenir 16, color `#4B5D8C`; **activo = `#44D880`**; hover → `#4B5D8C` (Wix `color_14`), transición .4s.
- Sin subrayado, sin indicador de barra: solo cambio de color.
- **Para la app:** mantener blanco + logo, pero el verde activo como texto no
  llega a contraste (1,85:1). Usar texto marino 700 + **barra inferior/izquierda de 3 px verde**.

### 6.3 Botones (todos con radio 0)

| Variante | Fondo | Texto | Tipografía | Tamaño | Uso |
|---|---|---|---|---|---|
| **Primario verde (CTA)** | `#44D880` | `#00112C` | Avenir Heavy 22, +0.1em | 220×57 | "Contáctanos" en hero |
| **Marino** | `#0F2765` | blanco | Avenir Heavy 18, +0.1em | 283×59 | "Ver más servicios" |
| **Tinta** | `#00112C` | blanco | Avenir Light 17 | 146×41 | "Saber más", "Contacto" |
| **Verde pequeño** | `#44D880` | ~~blanco~~ → **`#00112C`** | Avenir 14 | 142×40 | "Ver más" en tarjetas |
| **Submit** | `#44D880` + borde 1px igual | `#00112C` | Avenir 14 | ancho completo × 36 | formularios |

Hover: aclarar el verde a `#6AE29A`; el marino pasa a `#273B7B`. Foco: anillo
3 px `#44D880` con 2 px de separación (ya está así en `erp.css`).

### 6.4 Tarjeta de servicio
- Fondo `#CFD3E0` (`#C3C9D9` al 80 %), sin borde, sin sombra, sin radio.
- Ilustración/icono a la izquierda (~40 %), a la derecha título Prompt 20/700
  marino, descripción Avenir 16/24 marino y botón verde pequeño abajo.
- Variante "catálogo" (página Servicios): panel gris `#CFD3E0` que contiene
  4 tarjetas: ilustración arriba sobre el gris y **rótulo en caja blanca** con Prompt 20 centrado.

### 6.5 Bloque destacado (texto + ilustración)
- Banda de ancho completo con fondo `#E8EBF7`.
- Título Prompt 30/700 con +0.07em, cuerpo Avenir 18, botón "Saber más" tinta.
- Ilustración a la derecha sobre círculo verde.

### 6.6 Banda degradada
- `--ne-gradient-band`, alto ~330 px, título Prompt 33 blanco centrado y fila
  de logos de clientes en blanco/monocromo.

### 6.7 Formulario de contacto
- Layout 1/3 + 2/3: panel izquierdo `#00112C` con "Contáctanos" (Prompt 26–33
  blanco) y datos de contacto; formulario a la derecha sobre blanco.
- Label Avenir 14 marino **encima** del campo; input blanco, borde 1px `#0F2765`,
  radio 0, alto 36–37 px, texto marino 14.
- Submit verde a todo el ancho.
- El sitio deja los labels en inglés ("First Name", "Send"): **en la app, todo en español.**

### 6.8 Encabezado de página interna
- Foto oscurecida a ancho completo (~250 px de alto) con título en MAYÚSCULAS
  blanco espaciado ("SOBRE NOSOTROS").

### 6.9 Footer
- Fondo `#EDEEF3`, borde superior 1px `#8793B2`, alto ~160 px.
- "© 2025 Notaría Espinosa, San Isidro, Lima, Perú." Avenir 14 marino + iconos
  sociales (Facebook, X, LinkedIn) 30 px.

### 6.10 Widget de WhatsApp
Es de terceros (certifiedcode.io) con sus propios verdes (`#15E18C`,
`#2BEB9B`) y radios redondeados. **No es marca**: no copiar esos valores.

---

## 7. Iconografía e ilustración

- **Iconos de servicio:** estilo "sticker". Contorno marino grueso (~4–6 % del
  tamaño), rellenos verde menta `#44D880`/`#6AE29A` y gris claro; esquinas
  ligeramente redondeadas; sin degradados. Temas: documentos, sobres, sellos,
  llaves, autos, pasaporte/boleto, portapapeles con checks, cronómetro.
- **Iconos de UI:** de línea, 1.5–2 px, monocromos (blanco en topbar, marino en
  contenido). Recomendado: Lucide, Phosphor (regular) o Tabler.
- **Ilustraciones de escena:** vector plano, personajes con traje marino,
  piel/cabello naturales, fondo de **círculo verde** detrás del grupo, toques
  de blanco y gris. Mismos dos colores dominantes que la marca.
- **Patrón:** líneas blancas finas geométricas (hexágonos/isométrico) sobre
  marino oscuro, en el hero, como textura de fondo.
- **Fotografía:** retrato formal del notario (fondo de biblioteca) y fotos
  urbanas oscurecidas con overlay marino para encabezados.

---

## 8. Estados para la app (extensión de marca)

La marca no define estados de error/aviso; estos valores encajan con la
paleta fría y cumplen AA:

| Estado | Fondo | Borde/acento | Texto |
|---|---|---|---|
| Éxito / coincide | `#E5FAED` | `#44D880` | `#0F5132` |
| Información | `#EDEFF8` | `#4B5D8C` | `#0F2765` |
| Aviso / revisar | `#FFF6DB` | `#E0A400` | `#5C4200` |
| Error / discrepancia | `#FDECEE` | `#C8283C` | `#8B1C28` |

El rojo deriva de la rampa burdeos del tema Wix (`#D12A3C`, `#8B1C28`) para no
introducir un tono ajeno.

---

## 9. Voz y tono

- **Tratamiento:** tú (tuteo), cálido pero formal en el fondo.
  "Contáctanos", "No te preocupes, en Notaría Espinosa estamos para ayudarte".
- **Verbos de acción en botones:** Contáctanos · Saber más · Ver más · Ver más servicios.
- **Vocabulario:** seguridad, confianza, agilidad, transparencia, sin complicaciones, a tu medida.
- **Datos institucionales:** "Aldo Espinosa Oré, Notario de Lima, R.M. N° 2009-2004-JUS".
  Las Camelias 162, San Isidro, Lima · 01 719 3975 · informes@notariaespinosa.com · L-V 9:00–18:45.
- Corregir en nuestra UI: "¿Porqué elegirnos?" → "¿Por qué elegirnos?"; labels en inglés → español.

---

## 10. Aplicación al Confrontador (`static/css/erp.css`)

`erp.css` ya usa `#0F2765`, `#44D880`, `#00112C` y `#C3C9D9`, así que va en la
línea de la marca. Lo que falta para alinearlo del todo:

1. **Tipografía:** hoy es `system-ui`. Cargar Prompt (títulos) y Nunito Sans o
   Avenir (cuerpo) y asignarlas con `--bs-body-font-family` y `h1–h6`.
2. **Radio:** `--bs-border-radius: 0.5rem` → `2px` (o `0`) para la estética rectilínea.
3. **Fondo de app:** `#F2F3F7` es correcto; la marca usaría `#EDEFF8` (tinte lavanda), más fiel a la paleta.
4. **Texto secundario:** `#5C6470` es gris neutro; la marca usa `#4B5D8C`
   (marino desaturado, 6,5:1 sobre blanco). Cambiarlo para que no se vea gris.
5. **Botón verde:** texto `#0F2765` está bien; la marca usa `#00112C` y
   Avenir Heavy con +0.1em en CTAs.
6. **Sidebar/topbar:** marino `#0F2765` con ítem activo en verde (barra +
   icono verde, texto blanco) replica el header/topbar del sitio.
7. **Una sola** banda con `--ne-gradient-band` (p. ej. cabecera del dashboard o pantalla de login).

Todos los valores están en [`tokens.css`](tokens.css).
