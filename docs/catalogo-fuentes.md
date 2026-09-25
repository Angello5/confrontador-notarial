# Catálogo de fuentes documentales

Qué documentos llegan a la confrontación, cómo se presenta en cada uno la
identidad de las personas, y qué datos **no** son de los comparecientes.

Salió de examinar 10 expedientes reales de la notaría: 75 archivos y **las 435
páginas** de todos los PDF, pasadas por OCR y agrupadas por forma. Todos los
ejemplos de este documento son **ficticios**: reproducen la disposición y las
etiquetas de los documentos reales, con nombres inventados y números de
documento del rango 9000xxxx, que está por encima de los emitidos.

## Por qué existe este documento

La capa de regla se diseñó leyendo escrituras, que son prosa: `JUAN PÉREZ, DE
NACIONALIDAD PERUANA, DNI 12345678`. Pero **los documentos del cliente son
formularios**, y cada emisor usa etiquetas distintas para lo mismo. Sin un
catálogo, cada variante nueva se descubre cuando un notario ve un resultado
raro.

Además, el problema más grave encontrado no es que falte un dato: es que
**sobran datos de personas que no son parte del acto** y el sistema los trata
como si lo fueran.

## Hecho transversal: no todo número de 8 dígitos es un DNI

Los documentos oficiales peruanos llevan, además de los datos del ciudadano,
metadatos de quién emitió o consultó el documento. Se ha comprobado que
conviven en la misma hoja:

| Dato | Forma | A quién pertenece |
|---|---|---|
| DNI del compareciente | 8 dígitos, puede empezar por 0 | La parte del acto |
| Documento del operador | 8 dígitos | El empleado de la notaría que hizo la consulta |
| RUC de la entidad | 11 dígitos | La notaría |
| Número de transacción | 10 dígitos | El sistema emisor |
| Código de verificación | 8 dígitos | El sistema emisor |
| Número de partida | 8 dígitos | El predio o la sociedad |
| Teléfono | 9 dígitos | El compareciente, pero no es su documento |
| Cifras dentro de un correo | 8 dígitos | Nada |

**Un número de 8 dígitos aislado no identifica a nadie.** Solo cuenta como DNI
si lo acompaña una etiqueta que lo diga, y si no está dentro de un bloque de
metadatos.

### Bloques que deben excluirse antes de extraer

- **Marca de agua diagonal repetida**: lleva el nombre y el número del empleado
  que hizo la consulta, superpuestos a toda la página.
- **Cabecera con el nombre del notario**.
- **Pie "Información de Consulta"** o **"Información de Consulta Dactilar"**:
  usuario, entidad, fecha y número de transacción.
- **Pie legal** de SUNARP sobre responsabilidad y plazos.

Sin excluirlos, el catálogo mezcla al ciudadano con el personal de la notaría,
y la confrontación puede dar por buena una identidad que no corresponde.


## Censo: qué hay en 435 páginas

Agrupadas por las marcas estructurales que contiene cada una.

| Páginas | Tipo |
|---:|---|
| 62 | Consulta de coincidencias SISGEN |
| 38 | Página en blanco o separador de escaneo |
| 32 | Ficha de autenticación biométrica |
| 30 | Consulta en línea RENIEC |
| 30 | Declaración jurada de conocimiento del cliente |
| ~90 | Partidas y certificados SUNARP, en varias combinaciones |
| ~60 | Prosa notarial: minuta y proyecto |
| ~30 | Poderes y facultades |
| 17 | Documento nacional de identidad escaneado |
| 3 | Vehicular |
| 6 | Sucesión intestada / municipal |

Dos cifras que condicionan el diseño:

- **38 páginas en blanco**, casi una de cada diez. Son separadores del escáner.
  El OCR gasta tiempo en ellas y no aportan nada.
- **62 páginas de SISGEN**, el tipo más numeroso del corpus, y ninguna de ellas
  aporta identidades del acto.

## Los tipos encontrados

### 1. Consulta en línea RENIEC — "Informe de la Consulta"

Dos columnas de `Etiqueta: valor`, con foto, firma y huellas.

```
CUI:                 90000011 - 5
Apellido Paterno:    LUMARIA
Apellido Materno:    ZURBELIA
Nombres:             ALBA
Sexo:                <sexo>
Fecha de Nacimiento: 01/01/1970
Estado Civil:        CASADO
```

- **Una sola persona** por documento.
- El documento aparece como **CUI**: 8 dígitos, espacio, guion, dígito de
  control. **No** lleva la etiqueta `DNI`.
- El DNI puede **empezar por cero**.
- Contaminantes: marca de agua con el operador, cabecera del notario, pie de
  consulta.

### 2. Ficha de autenticación biométrica de la notaría

```
INFORMACIÓN PERSONAL
DNI                90000011
Primer Apellido    LUMARIA
Segundo Apellido   ZURBELIA
Nombres            ALBA
```

Y al pie de la firma, el mismo nombre en otro orden:

```
LUMARIA ZURBELIA, ALBA
DNI 90000011
```

- **Una sola persona**.
- Etiquetas **distintas** de las de RENIEC: `Primer Apellido` y `Segundo
  Apellido` en vez de `Apellido Paterno` y `Apellido Materno`.
- Aparece el formato **`APELLIDOS, NOMBRES`** separado por coma.
- Contaminante grave: `Operador: 90000099 - <nombre del empleado>`, con un
  número de 8 dígitos indistinguible de un DNI.

### 3. Declaración jurada de conocimiento del cliente — rellenada a mano

Formulario impreso con los valores **manuscritos**.

```
1. Apellidos:  LUMARIA ZURBELIA          2. Nombres:  ALBA
3. Documento de Identidad:  DNI N°:  9000 00 11
8. Número de Teléfono: 900000001      9. Correo: 19000001ejemplo@correo.com
11. Nombres y Apellidos del cónyuge:  NEBULOSA FICTICIA VENTORIA
```

- **Dos personas**: el declarante y su cónyuge. El cónyuge aparece con nombre
  pero **sin documento**.
- Tercer juego de etiquetas: `Apellidos` y `Nombres`, sin distinguir paterno de
  materno.
- **El DNI manuscrito viene con espacios** (`9000 00 11`). Es el origen de los
  fragmentos de 6 y 7 dígitos que aparecían en el catálogo.
- El teléfono (9 dígitos) y las cifras del correo (8 dígitos) son candidatos
  falsos.
- **La escritura a mano es la fuente menos fiable para el OCR** de todas las
  encontradas.

### 4. Certificado de vigencia SUNARP — persona jurídica

Prosa registral, no formulario.

```
Que, en la partida electrónica N° 80000001 del Registro de Personas Jurídicas
de la Oficina Registral de <ciudad>, consta registrado y vigente el nombramiento
a favor de TELURIO VENTORIA, BRUNO, identificado con DNI. N° 90000022

DENOMINACIÓN O RAZÓN SOCIAL: GRUPO EJEMPLO ASOCIADOS
ASIENTO: B00001
CARGO: GERENTE GENERAL
```

- Interviene una **persona jurídica** representada por una persona natural. El
  núcleo no modela hoy esa distinción.
- Nombre en formato **`APELLIDOS, NOMBRE`** con coma.
- El documento se rotula **`DNI.`** con punto, forma que la regla actual **no
  reconoce**.
- Contaminantes: `Código de Verificación` (8 dígitos) y el número de partida
  (8 dígitos).


### 6. Consulta de coincidencias SISGEN — el caso más peligroso

Es el tipo **más numeroso del corpus**: 62 de 435 páginas.

```
CONSULTA REALIZADA
Fecha:                     16/09/2026 16:10:21
Documento Identificativo:  D.N.I. 90000011
Coincidencias:             0
Nombre:
N. Consulta:               80000003
```

Cuando hay coincidencias, la página **lista entidades de listas restrictivas**:

```
1.- (564) OTRO - Porcentaje de similitud: 70%
   Nombre:                   EMPRESA FICTICIA SAC
   Documento identificativo: RUC 20000000001
   Delito/Cargo:             ...
   Lista Origen:             ...
```

**Esas personas y empresas NO son parte del acto.** Son coincidencias por
parecido de nombre en listas de vigilancia. Si entran al catálogo, la escritura
se estaría confrontando contra identidades de una lista de sancionados.

De 62 páginas, 30 tienen cero coincidencias y al menos una tiene dos. Es decir:
el caso peligroso es **poco frecuente pero real**, que es la peor combinación,
porque no aparece al probar con dos o tres expedientes.

Qué aporta y qué contamina:

| Dato | Uso |
|---|---|
| `Documento Identificativo` | El documento consultado, pero **sin nombre al lado**: no se puede atribuir a nadie, así que la página se descarta entera. Ese número aparece con su nombre en la ficha RENIEC y en la biométrica del mismo legajo. |
| `N. Consulta` | 8 dígitos, **no es un documento** |
| Bloques `1.-`, `2.-` de coincidencias | Terceros ajenos: **excluir** |
| Pie con usuario y notaría | **Excluir** |

## El OCR corrompe las propias etiquetas

En una página SISGEN real, el documento del compareciente **no se captura**, y
no por culpa del patrón:

```
DOCUMENTO IDENTIFICATIVO: D.N.1,   ← la I se leyó como 1 y el punto como coma
```

La etiqueta llega corrompida, así que cualquier regla que dependa de reconocerla
exactamente falla. Esto vale para todos los tipos: **la tolerancia a erratas de
la etiqueta es tan importante como la variedad de etiquetas**.

### 5. Minuta y proyecto de escritura

Prosa notarial densa, 4.000 a 7.000 caracteres por página. Es el formato para
el que se diseñó la capa de regla y **funciona**: `NOMBRE, DE NACIONALIDAD
PERUANA`, `CASADO CON NOMBRE,`.

## Formas de rotular el documento de identidad

Comprobado contra la implementación actual:

| Forma | Origen | ¿Se reconoce hoy? |
|---|---|---|
| `DNI 90000011` | ficha biométrica | sí |
| `DNI N°: 90000011` | declaración jurada | sí |
| `DNI Nº 90000011` | variante de la letra N | sí |
| `D.N.I. N° 90000011` | prosa | sí |
| `identificado con DNI 90000022` | prosa | sí |
| `DNI. N° 90000022` | SUNARP | **no** |
| `CUI: 90000011 - 5` | consulta RENIEC | **no**, salvo en imágenes |
| `DNI N°: 9000 00 11` | manuscrito | **no** |

## Formas de presentar el nombre

| Forma | Origen |
|---|---|
| `Apellido Paterno` / `Apellido Materno` / `Nombres` en líneas separadas | consulta RENIEC |
| `Primer Apellido` / `Segundo Apellido` / `Nombres` en líneas separadas | ficha biométrica |
| `Apellidos` / `Nombres`, sin separar paterno de materno | declaración jurada |
| `APELLIDOS, NOMBRES` en una línea con coma | firma biométrica, SUNARP |
| `NOMBRE COMPLETO, DE NACIONALIDAD` | minuta y escritura |
| `CASADO CON NOMBRE COMPLETO` | minuta y escritura |

## Cuántas personas trae cada documento

Esto condiciona el diseño: **no basta con extraer una persona por archivo**.

| Documento | Personas del acto | Personas ajenas al acto |
|---|---|---|
| Consulta RENIEC | 1 | operador, notario |
| Ficha biométrica | 1 | operador, notario |
| Declaración jurada | 2 (declarante y cónyuge) | — |
| Certificado SUNARP | 1 natural + 1 jurídica | — |
| Legajo de recaudos | **varias**, una por bloque | operador, notario |

Un legajo reúne varios de estos documentos en un solo PDF, así que la
extracción debe **segmentar por bloques** antes de asociar nombre y documento.
Unir el nombre de un bloque con el número de otro produce un cruce de
identidades con apariencia de certeza, que es el peor resultado posible.

## Qué queda pendiente de decidir

- **Persona jurídica**: el núcleo solo modela personas naturales. Un acto con
  una sociedad representada necesita un concepto nuevo.
- **Cónyuge sin documento**: aparece con nombre y sin DNI. Hay que decidir si
  se verifica y contra qué.
- **DNI manuscrito con espacios**: si se juntan los grupos, se arriesga a unir
  números que no van juntos. Conviene medirlo antes de decidir.
- **Partidas registrales de predios**: no se han catalogado todavía sus
  etiquetas.
