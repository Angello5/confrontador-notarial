# F43 · Transferencia vehicular

**Fecha**: 2026-10-09  
**Estado**: implementado; cobertura con datos ficticios.  
**Alcance**: `Expediente.tipo` (migración 0011), submenú y lista en `expedientes/views.py` y `templates/`, `nucleo/vehicular.py`, lectura por filas de los PDF con capa de texto en `adaptadores/extraccion.py` y reglas nuevas en el catálogo.

## Origen

El usuario pidió el 2026-10-09 la transferencia vehicular:

- Va como submenú de «Kardex»: «Kardex» y debajo «Transferencia vehicular».
- No tiene minuta: se compara solo la información con el borrador (el acta).
- La información a comparar es la boleta informativa, los DNI de las partes y los cheques.

## Comportamiento implementado

- **Tipo de kardex.**
  - `Expediente.tipo` vale `NOTARIAL` (por defecto) o `VEHICULAR`.
  - El número es único entre los activos de su tipo: un acta vehicular puede repetir el número de un kardex notarial.
- **Navegación.** «Transferencia vehicular» cuelga de «Kardex» en el menú lateral y abre `/expedientes/vehicular/`, que lista y crea solo kardex vehiculares. Las migas y títulos de sus pantallas dicen «Transferencia vehicular».
- **Carga sin minuta.**
  - El kardex vehicular tiene dos zonas: «Información» (boleta informativa, DNI y cheques) y el borrador.
  - El servidor rechaza una minuta.
  - Para confrontar basta con la información y el borrador.
- **Lectura de PDF con capa de texto** (`_FORMATO_TEXTO` 5):
  - Se reconstruyen las filas como en el OCR: «Placa  : AXC000  OFICINA LIMA».
  - El texto en diagonal (marca de agua de las consultas en línea) se descarta.
  - La detección de capa dudosa no cambia.
- **Reglas vehiculares** (`nucleo/vehicular.py`, todas ALTA). Se lee la boleta informativa por sus rótulos.
  - `PLACA`: la placa del acta debe ser la de la boleta. Se ignoran guiones y espacios. Si el acta no la menciona, falta.
  - `PARTIDA`: la partida del vehículo debe aparecer. Si no, se observa la partida citada junto a la placa (hasta 400 caracteres después).
  - `VEHICULO`: marca, modelo, año, serie, VIN, motor, color, categoría y carrocería.
    - Se revisan solo si el acta los menciona junto a la placa (200 caracteres antes y 800 después).
    - Más lejos, «número de serie» es el de la foja notarial.
  - `PROPIETARIO`: el propietario registral debe aparecer en el acta. Si una ventana se le parece (≥ 85), sale «debe decir».
  - `PRECIO`: el acta debe indicar el precio, un importe con moneda hasta 400 caracteres después de «PRECIO». También si se paga por transferencia.
  - `CHEQUE`: el monto transferido con cada cheque debe aparecer en el acta. El OCR lee «*****70.000.00» y se interpreta como 70,000.00. No se comparan número, banco ni beneficiario.
- **Reglas del motor general** que siguen activas: nombres, DNI, RUC, estado civil, domicilio, género y la capa lingüística. En modo vehicular no se usan:
  - la regla general de partidas: las de los poderes no vienen en la información;
  - la regla general de montos: el precio se coteja con los cheques.
- **Pestaña**: las observaciones vehiculares van en «Datos».

Catálogo de reglas `2026.10.09-11`.

## Medición (kardex de ejemplo 35208, local, sin versionar)

- **Errores reales detectados:** el nombre mal escrito de un representante, el DNI truncado y el RUC de 9 dígitos.
- **Reglas vehiculares:** 0 falsos positivos.
  - Con errores sembrados en el acta (placa, partida y modelo), las tres se detectan.
- **El 71856**, único documento local con capa de texto, da los mismos hallazgos que antes con la lectura por filas.

## Decisiones del usuario (2026-10-09)

- **Cheques:** se compara el monto transferido; no se comparan número, banco ni beneficiario.
- **Precio:** debe estar en el acta, también cuando se paga por transferencia.
- **Severidad:** ALTA para las reglas vehiculares.

## [NEEDS CLARIFICATION]

- **Otros documentos:** tarjeta de propiedad, SOAT, papeletas, copia literal y vigencia de poder se pueden subir, pero no tienen reglas propias.

## Límites conocidos del motor general en actas vehiculares

- **Nombre que falta (falso):** el compareciente presentado como «PERUANO», sin «DE NACIONALIDAD», no se reconoce como nombre y sale como que falta.
- **Domicilio de los representantes:** se pide aunque el acta solo declara el de las empresas.
- **Estado civil:** con el nombre mal escrito, se toma de otra persona.

## F44 · Ajustes tras la primera prueba (2026-10-09)

- **Submenú.** «Transferencia vehicular» cuelga de «Kardex» con sangría, una guía vertical y letra menor (`.submenu`). Antes se veía como otra entrada del menú.
  F47 (`specs/039-menu-expedientes/spec.md`) lo reorganiza: el grupo se llama «Expedientes» y cuelgan de él «Kardex» y «Transferencia vehicular».
- **Informe Word.** En una transferencia vehicular, el resumen dice que se confrontó contra «la información de la transferencia (boleta informativa, DNI y cheques)». El pie dice «la información y el acta». Ya no menciona la minuta.
- **Catálogo** `2026.10.09-12`. La regla `PRECIO` entró sin subir la versión, así que las corridas hechas con la `-11` no la aplicaban; ahora se recalculan.

## F45 · Ajustes con dos actas reales más (2026-10-09)

Probado con dos kardex de transferencia locales (sin versionar). Cambios:

- **Acta en tabla** («MARCA:  X  MODELO:  Y»): el valor de una característica termina en el rótulo siguiente. Antes no se capturaba y un modelo mal escrito pasaba sin aviso.
- **Vehículo entregado a cuenta del pago:** las características se buscan desde la placa hasta el precio. Lo que sigue describe otro vehículo y daba 3 falsos positivos.
- **«AÑO MODELO 2027»** es el año, no el modelo.
- **Partida corta** (4 dígitos): sale «debe decir» en lugar de «falta».
- **Propietario persona natural:** la boleta lista apellidos y luego nombres. El mismo nombre en otro orden vale. Si solo se parece en otro orden, lo observa la regla NOMBRE con la ficha RENIEC, porque no hay corrección literal que proponer.
- **RUC sin ficha RUC entre la información:** pasa a aviso MEDIA («Sin ficha RUC en los recaudos»). Antes salía como ALTA «no coincide con ninguna fuente».
- **Nombres con «, PERUANO,»:** se reconocen como compareciente, como «DE NACIONALIDAD». Hasta 6 palabras; se quitan «ENTRE» y «CELEBRADA» de los bordes. Daba un falso «Nombre no aparece» (ALTA) en las tres actas.
- **Lista notarial:** se suman TRANSFERENTE, ADQUIRENTE, ADQUIRIENTE, CANCELATORIO y SOAT.
- **Constancia de depósito (abono):** su monto también debe constar en el acta, como el de un cheque. Lo decidió el usuario el 2026-10-09. En pantalla el campo se llama «Medio de pago».
- **Domicilio en un rango de numeración:** el acta dice «AV. X 1537» y RENIEC «AV. X 1501-1551». El usuario confirmó que es un error, y ya sale como «domicilio no encontrado».

- **Dirección del oficio notarial.** El tramo «UBICADO EN» del oficio notarial llegaba hasta el domicilio de la parte y salía como «Dirección» ALTA. Ahora un tramo termina en el rótulo siguiente y la dirección del oficio notarial no se compara. Además, «COOP.» se lee como COOPERATIVA, lo que quita también un falso «domicilio no encontrado».

- **Imagen con la extensión de otro formato.** Un JPEG guardado como .png se rechazaba porque el contenido no coincidía con la extensión. Ahora una imagen vale con la firma de cualquier formato de imagen admitido, porque el OCR lee el contenido. Un PDF o un archivo que no es imagen con extensión de imagen se sigue rechazando.

Catálogo `2026.10.09-14`.

**Regresión:**
- Los 12 borradores notariales locales dan los mismos hallazgos.
- La transferencia de ejemplo pierde 2 falsos positivos.

**Pendiente** (motor general):
- el DNI electrónico fotografiado no se lee como ficha (el cónyuge queda «sin ficha»);
- la numeración de los firmantes («1.- 2.- 3.-») se lee como cláusulas.
