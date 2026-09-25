# Catálogo de datos: la persona homogeneizada

Responde a una pregunta concreta: **¿se puede unificar lo que se extrae de los
recaudos en un solo esquema de persona, sea cual sea el documento de origen?**

Sí. Y la muestra dice además de dónde conviene sacar cada campo.

Base: los 10 expedientes reales de la notaría, 435 páginas pasadas por OCR
conservando la disposición en columnas, clasificadas por tipo con el núcleo
vigente y medidas con un instrumento **validado antes sobre páginas sintéticas
bien formadas** (100 % en las tres plantillas). Ningún dato personal aparece
en este documento; los ejemplos son ficticios.

Complementa a `docs/catalogo-fuentes.md`, que describe los documentos. Este
describe **los datos** y su fiabilidad.

## El esquema canónico

Un único registro de persona natural, independiente del documento de origen:

| Campo | Tipo | Normalización |
|---|---|---|
| `apellido_paterno` | texto | mayúsculas, Ñ conservada, tildes ignoradas |
| `apellido_materno` | texto | ídem |
| `nombres` | texto | ídem; puede tener varias palabras |
| `documento` | 8 dígitos | **conserva el cero inicial**; el CUI trae un dígito de control tras el guion que no forma parte del documento |
| `sexo` | enum | MASCULINO / FEMENINO |
| `fecha_nacimiento` | fecha | `dd/mm/aaaa` en origen → ISO |
| `estado_civil` | enum | SOLTERO / CASADO / VIUDO / DIVORCIADO, con género |
| `domicilio` | texto | dirección tal cual |
| `distrito` | texto | del domicilio, no del nacimiento |
| `conyuge` | texto | nombre completo; **sin documento** en la fuente |
| `procedencias` | lista | archivo y página de cada aparición |

Los formatos en que llega el nombre (`APELLIDO PATERNO / MATERNO / NOMBRES`,
`PRIMER / SEGUNDO APELLIDO`, `APELLIDOS / NOMBRES`, `APELLIDOS, NOMBRES`) se
proyectan todos sobre los tres campos canónicos. Cuando el origen trae
`APELLIDOS` sin separar, se conserva junto y se marca que la separación no es
de origen.

## Qué aporta cada documento, medido

Porcentaje de páginas del tipo en que la etiqueta lleva un valor legible.

| Campo | RENIEC consulta (28 pág.) | Biométrica (27) | Decl. jurada (81) | DNI escaneado (15) |
|---|---:|---:|---:|---:|
| `apellido_paterno` | **100** | **100** | 62 (junto) | — |
| `apellido_materno` | **100** | **100** | (junto) | — |
| `nombres` | **93** | **93** | 33 | — |
| `documento` | **100** | **100** | 57 | 7 |
| `estado_civil` | **100** | 89 | 36 | 40 |
| `fecha_nacimiento` | **96** | — | 25 | — |
| `sexo` | 82 | — | — | — |
| `domicilio` | **96** | — | 67 | — |
| `distrito` | **100** | — | 57 | 13 |
| `conyuge` | — | — | **35** | — |

Lecturas:

- **La consulta RENIEC y la ficha biométrica son fuentes completas y
  homogéneas.** Nombre, documento y estado civil al 89–100 %; la RENIEC añade
  fecha de nacimiento, sexo y domicilio. Son la columna vertebral del esquema.
- **El DNI escaneado es una fuente pobre**: documento legible en el 7 % de las
  páginas. Existe en el legajo, pero no hay que apoyarse en él: la misma
  persona aparece en su ficha RENIEC o biométrica con calidad total.
- **La declaración jurada es manuscrita** y rinde a medias (57–67 % en sus
  mejores campos). Aporta lo que nadie más da: **el cónyuge** (35 %) y la
  ocupación.
- La ficha biométrica lleva además un **QR con `nuDni`** que confirma el
  documento sin OCR (`docs/mediciones-ocr.md`).

## Orden de confianza por campo

Cuando el mismo campo llega de varios documentos, gana el de arriba:

1. **QR de la biométrica** para `documento`: exacto.
2. **Consulta RENIEC** y **biométrica**, campos etiquetados: 89–100 %.
3. **Declaración jurada**: complementa (`conyuge`, `ocupacion`), no manda.
4. **Prosa de minuta o escritura**: solo si no hay ficha; es lo que hoy mezcla
   comparecientes con personal de la notaría.
5. **DNI escaneado**: se ignora como fuente de identidad.

Dos personas con el mismo `documento` son la misma persona. Dos con nombres
parecidos y documento distinto, no. Ese criterio ya está en F11.

## Lo que el ERP guarda hoy y lo que deja escapar

F11 guarda `nombre`, `documento`, `procedencias` y `estado`. Con fiabilidad
del 89–100 % en las fichas oficiales se están **descartando** tres campos que
sí sirven para confrontar:

| Campo | Para qué serviría en la confrontación |
|---|---|
| `estado_civil` | Contrastar con "CASADO CON …" / "SOLTERO" de la minuta. Un casado que comparece solo es un error que hoy no se detecta. |
| `fecha_nacimiento` | Detectar minoría de edad y confirmar identidad cuando dos personas comparten nombre. |
| `domicilio` / `distrito` | Contrastar con "con domicilio en …" de la escritura. |

Y `conyuge`, que la declaración jurada da al 35 %, permite comprobar que el
cónyuge nombrado en la minuta es el declarado.

## Reglas que salen de la muestra

- El documento **puede empezar por cero** y siempre tiene ocho dígitos. Un
  número de ocho dígitos sin etiqueta no es un documento.
- El pie de las fichas oficiales trae **el RUC de la notaría al 100 %** y el
  número del operador: son contaminantes, no datos de la persona.
- Los apellidos con partícula (`DE LA CRUZ`) se conservan enteros (F11).
- El nombre se compara **ignorando tildes y conservando la Ñ** (F11).
- La misma página nunca aporta dos personas salvo la declaración jurada
  (declarante y cónyuge).

## Lo que la muestra no cubre

- Personas jurídicas: el esquema es de persona natural. Un representante de
  sociedad entra como persona natural con su documento; la sociedad no se
  modela.
- Partidas registrales de predios: no aportan identidades y no se catalogan
  aquí.
- Solo hay **un** expediente con errores sembrados; medir cuántos errores se
  detectan sigue pendiente de ese banco de pruebas.
