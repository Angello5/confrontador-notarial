# Research: F13 · Anclaje por ficha oficial

**Fuentes aprobadas (2026-09-25):** [spec.md](spec.md),
`docs/catalogo-datos.md` (orden de confianza) y `docs/catalogo-fuentes.md`.
Código leído: `nucleo/verificar.py` (F11/F12) y `expedientes/services.py`.

## Evidencia del código actual

- `catalogo()` recorre las páginas, llama a `_personas_de_pagina()` con el tipo
  de `clasificar_pagina()` y pasa **todos** los registros, de cualquier tipo, a
  `unificar_personas()`. Por eso una ficha, una declaración jurada y la prosa de
  la minuta compiten en pie de igualdad: el origen de las «tres filas por
  persona» del spec.
- `_personas_de_pagina()` ya distingue registro completo (nombre + documento,
  estado `CONFIRMADA`) de incompleto (`SIN_DOCUMENTO` o documento sin nombre en
  `REVISION_MANUAL`). F13 no toca esa extracción, salvo el cónyuge.
- En la declaración jurada, `_nombres_de_pagina()` mete al cónyuge en la misma
  lista que al declarante. Con dos nombres y un documento la página nunca da un
  registro completo: produce dos nombres sueltos y un documento suelto.
- La proyección `cat["NOMBRE"]`/`cat["DNI"]` se calcula desde
  `Catalogo.personas`. `revisar()`, `correspondencia()`, `diagnostico()`,
  `app.py` y `app_ortografia.py` solo usan esa proyección.
- `comparar_personas()` construye el lado del **borrador** con
  `catalogo(borrador)`. El borrador es prosa: con FR-001 literal no tendría
  ninguna persona y la regla de documento cruzado quedaría muda.
- `revisar_persona_ampliada()` ya exige `CONFIRMADA` con nombre y documento;
  recorre `cat.personas`, que pasarán a ser solo anclas.
- `unificar_personas()` marca `REVISION_MANUAL` en dos casos: conflicto de
  campos F12 al fusionar y mismo documento con nombres distintos. Hoy ambos
  saltan también entre ficha y prosa; con F13 solo pueden darse entre anclas.

## Decisiones

**D1. Ancla = registro completo de página RENIEC o BIOMETRICA.**
Motivo: FR-001 dice «con su documento» y SC-002/SC-003 exigen cero registros
incompletos presentados como persona. Una ficha que el OCR no leyó completa
(las 6 del Assumptions) produce **menciones**, no anclas. Es la condición que
ya usa `_anotar_reniec()`, así que SC-001 (≥ 49) conserva las mismas personas.

**D2. Adjunto = el mismo `Persona` de hoy, guardado dentro del ancla.**
`Persona` gana tres campos opcionales al final: `adjuntos`, `conyuge` y
`procedencia_conyuge`. Las posiciones F11/F12 no cambian. Un adjunto es el
registro no oficial tal como salió de su página (nombre, documento,
procedencias). No se fusiona con el ancla: el ancla conserva nombre, documento,
procedencias y campos F12 de sus fichas (FR-004), y el adjunto conserva su
propio origen para la tabla (FR-007).

**D3. Mención sin ficha = `Persona` en una ranura nueva `Catalogo.menciones`.**
Estado fijo `SIN_FICHA`. No es una entidad persistida (FR-009). Las menciones
se deduplican con `unificar_personas()` y después se fuerza `SIN_FICHA`, así
que nunca llevan `REVISION_MANUAL` (FR-004, SC-004).

**D4. Regla de pegado (FR-002/FR-003), en este orden:**

1. Registro con documento: se pega al ancla con ese documento si es **única**.
   Si no hay ancla, mención. Si hay dos anclas con ese documento (ya marcadas
   en revisión entre anclas), mención: no se elige por el usuario.
2. Registro sin documento y con nombre: se pega al ancla cuya
   `_nombre_clave()` coincide exactamente, si es única. Si no, mención.
3. Un registro con documento que no está en ninguna ancla **nunca** se pega
   por nombre: sería justo el cruce de identidades que F11 quiere detectar.

El pegado ocurre después de unificar las anclas entre sí, para que el
resultado no dependa del orden de las páginas.

**D5. Proyección (FR-008) desde todas las estructuras.**
`NOMBRE` = nombre y cónyuge de cada ancla, cada adjunto y cada mención;
`DNI` = documento de cada uno. Todo nombre o documento que hoy llega a la
proyección sigue llegando, venga de donde venga. La única diferencia posible
es una variante que hoy se perdía al fusionar y solo difiere en signos que
`_nombre_clave()` ignora; la prueba de paridad sobre fixtures ficticios
(SC-005) lo fija antes de tocar código.

**D6. Conflictos (FR-004/FR-005).** `unificar_personas()` no cambia para las
anclas: mismo documento y mismo nombre se unifican; documento distinto nunca;
mismo documento con nombre distinto queda en revisión (es un conflicto
**entre anclas**, permitido por FR-004). La regla de emisión más reciente de
F12 sigue igual porque solo RENIEC aporta campos F12 y RENIEC siempre es ancla.
Entre ancla y adjunto no hay comparación de campos: manda el ancla sin marca.

**D7. Cónyuge (FR-006).** En una página `DECLARACION_JURADA`,
`_personas_de_pagina()` saca de la lista de nombres el valor de
`NOMBRES Y APELLIDOS DEL CONYUGE` (en el bloque y en el recorrido por líneas) y
lo guarda en `conyuge`/`procedencia_conyuge` del registro del declarante.
Así el declarante suele quedar completo (un nombre, un documento) y se pega
por D4. Al pegarse, el ancla toma `conyuge` si aún no tiene; el adjunto
conserva el suyo. `unificar_personas()` solo fusiona dos menciones si sus
cónyuges no chocan, para no perder un nombre de la proyección.

**D8. `comparar_personas()`.** El lado del borrador recorre anclas, adjuntos
y menciones del catálogo del borrador (en la práctica, menciones). El lado de
las fuentes:

- `DOCUMENTO_CRUZADO`: titular = **ancla** única por nombre (Clarifications:
  las reglas por persona exigen ancla) y documento hallado presente en
  `fuente["DNI"]`.
- `DOCUMENTO_SIN_TITULAR`: documento hallado **ausente de** `fuente["DNI"]`.
  Si se usaran solo anclas, un compareciente sin ficha cuyo documento está en
  la minuta daría un aviso falso «no pertenece a una persona conocida».

**D9. Tabla.** `_personas_legibles()` recibe una secuencia de personas en vez
del catálogo y se usa dos veces: anclas y menciones. Cada ancla añade cónyuge
con procedencia y sus adjuntos con procedencia. El sondeo JSON no cambia.

## Consecuencias que el propietario debe conocer

- Dos comparecientes **sin ficha** con los documentos intercambiados dejan de
  dar `DOCUMENTO_CRUZADO`; la capa de campos no lo ve porque ambos documentos
  están en las fuentes. Es lo que dice la Clarification, pero rompe el
  escenario de F11 US1 cuando no hay fichas. La prueba F11 se reescribe con
  fichas ficticias.
- El expediente de referencia (8 de 8, 0 falsos positivos; Constitución II/III)
  debe medirse antes y después: si alguno de los 8 errores se detectaba por un
  titular de prosa, F13 lo perdería.

## Aclaraciones pendientes

- [NEEDS CLARIFICATION] Cónyuge de una declaración jurada cuyo declarante no
  queda identificado (cero o varios nombres, o no se pega a ningún ancla).
  Por defecto propuesto: queda en la mención del declarante o, si no hay
  declarante, como mención propia; nunca se descarta, porque FR-008 exige que
  siga en la proyección.
- [NEEDS CLARIFICATION] Dos declaraciones juradas pegadas al mismo ancla con
  cónyuges distintos. FR-004 prohíbe marcar revisión fuera de las anclas. Por
  defecto propuesto: el ancla muestra el primero por orden de página y cada
  adjunto muestra el suyo, sin marca.

## Deuda deliberada

Mostrar el tipo de página en la procedencia (hoy `Procedencia` no lo lleva);
agrupar adjuntos repetidos del mismo ancla; las 6 fichas incompletas por OCR;
ocupación de la declaración jurada; personas jurídicas.
