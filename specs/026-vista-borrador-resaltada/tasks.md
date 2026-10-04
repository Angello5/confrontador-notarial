# Tasks: F32 · Vista del borrador con errores resaltados

**Input**: `specs/026-vista-borrador-resaltada/` (plan.md, spec.md, research.md, data-model.md, contracts/vista-borrador.md, quickstart.md)

**Tests**: obligatorios en el núcleo (constitución III): cada regla empieza con un test que falla. Solo datos ficticios.

**Tramos**: A = US1 + US3 (`.docx`, ya permitido por la constitución 1.7.0). B = US2 (escaneados y demás formatos), **BLOQUEADO** hasta que la constitución 1.8.0 esté aprobada por la notaría e integrada en `main`.

## Phase 1: Setup

- [X] T001 Comprobar que `soffice` y `pymupdf==1.28.2` están disponibles en el entorno de pruebas local (runtime de auditoría) y anotar en `specs/026-vista-borrador-resaltada/quickstart.md` cualquier paso extra

## Phase 2: Foundational (bloquea US1 y US3)

- [X] T002 [P] Tests que fallan para `marcas(segmentos, valor)` en `tests/test_ubicacion_pagina.py`. Casos: valor en un segmento; valor partido en dos segmentos de la misma línea; valor que cruza dos líneas (dos rectángulos, misma `aparicion`); dos apariciones (`aparicion` 0 y 1); valor dentro de una palabra (bordes por proporción de caracteres, dentro del segmento); tildes y mayúsculas (`"Pérez"` contra `"PEREZ"`); valor ausente (lista vacía); valor vacío (lista vacía); determinismo (dos llamadas dan el mismo resultado)
- [X] T003 Implementar en `nucleo/correccion.py` la función `marcas(segmentos, valor) -> list[dict]`. Reglas: segmentos `(texto, x0, y0, x1, y1, linea)` con "`0 ≤ x0 < x1 ≤ 1`"; une segmentos de la misma línea con espacio y líneas con `\n`; busca con `nucleo.correccion.coincidencias`; devuelve `{x0, y0, x1, y1, aparicion}` en fracciones de página, dentro del segmento de origen. Sin importar Django, PyMuPDF ni el sistema de archivos
- [X] T004 [P] Test que falla en `tests/test_paginas_adaptador.py`: un `.docx` ficticio de dos páginas, generado en el test y con un DNI ficticio en la página 2, se convierte a PDF, y `segmentos(pdf, 2)` contiene ese DNI con coordenadas en [0, 1]; `png(pdf, 1)` empieza con la firma PNG. Marcar con `skipif` si no hay `soffice`
- [X] T005 Permitir `.docx` en `_soffice` de `adaptadores/extraccion.py` sin cambiar el comportamiento de `_legacy` (validación de sufijos propia de la conversión a PDF)
- [X] T006 Implementar `adaptadores/paginas.py`: `a_pdf(original, destino)` (vía `_soffice`, formato `pdf`), `paginas(pdf) -> list[{numero, proporcion}]`, `segmentos(pdf, n)` (con `page.get_text("words")`, `linea` = índice de `(bloque, línea)`, coordenadas divididas por el ancho y el alto de la página) y `png(pdf, n)` (110 ppp). Los errores no llevan rutas
- [X] T007 Funciones de ruta y borrado de la caché de vista en `expedientes/services.py`: `ruta_vista(documento)` → `EXPEDIENTES_TEMP_DIR / f"vista-{expediente_id}-{documento_id}-{hash_archivo[:16]}.pdf"` y `borrar_vistas(expediente_id, documento_id=None)`. Llamar a `borrar_vistas` desde `eliminar_documento`, con un test en `tests/test_vista_borrador.py`

**Checkpoint**: el núcleo y el adaptador pasan sus tests; aún no hay interfaz.

## Phase 3: User Story 1 · Borrador `.docx` con errores marcados (P1) 🎯 MVP

**Goal**: la pantalla de resultado muestra las páginas del `.docx` con recuadros rojo, amarillo y neutro, enlazados con la lista.

**Independent Test**: borrador `.docx` ficticio con un DNI erróneo (alta), un monto distinto (media) y una errata (baja). Los tres recuadros aparecen en su página y con su color; elegir en la lista lleva al recuadro y el clic en el recuadro selecciona la observación.

- [X] T008 [P] [US1] Tests que fallan para `vista_borrador(expediente, borrador, corrida)` en `tests/test_vista_borrador.py`. Casos:
  - `estado` `LISTA` con `marcas["r1"]` en la página correcta.
  - Identificadores `p<n>`, `r<n>` y `o<n>` en el mismo orden que la plantilla.
  - SHA-256 distinto del original → `NO_DISPONIBLE`/`VERIFICACION`.
  - Sin original → `SIN_ORIGINAL`.
  - Borrador no `.docx` → `FORMATO`.
  - La segunda llamada reutiliza la caché (no reconvierte).
- [X] T009 [US1] Implementar `vista_borrador` en `expedientes/services.py`:
  - Verifica el SHA-256 del original contra `Documento.hash_archivo`.
  - Convierte a la caché `ruta_vista` escribiendo en un temporal y renombrando de forma atómica.
  - Toma `resultado_de_corrida(corrida)` y recorre `personas` (valor `hallado`), `regla` (`hallado`) y `ortografia` (`palabra`).
  - Las observaciones con `ubicacion.linea` nula van a `no_ubicadas` con `AUSENTE`; las demás se buscan con `marcas` página a página, y si no hay rectángulos van a `no_ubicadas` con `NO_EN_PAGINA`.
  - Devuelve la estructura de `data-model.md` ("Vista del borrador").
- [X] T010 [P] [US1] Tests que fallan para las vistas en `tests/test_vista_borrador.py`, según `contracts/vista-borrador.md`:
  - Sin sesión: 302. Sin rol: 403.
  - 404 con otro expediente, con otro documento, con un documento que no es borrador, sin `?corrida` y con una corrida ajena.
  - JSON con `Cache-Control: no-store`. PNG `image/png`, también `no-store`.
  - 404 si la página está fuera de rango.
  - Ningún campo del JSON contiene la ruta de originales ni de temporales.
- [X] T011 [US1] Implementar `documento_vista` (JSON) y `documento_vista_pagina` (PNG) en `expedientes/views.py`, delgadas, con `login_required`, `require_GET`, `_requiere_rol` y `_expediente_visible`. Añadir las cabeceras `Cache-Control: no-store` y `X-Content-Type-Options: nosniff`, y registrar las rutas `<int:pk>/documentos/<int:doc_id>/vista/` y `.../vista/<int:n>/` en `expedientes/urls.py`
- [X] T012 [US1] Crear `templates/expedientes/_vista_borrador.html`:
  - Panel "Borrador" con la leyenda de colores, los estados "Preparando la vista del borrador…" y "Cargando página X de N", y el aviso de `NO_DISPONIBLE` con el texto de `contracts/vista-borrador.md`.
  - Una figura por página con `<img loading="lazy">` y un `alt` del tipo "Página X del borrador".
  - Un `<button class="marca-pagina" data-obs data-sev>` por rectángulo, posicionado en %, con `aria-label`.
  - Controles de zoom (ajustar a ancho / ampliar).
- [X] T013 [US1] Integrar el visor en `templates/expedientes/confrontacion.html`:
  - Incluir `_vista_borrador.html` y, en `revisionConfrontacion`, pedir el JSON con `fetch` usando `resultado.corrida_id`.
  - `elegir(id)` desplaza a la primera aparición y la destaca; el clic o Enter en una marca llama a `elegir`; Avance y Retroceso de página cambian de página.
  - Las marcas obedecen `visible()` (filtros de capa y severidad).
  - Si no hay `corrida_id`, mostrar el aviso `CORRIDA`.
- [X] T014 [P] [US1] Estilos en `static/css/erp.css`:
  - `.marca-pagina[data-sev="ALTA"]` rojo con borde continuo, `MEDIA` ámbar con borde discontinuo y `BAJA` neutro con borde punteado, con relleno translúcido.
  - Estado seleccionado con contorno grueso y `:focus-visible`.
  - Leyenda, contenedor de página con `aspect-ratio` según `proporcion` y modo impresión que oculta el visor.
- [X] T015 [US1] Test de plantilla en `tests/test_vista_borrador.py`: la página de resultado contiene el panel del visor, la URL de la vista con `?corrida=` y la leyenda "Severidad alta / media / baja"

**Checkpoint**: US1 verificable en el navegador con datos ficticios (quickstart, prueba manual 1–4).

## Phase 4: User Story 3 · Observaciones no ubicadas (P3)

**Goal**: las observaciones sin sitio en la página se indican y se cuentan.

**Independent Test**: una minuta ficticia con un párrafo ausente del borrador produce "No ubicada en el borrador" y aumenta el contador.

- [X] T016 [P] [US3] Test que falla en `tests/test_vista_borrador.py`: una observación de párrafo ausente (`ubicacion.linea` nula) aparece en `no_ubicadas` con `AUSENTE` y sin `marcas`; un valor con línea pero partido por un guion de corte aparece con `NO_EN_PAGINA`
- [X] T017 [US3] En `templates/expedientes/_vista_borrador.html` y `confrontacion.html`: contador "N observaciones no marcadas en las páginas". Al elegir una no ubicada, la vista no cambia de página y el detalle muestra el texto de `contracts/vista-borrador.md` según el motivo

**Checkpoint**: Tramo A completo.

## Phase 5: User Story 2 · Borrador escaneado (P2) ⛔ BLOQUEADO

**Bloqueo**: no empezar hasta que la constitución 1.8.0 (principio IV, conservación del borrador en cualquier formato) esté aprobada por la notaría e integrada en `main`. Hasta entonces, los borradores no `.docx` responden `FORMATO`.

- [ ] T018 [US2] Tests que fallan en `tests/test_expedientes_services.py`: `registrar_documento` conserva el borrador en cualquier formato admitido como `original<sufijo>`, con permisos `0o400`; los documentos del cliente y la minuta siguen sin conservarse
- [ ] T019 [US2] Generalizar `ruta_original` y `_conservar_original` en `expedientes/services.py` para conservar `original<sufijo>` de todo borrador, y adaptar `aplicar_correcciones`, que sigue exigiendo `.docx` para corregir
- [ ] T020 [P] [US2] Test que falla en `tests/test_calidad_ocr.py` (o el test existente de `calidad_ocr`): `ordenar_filas(cajas, angulo, tol)` reproduce exactamente el `texto` de `resumir()` con cajas ficticias horizontales e inclinadas
- [ ] T021 [US2] Extraer `ordenar_filas` de `resumir()` en `adaptadores/calidad_ocr.py` sin cambiar `VERSION` ni el texto producido
- [ ] T022 [US2] Test que falla y luego implementación de `segmentos_ocr(calidad_pagina)` en `adaptadores/paginas.py`: pasa `cajas` a segmentos en fracciones usando `dimensiones` (o 200 ppp sobre el tamaño de la página) y conserva `transformacion.giro` para mostrar la página con ese giro
- [ ] T023 [US2] Ampliar `vista_borrador` y `png` para borradores PDF (páginas `texto_pdf` con palabras de PyMuPDF; páginas `ocr` con `segmentos_ocr`), imágenes (la propia imagen como página) y `.doc`/`.rtf`/`.odt` (vía `a_pdf`), con tests en `tests/test_vista_borrador.py` que usen un PDF escaneado ficticio
- [ ] T024 [US2] Mostrar junto a la página el aviso de lectura dudosa de F31 cuando la página tenga `requiere_revision`, en `templates/expedientes/_vista_borrador.html`

## Phase 6: Polish & Cross-Cutting

- [X] T025 Borrar la caché de vista en `expedientes/management/commands/suprimir_texto_expediente.py` (`borrar_vistas(expediente.pk)`), con un test en `tests/test_expedientes_commands.py`
- [X] T026 [P] Actualizar `spec.md` (Status) y `docs/roadmap.md` (F32 en curso o terminada), y documentar en `specs/026-vista-borrador-resaltada/quickstart.md` los resultados de la verificación
- [X] T027 Ejecutar `ruff check .`, `ruff format --check .` y la suite completa con cobertura; revisar que el diff no contiene datos reales ni secretos
- [ ] T028 Verificación en el navegador con datos ficticios (quickstart, prueba manual) y revisión contra las 10 heurísticas de Nielsen. Hecho: navegador con datos ficticios (ver quickstart). Pendiente: severidad media en pantalla, revisión de las 10 heurísticas con un digitador y medición del 95 % de SC-001 con el conjunto ficticio de referencia

## Dependencies & Execution Order

- Phase 1 → Phase 2 → US1 (Phase 3) → US3 (Phase 4) → Polish.
- T003 depende de T002; T005 y T006 dependen de T004; T009 depende de T003, T006 y T007; T011 depende de T009; T013 depende de T011 y T012.
- US3 usa el servicio de US1 (T009) pero se prueba por separado.
- US2 (Phase 5) depende de la aprobación de la constitución 1.8.0 y de US1.

## Parallel Opportunities

- T002 y T004 (tests de núcleo y adaptador, archivos distintos).
- T008 y T010 (tests de servicio y de vistas) mientras se implementa T006.
- T014 (CSS) en paralelo con T011 y T012.

## Implementation Strategy

MVP = Phase 1 + Phase 2 + US1. Después, US3, que es poco trabajo y completa el Tramo A. US2 entra como incremento cuando se apruebe la enmienda.

## Notas de implementación (2026-10-02)

- T009: la conversión con LibreOffice no ocurre en la petición. La vista deja un `.pedido` y el worker lo convierte con `preparar_vistas()` (véase `research.md` R5, revisado tras medir de 12 a más de 120 s por conversión).
- T007/T025: `borrar_vistas` se llama desde `borrar_originales`, que ya usan `eliminar_documento` y `suprimir_texto_expediente`; no hizo falta tocar el comando.
- E1/E2 (de `/speckit-analyze`): botones «aparición anterior/siguiente» y ciclo entre observaciones solapadas en `confrontacion.html`.
- `tests/conftest.py` lista los módulos productivos esperados en la cobertura: se añadió `adaptadores/paginas.py`. `marcas` vive en `nucleo/correccion.py` porque `test_nucleo_puro` prohíbe que los módulos del núcleo se importen entre sí.
