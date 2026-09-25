# Research: F11 · Extracción por personas

**Alcance**: diseño de la extracción por páginas, la asociación determinista
entre nombre y documento y la compatibilidad con el núcleo y F4. Esta etapa no
implementa código ni reescribe `spec.md`.

## Evidencia revisada

- `.specify/memory/constitution.md` 1.6.0: núcleo puro, determinismo,
  privacidad, pruebas primero y retención indefinida del texto extraído.
- `docs/roadmap.md`: F11 cubre personas naturales; las jurídicas quedan fuera.
- `nucleo/verificar.py`: `catalogo()` devuelve conjuntos por campo; `revisar`,
  `correspondencia` y `diagnostico` dependen de ellos; `revisar_parrafos()`
  compara texto largo de la minuta.
- `adaptadores/extraccion.py`: `leer()` devuelve una sola cadena; `_pdf()` ya
  recorre páginas, pero las une antes de devolverlas; PDF e imágenes pasan por
  una caché local de OCR.
- `expedientes/services.py` y `TextoExtraido`: F4 guarda esa cadena en una
  fila identificada por `hash_archivo` y `version_extractor`, y borra el archivo
  temporal al terminar.
- `specs/005-confrontacion/`: F5 pasa `dict[str, str]` al núcleo y conserva la
  salida textual de reglas para no alterar la medición.
- `docs/catalogo-fuentes.md`: está incorporado al árbol de F11 y se usa como
  referencia de tipos, etiquetas y descarte.

## Resoluciones aplicadas

- NC-001: toda página SISGEN se descarta, incluido `Documento Identificativo`.
- NC-002: el adaptador une páginas con el separador `\f`; no hay campo nuevo ni
  migración. Un texto histórico sin separador se procesa como un solo bloque.
- NC-003: el cónyuge entra como `Persona` sin documento; solo se verifica su
  nombre.
- NC-004: los grupos manuscritos separados por espacios no se unen.
- NC-005: una página no clasificada que conserva identidad posible se cuenta y
  se lista por archivo y página, sin guardar ni mostrar su contenido; la prosa
  o anexo sin nombres ni documentos se ignora porque no puede aportar.

## Decisiones de diseño

### 1. Contrato nuevo y convivencia con el contrato por campos

El retorno de `catalogo()` pasará a ser un `Catalogo` puro e inmutable, con:

- `personas`: secuencia estable de `Persona(nombre, documento, procedencias,
  estado)`. Nombre y documento son opcionales para representar un bloque con un
  nombre legible pero sin documento o un documento legible sin nombre.
- `partidas` y `montos`: conjuntos de valores extraídos con las expresiones
  existentes.
- `paginas_descartadas`: conteo y tipo de cada página descartada, y
  `paginas_no_clasificadas`: archivo y página para revisión manual, sin guardar
  texto.

`Procedencia` contiene únicamente la clave de fuente entregada por la
aplicación y el número de página. `estado` distingue una asociación confirmada
de una que requiere `revision_manual`; no autoriza coincidencias aproximadas.
Las estructuras son `dataclass(frozen=True)` o equivalente estándar, sin
conocer Django, OCR, base de datos ni archivos.

Para que el cambio no rompa a F5 ni a los consumidores existentes, `Catalogo`
ofrecerá una proyección de solo lectura con las claves `NOMBRE`, `DNI`,
`PARTIDA` y `MONTO`. La proyección se calcula así:

```text
NOMBRE  = nombres no nulos de personas
DNI     = documentos no nulos de personas
PARTIDA = partidas extraídas con la regla existente
MONTO   = montos extraídos con la regla existente
```

`__getitem__`/`get` o un adaptador explícito mantendrá el acceso actual
`cat["NOMBRE"]`; no se expondrá una segunda copia mutable del catálogo. Las
funciones `revisar()`, `correspondencia()` y `diagnostico()` consumirán esta
proyección, y aceptarán temporalmente un `dict[str, set[str]]` legado para los
tests y consumidores que aún lo construyan a mano. Una entrada legado se
trata como una página de fuente única y conserva la salida histórica por
campos.

La comprobación de identidad ligada será una función nueva, separada de la
salida textual histórica de `revisar()`. Recibirá `Catalogo` y bloques del
borrador y devolverá observaciones estructuradas de documento cruzado o sin
titular. Así `revisar()` puede continuar produciendo exactamente las cadenas
actuales, mientras F11 añade la comprobación que los conjuntos sueltos no
pueden expresar.

No se derivarán párrafos desde `Catalogo`: `revisar_parrafos()` seguirá
recibiendo el texto de la minuta y conservará umbral y algoritmo. Partidas,
montos y párrafos quedan así fuera del filtro de identidades y satisfacen
FR-013.

### 2. Texto por página sin romper `leer()`

Se añadirá una operación `leer_paginas(Path) -> tuple[str, ...]`:

- PDF: una cadena por página; si carece de texto, OCR solo para esa página.
- Imagen: una tupla de una página.
- DOCX, formatos legacy, TXT y XLSX: una tupla de una página lógica, porque
  esos adaptadores no disponen de paginación fiable sin renderizar.

`leer(Path)` conservará su firma y devolverá `"\f".join(leer_paginas(Path))`
para que CLI, Streamlit, léxico, F4 y tests existentes sigan recibiendo una
cadena. La función común para PDF no volverá a ejecutar OCR: la caché de OCR se
guardará con el mismo contenido por página y sus metadatos de modelo.

La cadena plana de F4 sigue siendo el único valor persistido. Las páginas nuevas
se separan con `\f`; las filas antiguas no se migran ni se rellenan de forma
inventada y se procesan como un solo bloque, degradando sin romper F5.

### 3. Segmentación mínima

La unidad inicial será **una página = un bloque**. Es suficiente para el corpus
observado, donde lo normal es un documento por página, y permite asociar todo
nombre y documento dentro de una frontera verificable sin inventar un
segmentador visual.

Dentro de una página se extraen varias personas solo cuando las etiquetas y
los valores están en el mismo bloque lógico de formulario. En una declaración
jurada, por ejemplo, el declarante y el cónyuge salen de sus rótulos vecinos;
no se empareja el DNI del declarante con el nombre del cónyuge. Si una página
contiene varios documentos sin separador determinista, se conserva como un
bloque ambiguo y no se combinan sus valores. Un segmentador interno por
coordenadas queda como deuda, no como heurística en esta fase.

### 4. Clasificación y descarte conservador

La clasificación será una función pura de texto normalizado y tendrá
precedencia fija: `BLANCA_SEPARADOR`, `SISGEN`, `RENIEC`, `BIOMETRICA`,
`DECLARACION_JURADA`, `SUNARP`, `IDENTIDAD`, `PROSA`, `DESCONOCIDA`.

- `BLANCA_SEPARADOR`: texto vacío o solo separadores, sin etiquetas ni tokens
  de identidad.
- `SISGEN`: combinación de dos o más marcas estructurales (`CONSULTA
  REALIZADA`, `COINCIDENCIAS`, `DOCUMENTO IDENTIFICATIVO`, `N. CONSULTA`). La
  página completa, incluido `Documento Identificativo`, se excluye siempre.
- `RENIEC`: `CUI` y las tres etiquetas de nombres de la consulta.
- `BIOMETRICA`: `INFORMACION PERSONAL` con `Primer Apellido`, `Segundo
  Apellido` y `Nombres`, o la firma rotulada del mismo bloque.
- `DECLARACION_JURADA`: etiquetas `Apellidos`, `Nombres` y `Documento de
  Identidad`/`DNI`, con sus campos de cónyuge separados.
- `SUNARP`: marcadores registrales como `partida`, `asiento`, `cargo` o
  `identificado con`; el representante natural se considera solo si está
  ligado a su rótulo de documento; razón social, RUC y códigos no son personas
  naturales.
- `IDENTIDAD`: campos propios de una ficha de identidad, sin mezclar operadores
  ni pies.
- `PROSA`: nombres y DNI únicamente en patrones ya permitidos por el núcleo.
- `DESCONOCIDA`: nunca se descarta entera; solo produce candidatos con rótulo
  explícito y deja la procedencia para revisión.

Las únicas páginas descartadas enteras son las que una regla estructural
inequívoca clasifica como separador o SISGEN. Las cabeceras, marcas de agua, pies de consulta, pies legales y
bloques de resultados se eliminan del análisis de personas, no del texto plano
ni de la extracción de partidas/montos. Una cifra de ocho dígitos sin etiqueta
no es DNI. Ante duda, se conserva el candidato como `revision_manual` o no se
extrae; nunca se descarta en silencio.

### 5. Etiquetas con erratas OCR

La tolerancia se limita a etiquetas, no a valores. Primero se normalizan
Unicode, mayúsculas, espacios y puntuación. Después se usa una tabla cerrada
de variantes para `DNI`, `DNI.`, `D.N.I.`, `D.N.I. N°` y la observada
`D.N.1,`; el reemplazo `1 -> I` solo se admite en la posición exacta de
`D.N.1` y junto a su puntuación. Una alternativa es una distancia de edición
máxima uno únicamente contra esa etiqueta completa, con límites de palabra.

La captura exige inmediatamente después un rótulo permitido y exactamente
ocho dígitos (o el formato `CUI` de ocho dígitos, guion y control). Se rechazan
líneas marcadas como operador, usuario, consulta, transacción, verificación,
RUC, partida, teléfono o correo. No se convierten números aislados ni grupos
manuscritos separados por espacios. La prueba roja debe demostrar que la
errata entra y que el número del operador, la transacción, el teléfono y el
correo no entran.

### 6. Unificación segura

La normalización de nombre quita tildes, uniforma mayúsculas y espacios y
elimina puntuación periférica. El orden `APELLIDOS, NOMBRES` solo se reordena
cuando hay coma y el bloque cumple la forma rotulada; no se reordenan líneas de
prosa arbitrarias.

La prioridad de unificación es:

1. mismo documento exacto y nombre compatible en bloques distintos;
2. sin documento, mismo nombre completo normalizado y procedencia distinta;
3. cualquier semejanza difusa: nunca unificar; marcar `revision_manual`.

Si dos candidatos tienen nombres parecidos pero documentos distintos, quedan
separados. Si un mismo documento aparece con nombres incompatibles, quedan
separados y se informa conflicto para revisión; no se escoge una lectura.
Un nombre sin documento permanece visible como candidato sin documento hasta
que la notaría defina si participa en la confrontación. Esto evita convertir
una coincidencia aproximada en aprobación.

## Decisiones aplicadas

Las cinco aclaraciones del propietario están incorporadas en `spec.md`: SISGEN
se descarta completo; no hay migración; el cónyuge se conserva sin documento;
los grupos manuscritos separados no se unen; y las páginas desconocidas con
identidad posible se cuentan y listan por archivo y página, sin texto.

## Deuda explícita

- Un bloque visual menor que una página requiere coordenadas o un parser de
  formularios; no se construye hasta contar casos que lo necesiten.
- Partidas registrales de predios no están catalogadas en la referencia; se
  conserva el extractor histórico y no se amplían etiquetas por intuición.
- La persona jurídica no se modela en F11; solo se excluyen razón social, RUC y
  otros identificadores no naturales.
