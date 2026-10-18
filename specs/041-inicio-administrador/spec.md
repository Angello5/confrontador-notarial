# Feature Specification: F53 · Inicio del administrador

**Feature Branch**: `041-inicio-administrador`

**Created**: 2026-10-18

**Status**: Implementado localmente (2026-10-18); pendiente de PR.

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
- Sin dependencias nuevas ni CDN (constitución, restricciones técnicas).
