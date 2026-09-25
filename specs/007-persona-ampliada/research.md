# Research: F12 · Persona ampliada

**Alcance**: planificación solamente. `spec.md` aprobado no se modifica; no se
implementa código ni se decide una regla de negocio pendiente.

## Evidencia y discrepancias

- La constitución 1.6.0 exige núcleo puro y determinista, TDD con datos
  ficticios, privacidad, y conservar la medición privada antes de integrar.
- F11 define `Persona(nombre, documento, procedencias, estado)` como subtipo de
  `namedtuple`; hay construcciones posicionales de tres y cuatro argumentos.
  `unificar_personas()` reconstruye cada persona dos veces y perdería cualquier
  campo añadido si no se actualiza. `comparar_personas()` devuelve una tupla de
  diccionarios de identidad; `revisar()` mantiene cadenas históricas.
- `_linea_etiquetada()` ya lee valor junto al rótulo o en la celda siguiente,
  separada por dos espacios. `_personas_de_pagina()` puede retornar antes de
  llegar a la extracción de página completa; los nuevos campos deben asociarse
  a la única persona verificable de una página RENIEC o BIOMETRICA, sin capturar
  otra columna, operador, pie ni otra persona.
- `docs/catalogo-fuentes.md` documenta literalmente **`Estado Civil`** y
  **`Fecha de Nacimiento`** en RENIEC. No documenta el rótulo de domicilio ni
  distrito en RENIEC, ni el de estado civil en biométrica. Tampoco documenta
  rótulos de fecha, domicilio o distrito en biométrica. No se inventarán.
- `docs/catalogo-datos.md` mide RENIEC: estado civil 100 %, fecha 96 %,
  domicilio 96 %, distrito 100 %; biométrica: estado civil 89 %, los otros tres
  campos sin cobertura medida (`—`). Por eso la frase de entrada de `spec.md`
  que atribuye fecha y domicilio a ambas plantillas con fiabilidad 89–100 %
  contradice la tabla. El catálogo mide 28/27 páginas de esos tipos, mientras
  `catalogo-fuentes.md` censa 30/32; falta explicar la diferencia de muestra,
  pero no se extrapolan porcentajes.
- US1 dice «minuta», mientras sus escenarios y el flujo F5 comparan el
  **borrador**. `confrontar_borrador()` reúne minutas para párrafos, pero pasa
  solo el borrador a `comparar_personas()`. La fuente textual de la regla civil
  debe confirmarse por el propietario antes de implementarla.
- Aunque el propietario aprobó el texto para planificar, la cabecera de
  `spec.md` aún indica `Status: Draft`; se reporta como discrepancia editorial.

## Decisiones de diseño propuestas

### Contrato de `Persona`

Conservar los cuatro campos iniciales y el constructor posicional vigente.
Añadir al final `estado_civil`, `fecha_nacimiento`, `domicilio`, `distrito` y
`procedencia_estado_civil`, `procedencia_fecha_nacimiento`,
`procedencia_domicilio`, `procedencia_distrito`, todos opcionales. `estado`
sigue valiendo `CONFIRMADA` si se omite. Los constructores actuales de tres o
cuatro argumentos y los atributos ya usados conservan su significado. En la
implementación, un `__new__` con valores por defecto explícitos permite también
usar argumentos con nombre; no se cambia a dataclass ni se altera el orden de
los cuatro campos existentes. Se revisarán usos de desempaquetado/longitud de
tupla antes de editar; la tupla crecerá.

Cada procedencia nueva conserva archivo y página **del valor seleccionado** y
el tipo de página necesario para aplicar la prioridad RENIEC > BIOMETRICA del
conflicto civil. Puede ser una tupla nombrada pura distinta de `Procedencia`
histórica, de modo que la salida de identidad F11 y sus procedencias no cambien.
Una procedencia ausente acompaña siempre a un valor ausente. La unificación
arrastra valor y procedencia juntos; nunca llena un campo usando otra persona.
Para estado civil discordante se conserva RENIEC y se usa en el cuarto campo
`estado` el código específico `REVISION_MANUAL_ESTADO_CIVIL`; así el motivo
sobrevive a la unificación sin añadir otro campo. `comparar_personas()` puede
emitir la observación de conflicto y la UI muestra «Revisión manual: estado
civil discrepante». La regla puede usar el valor RENIEC, pero la UI debe avisar
del conflicto.

### Captura y normalización

Solo se lee tras clasificar inequívocamente como RENIEC o BIOMETRICA. Los
rótulos confirmados son `ESTADO CIVIL` y `FECHA DE NACIMIENTO` en RENIEC,
normalizados por `norm()` antes de llamar a `_linea_etiquetada()`. La etiqueta
biométrica de estado civil y las de domicilio/distrito esperan documentación
en el catálogo; no se buscan sin rótulo cerrado. La página debe aportar una
sola persona ligada al bloque; de lo contrario se deja el campo vacío para no
atribuirlo a otro compareciente. No se leen declaración jurada, DNI escaneado,
SISGEN, prosa ni campos del pie.

`CASADA/CASADO`, `SOLTERA/SOLTERO`, `VIUDA/VIUDO` y
`DIVORCIADA/DIVORCIADO` se proyectan a los cuatro enum sin género de FR-003;
no se añade almacenamiento del género porque la spec lo condiciona a una
necesidad de presentación que no existe. Fecha válida `dd/mm/aaaa` o
`dd-mm-aaaa` se convierte a `datetime.date` y se muestra como ISO; se rechaza
una fecha imposible o con letras OCR confundibles, incluido `197б`. El
domicilio se conserva tal cual tras limpiar espacios de OCR; su comparación
ignora tildes y mayúsculas. Distrito procede del campo del domicilio, nunca de
nacimiento. No se separa un distrito por heurística hasta conocer su rótulo o
frontera documental. `documento` mantiene sus ocho caracteres y cero inicial.

### Reglas y servicio

Ampliar `comparar_personas(fuente, borrador, *, fecha_referencia=None, ...)`
con observaciones estructuradas de tipos civiles, menor de edad, domicilio y
conflicto, conservando su llamada de dos argumentos y el contenido/orden de
sus observaciones de identidad. El comparador solo actúa sobre una persona
ligada inequívocamente por documento y nombre; sin documento no emite regla
de cónyuge. Para las nuevas reglas no se comparan campos de una persona con
otra. `revisar()` y `revisar_parrafos()` permanecen intactas.

El núcleo recibe la fecha de referencia como entrada explícita: nunca consulta
el reloj. Si falta, no afirma minoría de edad. El alcance de «sin cónyuge» y
la selección minuta/borrador se deben aclarar antes de cerrar la regla civil.
La equivalencia de abreviaturas de domicilio se debe aclarar antes de cerrar
la regla de domicilio. La aplicación adapta los nuevos diccionarios a filas de
`Regla` y añade esas filas después de las históricas, sin parsear cadenas
nuevas con `parsear_observacion_regla()`. `_resumen_extraccion()` y la plantilla
solo muestran cada campo y su procedencia tras la autorización actual. El
endpoint JSON de sondeo sigue limitado a estados y contadores.

## Preguntas pendientes para el propietario

1. `[NEEDS CLARIFICATION]` ¿La edad se calcula a la fecha de hoy o a la fecha
   del acto? La fecha del acto no se extrae hoy del borrador. (`spec.md` US2).
2. `[NEEDS CLARIFICATION]` ¿Cuál es la lista cerrada de abreviaturas de domicilio
   equivalentes? (`spec.md` US3; sus cuatro pares son ejemplos, no una lista
   declarada exhaustiva).
3. **Error documental por corregir sin reescribir el spec aquí**: confirmar los
   rótulos y fronteras de `domicilio`/`distrito` RENIEC y `estado_civil`
   biométrica en `docs/catalogo-fuentes.md`, así como la diferencia de muestra
   entre los dos catálogos. Hasta entonces, esas capturas no pueden cumplir
   SC-001 ni el estado civil biométrico con certeza.
4. **Contradicción del spec por resolver**: ¿US1 compara la minuta, el borrador
   o ambos? Precisar qué cuenta como «sin mención de cónyuge» para una persona
   concreta y cómo se distingue de un cónyuge mencionado en otro lugar.

## Deuda deliberada

Cónyuge manuscrito de declaración jurada, personas jurídicas, fecha del acto
extraída, equivalencias de domicilio no aprobadas y persistencia F6. No se
introducen modelos, red, dependencias, migraciones ni otra ruta de comparación.
