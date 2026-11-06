# Feature Specification: F64 · Sugerencias en cifras y cuotas

**Feature Branch**: `feat/f64-sugerencias-cifras`

**Created**: 2026-10-30

**Status**: Draft

**Input**: User description: "Que los avisos de cifra y letras, área y cuotas digan, resumido y en lenguaje sencillo, lo que encontraron en la minuta y la sugerencia concreta («Se sugiere …»). Letras mal escritas que corregidas valen la cifra: se sugiere el texto correcto. Letras distintas de la cifra: si la minuta trae el dato, se dice qué dice y se sugiere corregir la que no coincide; si no lo trae, se dice lo hallado y que revise cuál corresponde. Cuotas que no suman 100 %, en todos los actos: se compara la cuota de cada persona con la minuta y se sugiere la corrección."

## Origen

Hoy tres avisos le dicen a la usuaria que algo no cuadra, pero no qué poner:

| Aviso | Qué dice hoy |
|---|---|
| Número en letras | «La cifra y las letras no valen lo mismo. Corrija la que no corresponda.» |
| Área | «La cifra y las letras del área no valen lo mismo. Corrija la que no corresponda.» |
| Copropiedad | «Las cuotas de copropiedad no suman 100 %. Corrija la que no corresponda.» |

F60 eligió esa redacción a propósito: con el proyecto solo, el ERP no sabe si está mal la cifra o las letras. Pero en muchos casos sí se puede saber:

- si las letras están **mal escritas** («TREINTA Y SEI», «SEIZ», «TREINTAY SEIS») y, corregida la palabra, valen la cifra, no hay duda de qué poner;
- si la **minuta** trae el dato, desempata.

El 2026-10-30 el usuario pidió que el aviso diga lo que encontró en la minuta y la sugerencia, de forma resumida y sencilla. Decidió también que la suma de cuotas se revise **en todos los actos** (copropiedad, aportes a sociedad, herederos y otros), no solo en copropiedad.

Todo es determinista, sin modelos (principio I): son datos con una única respuesta correcta.

## Clarifications

### Session 2026-10-30

- Q: ¿En qué actos deben sumar 100 % las cuotas? → A: en todos (copropiedad, aportes a sociedad, herederos, otros), siempre que los porcentajes repartan algo entre personas; no se suman intereses, moras ni otras tasas.
- Q: ¿Cómo se reconoce un reparto? → A: oración con dos o más porcentajes que nombra a las personas o usa términos de reparto (copropiedad, cuota, acciones, participaciones, aporte, herencia, heredero, legítima); nunca intereses, moras, penalidades, tasas, comisiones, descuentos ni impuestos. Se mide en los kardex locales (confirmado por el usuario).
- Q: ¿Cómo se ven los avisos? → A: lo hallado, lo que dice la minuta y «Se sugiere …», como en los ejemplos de las historias (confirmado por el usuario).
- Q: Si la minuta no trae el dato, ¿qué dice el aviso? → A (confirmado por el usuario): lo hallado, sin elegir: «La cifra dice 36 % y las letras dicen 35 %. La minuta no trae este dato: revise cuál corresponde.»

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Letras mal escritas (Priority: P1)

La usuaria confronta un proyecto que dice «TREINTA Y SEI POR CIENTO (36%)». El aviso le dice que las letras están mal escritas y le sugiere el texto exacto: «TREINTA Y SEIS POR CIENTO (36%)».

**Why this priority**: es el caso más frecuente (letras con una errata) y la sugerencia no tiene duda posible.

**Independent Test**: confrontar proyectos ficticios con erratas en las letras de un porcentaje, un monto y un área, y comprobar el texto sugerido.

**Acceptance Scenarios**:

1. **Given** el proyecto dice «TREINTA Y SEI POR CIENTO (36%)», **When** se confronta, **Then** el aviso dice «Las letras están mal escritas. Se sugiere: TREINTA Y SEIS POR CIENTO (36%).»
2. **Given** el proyecto dice «TREINTAY SEIS (36) MESES», **When** se confronta, **Then** se sugiere «TREINTA Y SEIS (36)».
3. **Given** la palabra mal escrita, corregida, no da la cifra («TREINTA Y SEI (37)»), **When** se confronta, **Then** no se trata como errata: se aplica la historia 2.

---

### User Story 2 - Cifra y letras distintas: desempata la minuta (Priority: P1)

El proyecto dice «TREINTA Y CINCO POR CIENTO (36%)». Las dos están bien escritas, pero no valen lo mismo. El ERP busca el dato en la minuta y le dice a la usuaria qué encontró y qué corregir.

**Why this priority**: es el error que más daño hace (un porcentaje, un precio o un área distintos) y hoy la usuaria tiene que ir a buscarlo a mano.

**Independent Test**: tres proyectos ficticios con la misma discrepancia y tres minutas: una que dice 36 %, otra 35 % y otra que no trae el dato.

**Acceptance Scenarios**:

1. **Given** la minuta dice 36 %, **When** se confronta, **Then** el aviso dice «La minuta dice 36 %. Se sugiere corregir las letras: TREINTA Y SEIS POR CIENTO (36%).»
2. **Given** la minuta dice 35 %, **When** se confronta, **Then** el aviso dice «La minuta dice 35 %. Se sugiere corregir la cifra: TREINTA Y CINCO POR CIENTO (35%).»
3. **Given** la minuta no trae ni 35 % ni 36 % (o trae los dos), **When** se confronta, **Then** el aviso dice «La cifra dice 36 % y las letras dicen 35 %. La minuta no trae este dato: revise cuál corresponde.»
4. **Given** lo mismo con un área («CIENTO VEINTE METROS CUADRADOS (125.00 M2)») o un monto en soles o dólares, **When** se confronta, **Then** el aviso sigue las mismas tres reglas con su unidad.

---

### User Story 3 - Cuotas que no suman 100 %, en todos los actos (Priority: P1)

El proyecto reparte un bien, unas acciones o una herencia: «JUAN PEREZ EL 20 %, ANA RUIZ EL 20 % Y LUIS SOTO EL 50 %». Suman 90 %. El ERP compara la cuota de cada persona con la minuta y dice cuál cambiar.

**Why this priority**: un reparto que no suma 100 % deja una parte del bien sin dueño; el usuario pidió revisarlo en todos los actos.

**Independent Test**: proyectos ficticios de copropiedad, aporte a sociedad y sucesión con una cuota cambiada, con y sin el reparto en la minuta.

**Acceptance Scenarios**:

1. **Given** la minuta reparte 20 %, 20 % y 60 % entre las mismas personas, **When** se confronta, **Then** el aviso dice «Las cuotas suman 90 %. La minuta dice LUIS SOTO 60 %. Se sugiere: LUIS SOTO 60 % (dice 50 %).»
2. **Given** dos cuotas cambiadas, **When** se confronta, **Then** la sugerencia nombra a las dos personas, en el orden del proyecto.
3. **Given** la minuta no trae el reparto, **When** se confronta, **Then** el aviso dice «Las cuotas suman 90 %. La minuta no trae el reparto: revise cuál corresponde.»
4. **Given** un aporte a sociedad o una sucesión, sin la palabra «copropiedad», **When** las cuotas de las personas no suman 100 %, **Then** se avisa igual.
5. **Given** una oración con un interés del 2 % y una mora del 1 %, **When** se confronta, **Then** no se avisa: no reparten nada entre personas.

---

### Edge Cases

- **Aviso ya guardado:** las confrontaciones anteriores se siguen viendo como hoy; la sugerencia aparece en las nuevas.
- **Cifra con decimales en letras** («MIL QUINIENTOS Y 50/100 SOLES (S/ 1,500.00)»): la sugerencia escribe las letras con el mismo formato de céntimos del proyecto.
- **Cifras que el ERP no sabe escribir en letras con seguridad** (fuera de 0 a 999 999 999 999): el aviso dice el valor correcto en cifra, sin letras.
- **Errata ambigua:** si una palabra mal escrita se parece por igual a dos palabras numéricas, se toma solo si exactamente una de las lecturas da la cifra; si ninguna o varias, se aplica la historia 2.
- **«CADA UNO»:** como hoy, no se suman las cuotas.
- **Vendedores y compradores en la misma oración** (200 %) o una cuota que es la suma de las demás: como hoy, no se avisa.
- **Cuotas en varias oraciones:** como hoy, solo se suman las de una misma oración.
- **Nombres distintos entre minuta y proyecto** (una persona más o menos): no se sugiere por persona; el aviso dice la suma y que revise.
- **Corrección automática (F21):** estos avisos siguen sin entrar en el documento corregido; la sugerencia es para la usuaria.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Cuando las letras tienen una palabra mal escrita y, cambiándola por la palabra numérica más parecida, valen la cifra, el aviso dice «Las letras están mal escritas» y sugiere el texto completo correcto (letras, unidad y cifra).
- **FR-002**: Cuando cifra y letras valen distinto y la minuta trae uno solo de los dos valores con la misma unidad, el aviso dice qué dice la minuta y sugiere corregir la parte que no coincide, con el texto completo.
- **FR-003**: Cuando la minuta no trae ninguno de los dos valores, o trae los dos, el aviso dice los dos valores hallados y que la minuta no trae el dato, sin elegir.
- **FR-004**: FR-001 a FR-003 valen para números en letras (porcentajes, montos, plazos y demás) y para áreas.
- **FR-005**: La suma de cuotas se revisa en toda oración donde dos o más porcentajes reparten algo entre personas, en cualquier acto. No se suman porcentajes de intereses, moras, penalidades, tasas, comisiones, descuentos ni impuestos.
- **FR-006**: Si las cuotas no suman 100 % y la minuta reparte entre las mismas personas, el aviso dice la suma, lo que dice la minuta de cada cuota distinta y sugiere la cuota correcta por persona. Si no, dice la suma y que la minuta no trae el reparto.
- **FR-007**: Cada aviso tiene tres partes cortas: **lo hallado** en el proyecto, **lo que dice la minuta** (o que no lo trae) y **la sugerencia**, que empieza con «Se sugiere».
- **FR-008**: La línea de la lista de errores resume la sugerencia en una línea («Letras mal escritas: … → …», «Las cuotas no suman 100 %: … → LUIS SOTO 60 %»).
- **FR-009**: Las confrontaciones guardadas antes de F64 se muestran como hoy.
- **FR-010**: Estos avisos siguen fuera del documento corregido automático (F21), salvo la errata de las letras («letras mal escritas»): se corrige con el texto de la propia cifra y trae su casilla. F66 la extiende al área en letras (`specs/049-correccion-letras/`).
- **FR-011**: La misma entrada da siempre el mismo aviso y la misma sugerencia (principio I).

### UX Requirements (principio VIII)

- **Lenguaje de la notaría (2):** «La minuta dice…», «Se sugiere…», «revise cuál corresponde». Sin nombres de reglas ni de campos internos.
- **Minimalismo (8):** el aviso cabe en dos o tres líneas; la sugerencia va en su propia línea, lista para copiar.
- **Consistencia (4):** el mismo panel, la misma gravedad y la misma posición que los avisos de hoy.
- **Prevenir errores (5):** cuando no hay con qué desempatar, el aviso no sugiere un valor.

### Key Entities

- **Aviso de cifra:** lo hallado (texto del proyecto), el valor de la cifra, el valor de las letras, la unidad (%, soles, dólares, m², sin unidad), lo que dice la minuta (o nada) y la sugerencia.
- **Reparto de cuotas:** las personas y su porcentaje en el proyecto, la suma, y las personas y su porcentaje en la minuta.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En el conjunto de casos ficticios de las historias 1 a 3, el 100 % de los avisos con sugerencia sugiere el texto correcto.
- **SC-002**: Ningún aviso sugiere un valor cuando la minuta no lo trae o lo trae de dos formas (0 sugerencias inventadas).
- **SC-003**: Ninguna oración de intereses, moras o tasas genera un aviso de cuotas en el conjunto de prueba.
- **SC-004**: En los kardex de la medición local, ningún aviso que existía antes desaparece y el número de avisos de cuotas fuera de copropiedad se informa en la medición.
- **SC-005**: La usuaria puede corregir el error leyendo solo el aviso, sin abrir la minuta, en todos los casos con sugerencia.

## Assumptions

- La minuta es la fuente que desempata; las fichas RENIEC o RUC no traen estos datos.
- «Trae el dato» significa que la minuta contiene el valor con la misma unidad (porcentaje, soles, dólares o área), en cifra o en letras.
- Un porcentaje «reparte entre personas» si la oración trae dos o más porcentajes y nombra a las personas o usa términos de reparto (copropiedad, cuota, acciones y derechos, participaciones, acciones, aporte, herencia, heredero, legítima). Se mide en los kardex locales y se ajusta antes de cerrar la fase.
- La palabra numérica «más parecida» se elige por distancia de edición pequeña sobre el vocabulario de números en letras que el ERP ya lee.
- Los avisos guardados no se recalculan; el cambio vale para las confrontaciones nuevas.

## Medición (kardex locales, fuera del repositorio)

Medido el 30/10/2026 con los 6 borradores de la base local, comparando el núcleo anterior y el de F64 sobre las mismas entradas. Solo conteos.

| Medida | Resultado |
|---|---|
| Observaciones por tipo, antes y después | Iguales en los 8 tipos (39 observaciones) |
| Observaciones previas que desaparecen | 0 (SC-004) |
| Avisos de cifra y letras con sugerencia | 3 de 3, los tres por letras mal escritas; revisados a mano: la sugerencia es correcta en los tres |
| Avisos de cuotas nuevos (fuera de copropiedad) | 0: los kardex locales no tienen repartos con porcentajes |

El criterio de reparto (FR-005) queda probado solo con casos ficticios; se vuelve a medir cuando haya kardex con repartos.
