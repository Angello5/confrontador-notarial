# Research: F12 · Persona ampliada

**Fuentes aprobadas (2026-09-25):** [spec.md](spec.md),
`docs/catalogo-datos.md` y `docs/catalogo-fuentes.md`.

## Evidencia y decisiones cerradas

- La identidad F11 usa `Persona(nombre, documento, procedencias, estado)` como
  `namedtuple`; hay llamadas posicionales de tres y cuatro argumentos.
  `unificar_personas()` reconstruye la persona al fusionar y al marcar
  documentos ambiguos. Ambas reconstrucciones deben conservar los campos F12.
- Solo RENIEC aporta `ESTADO CIVIL`, `FECHA DE NACIMIENTO`, `DIRECCIÓN` y
  `DISTRITO DE DOMICILIO`. Se exige rótulo al inicio de línea y valor en su
  propia columna. `DISTRITO DE NACIMIENTO` no equivale a domicilio. El pie
  «Registro Nacional de Identificación y Estado Civil» no es un campo; la
  biométrica no aporta ninguno de los cuatro valores en F12.
- La medición estricta sobre 28 páginas RENIEC encontró estado civil 100 %, fecha
  96 %, dirección 79 % y distrito de domicilio 64 %. Los censos de 30 RENIEC y
  32 biométricas describen todas las páginas del corpus; las muestras de 28 y
  27 son las páginas medidas por el instrumento. No se extrapolan porcentajes.
- `CASADA/CASADO`, `SOLTERA/SOLTERO`, `VIUDA/VIUDO` y
  `DIVORCIADA/DIVORCIADO` se proyectan a los cuatro valores sin género. No se
  almacena género aparte mientras no se muestre. Fecha `dd/mm/aaaa` o
  `dd-mm-aaaa` inequívoca pasa a `date`; cifras OCR dudosas y fechas imposibles
  se descartan. Dirección y distrito conservan el texto del valor, con espacios
  de borde eliminados.
- US1 se compara con el **borrador**. «Sin mención de cónyuge» se evalúa en la
  cláusula de la persona, delimitada en `spec.md`; otra cláusula no cuenta.
- US2 calcula edad cumplida **a la fecha de hoy**, y la observación muestra
  esa fecha. El servicio debe pasarla al núcleo para mantenerlo puro.
- US3 usa la lista cerrada del spec: AV/AVENIDA, JR/JIRÓN, CA/CALLE,
  PSJ/PASAJE, MZ/MANZANA, LT/LOTE, URB/URBANIZACIÓN,
  AAHH/ASENTAMIENTO HUMANO, DPTO/DEPARTAMENTO, INT/INTERIOR,
  N°/NÚMERO y S/N; ignora puntos, tildes y orden del número.

## Contrato mínimo de esta ronda

Se conservan las cuatro posiciones históricas de `Persona` y se añaden al final
cuatro valores opcionales y cuatro procedencias opcionales. La procedencia
histórica `Procedencia(fuente, pagina)` basta porque los campos F12 solo salen
de RENIEC. Cada valor se fusiona con **su** procedencia; una ausencia no hereda
la de otro campo. La captura se aplica solo si la página RENIEC produce una
única identidad verificable por nombre y documento. No se añade migración ni
dependencia.

La tabla de extracción HTML autorizada muestra los cuatro pares. El sondeo JSON,
logs y errores no reciben sus valores. `comparar_personas()`, `revisar()` y
`revisar_parrafos()` mantienen sus observaciones históricas para la misma
entrada ficticia. Las reglas civil, edad y domicilio y el manejo de dos RENIEC
discordantes se implementan en la siguiente ronda; la decisión de prioridad
por fecha de emisión requiere capturar esa fecha de manera fiable.

## Deuda deliberada

Reglas US1–US3, conflicto entre consultas RENIEC, cónyuge manuscrito de
declaración jurada, personas jurídicas, fecha del acto y persistencia F6.
La medición privada `local_reference` queda a cargo del propietario antes de
integrar el cambio al núcleo.
