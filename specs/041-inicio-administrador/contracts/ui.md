# Contrato de interfaz: Inicio (`/`, vista `home`)

Métodos: `GET`/`HEAD` (sin cambios). Requiere sesión y rol Administrador o
Usuario (sin cambios).

## Administrador (`es_administrador`)

Contexto de plantilla:

- `cifras`: `{"notariales", "vehiculares", "total"}`
- `actividad`: 12 × `{"inicio", "kardex"}`
- `confrontaciones`: ≤ 5 × `{"expediente", "usuario", "fecha"}`
- `avisos`: lista de `Expediente`

Pantalla, en orden:

1. Avisos de documento ilegible (`core/_avisos_ilegibles.html`), solo si los hay.
2. Métricas: «Total» (no enlazada), «Kardex» → `expediente_lista`,
   «Transferencias vehiculares» → `vehicular_lista`.
3. «Actividad por semana»: `<ol aria-label="Kardex confrontados por semana,
   últimas 12 semanas">` con 12 `<li>`, cada uno con la cifra y la fecha
   `d/m` del lunes en texto.
4. «Últimas confrontaciones»: `<ul aria-label="Últimas confrontaciones">`,
   filas con código, chip de tipo, usuaria y `d/m/Y H:i`; cada fila enlaza a
   `expediente_detalle`. Estado vacío: «Aún no hay confrontaciones».

No aparecen: «Procesando», «Con error», «Requieren su atención», «Acceso
rápido», «Control administrativo», «Administrar usuarios».

## Usuario

Igual que hoy (métricas, «Últimos kardex», «Nueva confrontación»), salvo que:

- «Requieren su atención» desaparece;
- en su lugar, los avisos de `core/_avisos_ilegibles.html`, solo si los hay.

## Aviso de documento ilegible (los dos roles)

Por kardex: icono, código, texto «Un documento que usted subió no se pudo leer.
Elimínelo y vuelva a subirlo.» y botón «Abrir kardex» →
`expediente_detalle`. Sin nombre de archivo ni datos del documento.
