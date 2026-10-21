# Feature Specification: F53 · Inicio del administrador

**Feature Branch**: `041-inicio-administrador`

**Created**: 2026-10-18

**Status**: US1–US3 implementadas; US4–US5 añadidas el 2026-10-18.

**Input**: User description: "Rediseñar la pantalla de Inicio del rol Administrador: cifras que cuadren con el total, quitar «Procesando», «Con error», «Requieren su atención» y «Control administrativo»; separar kardex y transferencias vehiculares; añadir actividad por semana y «Últimas confrontaciones» con la usuaria que la ejecutó. Además, quien sube un documento que no se pudo leer recibe el aviso en su Inicio, sea Administrador o Usuario."

## Origen

El usuario revisó el Inicio del administrador como notario y señaló:

- «Kardex 8» no coincide con la suma de las tarjetas (0 + 6 + 0): los kardex
  «Sin documentos» no tienen tarjeta.
- «Procesando» y «Con error» son estados técnicos que no aportan al notario.
- «Requieren su atención» solo muestra documentos ilegibles, que no son errores
  que el administrador deba resolver; además, su detalle solo recorre los cinco
  kardex más recientes.
- «Control administrativo» repite el acceso del menú lateral «Usuarios y
  permisos».
- Interesa ver cuántos kardex y cuántas transferencias vehiculares hay, la
  actividad por semana y quién ejecutó cada confrontación.
- Se descartó la tarjeta «Pendientes de confrontar»: la confrontación es
  automática al terminar la carga (F26) y el usuario la consideró innecesaria.

El Inicio del rol Usuario se mantiene igual, salvo el aviso de documento
ilegible (Historia 3), que vale para cualquier rol.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Resumen con cifras que cuadran (Priority: P1)

El administrador abre Inicio y ve, de un vistazo, cuántos kardex notariales y
cuántas transferencias vehiculares tiene la notaría hasta la fecha. Las cifras parciales suman el total que se
muestra. Ya no aparecen las tarjetas «Procesando» ni «Con error», ni los
paneles «Requieren su atención» y «Control administrativo».

**Why this priority**: Es lo primero que ve el notario; una cifra que no cuadra
le quita confianza al sistema.

**Independent Test**: Con datos ficticios de varios tipos y estados, abrir
Inicio como Administrador y comprobar que kardex notariales + transferencias
vehiculares = total, y que los cuatro elementos retirados no aparecen.

**Acceptance Scenarios**:

1. **Given** 5 kardex notariales y 3 transferencias vehiculares activos de
   varias usuarias, **When** el administrador abre Inicio, **Then** ve
   «Kardex: 5», «Transferencias vehiculares: 3» y un total de 8.
2. **Given** kardex sin documentos, en proceso o con un documento ilegible,
   **When** el administrador abre Inicio, **Then** cada kardex cuenta en su
   tipo y el total sigue cuadrando.
3. **Given** cualquier estado de datos, **When** el administrador abre Inicio,
   **Then** no ve las tarjetas «Procesando» ni «Con error», ni los paneles
   «Requieren su atención» ni «Acceso rápido · Control administrativo».
4. **Given** el administrador pulsa la cifra de un tipo, **When** se abre la
   lista, **Then** es la de ese tipo y muestra el mismo número de kardex.

---

### User Story 2 - Actividad por semana y últimas confrontaciones (Priority: P2)

El administrador ve la actividad de confrontación de las últimas 12 semanas y
la lista de las últimas confrontaciones, con el kardex, su tipo, la usuaria que
la ejecutó y la fecha.

**Why this priority**: Da control sobre el trabajo del equipo, pero no bloquea
la tarea diaria.

**Independent Test**: Con confrontaciones ficticias repartidas en varias
semanas y usuarias, comprobar las cifras por semana y el orden y contenido de
la lista.

**Acceptance Scenarios**:

1. **Given** kardex confrontados en distintas semanas, **When** el
   administrador abre Inicio, **Then** ve una barra por cada una de las últimas
   12 semanas con el número de kardex distintos confrontados, incluidas las
   semanas en 0.
2. **Given** un kardex confrontado tres veces en la misma semana (por cambios
   en sus documentos), **When** el administrador abre Inicio, **Then** ese
   kardex suma 1 en esa semana.
3. **Given** confrontaciones de varias usuarias, **When** abre Inicio, **Then**
   «Últimas confrontaciones» muestra los cinco kardex confrontados más
   recientemente, uno por fila con su última confrontación, con kardex, tipo,
   usuaria y fecha, de la más reciente a la más antigua.
4. **Given** una fila de la lista, **When** la pulsa, **Then** se abre ese
   kardex.
5. **Given** que aún no hay confrontaciones, **When** abre Inicio, **Then** ve
   un estado vacío que lo explica, en lugar de una lista o gráfico vacío.

---

### User Story 3 - Aviso de documento ilegible para quien lo subió (Priority: P2)

Cuando un documento no se pudo leer, la persona que lo subió ve un aviso en su
Inicio, aunque haya salido del kardex. Vale para Administrador y para Usuario.
El administrador no ve los avisos de documentos que subieron otras usuarias.

**Why this priority**: Cubre el caso de quien sube y se va antes de que termine
la lectura; sin él, el error solo se ve al volver al kardex.

**Independent Test**: Subir como usuaria ficticia A un documento que termina
ilegible; comprobar que A ve el aviso en su Inicio y que el administrador y la
usuaria B no lo ven.

**Acceptance Scenarios**:

1. **Given** un documento ilegible subido por la usuaria A, **When** A abre
   Inicio, **Then** ve un aviso con el código del kardex, qué pasó y qué hacer
   («Un documento que usted subió no se pudo leer. Elimínelo y vuelva a
   subirlo.») y un enlace al kardex.
2. **Given** el mismo documento, **When** el administrador u otra usuaria abren
   Inicio, **Then** no ven ese aviso.
3. **Given** que A elimina el documento o el kardex se archiva, **When** A
   vuelve a Inicio, **Then** el aviso ya no aparece.
4. **Given** varios documentos ilegibles de A en distintos kardex, **When** A
   abre Inicio, **Then** ve un aviso por kardex, sin importar su antigüedad.

### User Story 4 - Ver por semana o por mes, con datos al día (Priority: P2)

Ampliación pedida el 2026-10-18. El administrador elige ver la actividad
**por semana** (últimas 12 semanas) o **por mes** (meses del año en curso, de
enero al mes actual). El Inicio se actualiza solo cada minuto, sin recargar la
página, y los cambios se muestran con animaciones suaves y didácticas.

**Why this priority**: permite seguir el trabajo del día sin recargar y
comparar el ritmo de la notaría a lo largo del año.

**Independent Test**: con confrontaciones ficticias en varias semanas y meses,
cambiar entre «Por semana» y «Por mes» y comprobar barras y cifras; crear una
confrontación nueva y comprobar que aparece en el siguiente minuto sin recargar.

**Acceptance Scenarios**:

1. **Given** el Inicio del administrador, **When** elige «Por mes», **Then** ve
   una barra por cada mes del año en curso, de enero al mes actual, con el
   número de kardex distintos confrontados en cada mes.
2. **Given** la vista por mes, **When** vuelve a «Por semana», **Then** ve las
   12 semanas, y su elección se conserva al volver a Inicio.
3. **Given** el Inicio abierto, **When** pasa un minuto y hay confrontaciones
   nuevas, **Then** cifras, barras, listas e indicadores se actualizan solos, y
   se indica la hora de la última actualización.
4. **Given** un cambio de cifras o de periodo, **When** se actualiza la
   pantalla, **Then** las barras crecen o bajan suavemente desde su valor
   anterior y los números avanzan hasta su nuevo valor (menos de 1 s).
5. **Given** el puntero o el foco del teclado sobre una barra, **When** se
   detiene en ella, **Then** se explica en una frase qué representa
   («5 kardex confrontados en la semana del 06/10»).
6. **Given** que el sistema operativo pide reducir el movimiento, **When** se
   actualiza la pantalla, **Then** los valores cambian sin animación.
7. **Given** la pestaña del navegador en segundo plano, **When** pasa el
   tiempo, **Then** no se consultan datos hasta que vuelve a estar visible, y al
   volver se actualiza de inmediato.

---

### User Story 5 - Indicadores de calidad del periodo (Priority: P2)

Ampliación pedida el 2026-10-18. Para el periodo elegido (12 semanas o año en
curso), el administrador ve:

- **Observaciones por gravedad**: cuántas ALTA, MEDIA y BAJA.
- **Confrontaciones por usuaria**: kardex confrontados por cada persona.
- **Usuarias con más errores**: observaciones por persona, de mayor a menor.
- **Errores más frecuentes**: los 5 tipos de observación que más se repiten.
- **Correcciones aplicadas**: documentos corregidos generados y correcciones
  aplicadas en ellos.

**Why this priority**: muestra dónde se equivoca el equipo y cuánto se
aprovecha la corrección automática; orienta la capacitación.

**Independent Test**: con confrontaciones ficticias de dos usuarias, con
observaciones de distinta gravedad y tipo, y una decisión de corrección,
comprobar cada indicador para cada periodo.

**Acceptance Scenarios**:

1. **Given** kardex creados por la usuaria A y por la usuaria B, **When** se
   confrontan, **Then** sus observaciones y confrontaciones se atribuyen a quien
   **creó** el kardex, aunque otra persona haya subido el borrador.
2. **Given** un kardex confrontado dos veces con los mismos documentos,
   **When** se calculan los indicadores, **Then** cuenta una sola vez; si se
   cambió algún documento, la nueva versión cuenta aparte.
3. **Given** observaciones ALTA, MEDIA y BAJA en el periodo, **When** abre
   Inicio, **Then** ve los tres totales.
4. **Given** varias usuarias, **When** abre Inicio, **Then** ve, por persona,
   kardex confrontados, observaciones y observaciones ALTA, ordenadas de más a
   menos observaciones.
5. **Given** observaciones de varios tipos, **When** abre Inicio, **Then** ve
   los 5 tipos más frecuentes con su descripción en lenguaje notarial y su
   cantidad.
6. **Given** documentos corregidos generados en el periodo, **When** abre
   Inicio, **Then** ve cuántos documentos se corrigieron y cuántas correcciones
   se aplicaron.
7. **Given** un periodo sin confrontaciones, **When** abre Inicio, **Then** cada
   indicador muestra un estado vacío que lo explica.

### Edge Cases

- Sin ningún kardex: las cifras muestran 0 y los paneles, su estado vacío.
- Kardex archivados: no cuentan en las cifras, ni en avisos.
  Las confrontaciones ya registradas siguen contando en la actividad semanal
  (es un registro histórico).
- Una usuaria desactivada: sus confrontaciones siguen apareciendo con su nombre.
- Confrontaciones repetidas del mismo kardex en una semana: cuentan una vez
  (FR-004).
- Semanas: se cuentan de lunes a domingo, en la hora local de la notaría.
- Una cuenta en los grupos Administrador y Usuario a la vez ve el Inicio del
  Administrador (la condición de administrador manda, como en el resto del ERP).

## Requirements *(mandatory)*

### Functional Requirements

**Inicio del Administrador**

- **FR-001**: El Inicio del Administrador MUST mostrar las cifras «Kardex»
  (notariales) y «Transferencias vehiculares», ambas de los expedientes activos
  (no archivados) de todas las usuarias, y un total igual a su suma.
- **FR-002**: El Inicio del Administrador MUST NOT mostrar las tarjetas
  «Procesando» ni «Con error», ni los paneles «Requieren su atención» ni
  «Acceso rápido · Control administrativo».
- **FR-003**: Las cifras «Kardex» y «Transferencias vehiculares» MUST abrir su
  lista (kardex o transferencias) con el mismo conjunto que cuentan. El total
  no es un enlace, porque no hay una lista que mezcle los dos tipos.
- **FR-004**: El Inicio del Administrador MUST mostrar la actividad de
  confrontación de las últimas 12 semanas: por semana, el número de kardex
  distintos confrontados al menos una vez; las semanas sin actividad, en 0.
- **FR-005**: El Inicio del Administrador MUST mostrar «Últimas
  confrontaciones»: los cinco kardex confrontados más recientemente, uno por
  fila con los datos de su última confrontación: código del kardex, tipo, nombre
  de la usuaria que la ejecutó y fecha y hora; cada fila abre el kardex.
- **FR-006**: La actividad semanal MUST mostrarse sin dependencias nuevas ni
  recursos externos, y con la cifra en texto además de la barra (no solo con
  color o altura).

**Aviso de documento ilegible (todos los roles)**

- **FR-007**: El Inicio de cualquier rol MUST mostrar un aviso por cada kardex
  activo con al menos un documento ilegible subido por quien mira la pantalla,
  sin límite por antigüedad.
- **FR-008**: El aviso MUST decir qué pasó y qué hacer, en lenguaje notarial,
  sin términos técnicos ni datos del documento (nombre de archivo incluido), y
  enlazar al kardex.
- **FR-009**: Un usuario MUST NOT ver avisos de documentos que subieron otras
  personas, tampoco el Administrador.
- **FR-010**: El aviso MUST desaparecer cuando el documento ya no está
  ilegible (eliminado o reemplazado) o el kardex se archiva.

**Periodo y actualización (US4)**

- **FR-012**: El Inicio del Administrador MUST ofrecer dos periodos: «Por
  semana» (últimas 12 semanas, lunes a domingo) y «Por mes» (meses del año en
  curso, de enero al mes actual), en hora de Lima. Por defecto, por semana; la
  elección se recuerda en ese navegador.
- **FR-013**: La actividad, los indicadores de calidad (FR-016 a FR-020) y las
  cifras MUST actualizarse solos cada 60 s sin recargar la página, y al cambiar
  de periodo. La pantalla muestra la hora de la última actualización y, si una
  actualización falla, lo dice sin borrar los datos ya mostrados.
- **FR-014**: Los cambios MUST animarse con suavidad (barras que crecen desde
  su valor anterior, cifras que avanzan hasta el nuevo valor, filas nuevas que
  aparecen gradualmente), en menos de 1 s, y sin animación si el sistema pide
  reducir el movimiento.
- **FR-015**: Cada barra MUST explicar, al pasar el puntero o con el foco del
  teclado, qué representa, en una frase con la cifra y el periodo. No se
  consultan datos mientras la pestaña está oculta.

**Indicadores de calidad (US5)**

- **FR-016**: Los indicadores MUST calcularse sobre las confrontaciones
  creadas en el periodo elegido. Dos confrontaciones del mismo kardex con los
  mismos documentos de entrada cuentan una sola vez; cada versión distinta de
  los documentos cuenta aparte.
- **FR-017**: Las observaciones y las confrontaciones MUST atribuirse a la
  persona que **creó el kardex** (decisión del usuario: quien crea el kardex es
  quien debe confrontarlo).
- **FR-018**: «Observaciones por gravedad» MUST mostrar los totales ALTA, MEDIA
  y BAJA según la gravedad registrada en cada observación.
- **FR-019**: «Usuarias con más errores» MUST listar, por persona: kardex
  confrontados, observaciones y observaciones ALTA, ordenadas por observaciones
  de mayor a menor. «Confrontaciones por usuaria» usa la misma lista.
- **FR-020**: «Errores más frecuentes» MUST mostrar los 5 tipos de observación
  más repetidos con la descripción del catálogo de reglas y su cantidad.
  «Correcciones aplicadas» MUST mostrar cuántos documentos corregidos se
  generaron y cuántas correcciones se aplicaron en ellos.

**Inicio del Usuario**

- **FR-011**: El Inicio del rol Usuario MUST seguir como hoy, salvo que
  sustituye el panel «Requieren su atención» por los avisos de FR-007
  (decisión del usuario, para todos los roles).

### Security Requirements

- Solo el rol Administrador ve las cifras de toda la notaría, la actividad
  semanal y las confrontaciones de otras usuarias. El rol Usuario sigue viendo
  solo sus kardex.
- Los avisos de FR-007 se filtran por quien subió el documento; ninguna vista
  muestra avisos ajenos.
- La pantalla solo muestra códigos de kardex, tipos, nombres de usuarias del
  sistema, fechas y cifras: nunca nombres de comparecientes, DNI, nombres de
  archivo ni contenido de documentos.
- No se crea ningún dato nuevo: todo se calcula a partir de los expedientes,
  documentos y confrontaciones ya registrados.

- Los indicadores por persona (FR-017, FR-019) solo los ve el Administrador.
  Muestran nombres de usuarias del sistema y cifras, nunca el contenido de las
  observaciones ni datos de comparecientes.
- La actualización automática usa un punto de consulta de datos que exige
  sesión y rol Administrador, y responde lo mismo que la pantalla.

### UX Requirements (principio VIII)

- Cifras y textos en español notarial («kardex», «confrontación»), sin
  «procesando», «error» ni términos técnicos en las tarjetas.
- Cada cifra es un enlace a su lista filtrada (reconocer antes que recordar).
- Estados vacíos con texto que explica la situación.
- El gráfico semanal es accesible: etiqueta por semana, cifra visible y
  descripción para lectores de pantalla.
- Mismos componentes visuales que el resto del ERP (tarjeta de métrica, panel,
  fila, chip).

### Key Entities

- **Expediente (kardex)**: tipo (Kardex o Transferencia vehicular), quién lo
  creó, si está archivado.
- **Documento**: estado (incluido «no se pudo procesar»), quién lo subió.
- **Confrontación (corrida)**: kardex, usuaria que la ejecutó, fecha, origen
  (automática o manual). Registro inmutable ya existente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En el 100 % de los casos de prueba, las cifras parciales del
  Inicio del Administrador suman el total mostrado.
- **SC-002**: El administrador sabe quién hizo cada una de las cinco últimas
  confrontaciones sin abrir ningún kardex.
- **SC-003**: El 100 % de los documentos ilegibles de una persona generan aviso
  en su Inicio, y el 0 % aparece en el Inicio de otra persona.
- **SC-004**: Inicio carga en menos de 2 segundos con el volumen de la notaría
  (≤ 10 usuarias, miles de kardex).

- **SC-005**: Tras una confrontación nueva, el Inicio del administrador la
  refleja en menos de 70 s sin que nadie recargue la página.
- **SC-006**: El 100 % de los indicadores de calidad cuadran con un recuento
  manual sobre los datos de prueba, sin contar dos veces la misma versión de
  documentos.

## Assumptions

- La actividad semanal cubre 12 semanas (el usuario propuso 8–12).
- «Últimas confrontaciones» muestra cinco filas, como la lista actual.
- En una confrontación automática, «la usuaria que la ejecutó» es la que la
  corrida registra hoy como usuario; no se cambia cómo se registra.
- Los kardex archivados no cuentan en las cifras; sus confrontaciones sí cuentan
  en la actividad semanal.
- FR-011: las métricas del Inicio del Usuario y su acceso rápido «Nueva
  confrontación» no cambian.
- La lista de kardex ya acepta el filtro por tipo que usan las cifras.
- US4–US5 (2026-10-18): «Usuarias con más errores» ordena por número total de
  observaciones; también muestra cuántos kardex confrontó cada persona para
  leer la cifra en contexto.
- Las confrontaciones que no llegaron a resultado (error o no disponible) no
  suman observaciones.
- La elección de periodo se guarda solo en el navegador (preferencia de
  pantalla, no dato de negocio).
- Sin dependencias nuevas ni CDN (constitución, restricciones técnicas).

## F57 · Ranking de errores por digitadora y versión imprimible

**Pedido** (2026-10-20): «Dashboard con ranking de errores por digitadora y
versión imprimible». Premisa: el sistema tiene que ahorrar tiempo.

**Decisiones del usuario** (2026-10-20):

- El ranking se ordena por **total de errores** (observaciones) del periodo.
- Los errores de un kardex se atribuyen a **quien creó el kardex**, el mismo
  criterio de US5.

### Requisitos

- **FR-F57-01**: «Usuarias con más errores» pasa a ser la tabla «Errores por
  digitadora», a todo el ancho, justo después de la actividad. Columnas:
  puesto, digitadora, kardex confrontados, total de errores (con una barra
  proporcional al mayor total, decorativa), Alta, Media, Baja y promedio por
  kardex (un decimal, solo informativo: no cambia el orden).
- **FR-F57-02**: Figuran **todas** las personas con al menos un kardex
  confrontado en el periodo, también las que no tienen errores; sin límite de
  filas. Quien solo confrontó fuera del periodo no figura.
- **FR-F57-03**: Orden por total de mayor a menor y, a igual total, por
  nombre. A igual total, mismo puesto (1, 2, 2, 4).
- **FR-F57-04**: Se reutiliza el cálculo de US5 (`indicadores_calidad`): una
  confrontación repetida con los mismos documentos no suma dos veces y las
  confrontaciones sin resultado no suman errores.
- **FR-F57-05**: Botón «Imprimir o guardar PDF» en las acciones de la página
  (mismo rótulo que la confrontación). Abre el diálogo de impresión del
  navegador; no se genera PDF en el servidor ni hay vista nueva.
- **FR-F57-06**: En papel van solo: la marca de la notaría (logo si está
  configurado y nombre), el título «Ranking de errores por digitadora», el
  periodo elegido con fechas absolutas («del 03/08/2026 al 20/10/2026»), quién
  lo emite y la fecha y hora de los datos, la tabla del ranking y los
  indicadores clave (gravedad, errores más frecuentes, correcciones). Sin menú
  lateral, botones, selector de periodo, cifras por tipo, actividad, últimas
  confrontaciones ni animaciones. Pensado para una hoja A4.
- **FR-F57-07**: Solo el Administrador ve el ranking y el botón, con los mismos
  permisos del Inicio del administrador; el JSON de `/inicio/datos/` añade
  `rango` y `fecha` para la cabecera impresa.

### Accesibilidad y textos

- Tabla con `caption`, `th scope="col"` en los encabezados y `th scope="row"`
  en la digitadora. Las gravedades se leen por el texto del encabezado (el
  color solo acompaña) y la barra es decorativa (`aria-hidden`): el número
  está siempre escrito. Contraste de los encabezados de gravedad ≥ 9:1.
- La descripción del panel explica el criterio en pantalla y en papel: errores
  del periodo, cada observación cuenta para quien creó el kardex, confrontar de
  nuevo con los mismos archivos no suma, el promedio solo informa.

### Por confirmar

- Empates: mismo puesto para el mismo total (1, 2, 2, 4) en lugar de puestos
  correlativos por orden alfabético.
- El promedio se muestra con punto decimal (2.5), como los montos en Perú.
- Se llama «digitadora» a toda persona que creó kardex, también si es
  administradora.
