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
  - `CHEQUE`:
    - El importe legible de cada cheque debe aparecer en el acta. El OCR lee «*****70.000.00» y se interpreta como 70,000.00.
    - Si el acta cita el número de un cheque, debe ser el de alguno de los cheques.
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

## [NEEDS CLARIFICATION]

- **Cheques:** no se comparan el banco ni el beneficiario («a la orden de»). ¿El beneficiario debe ser la transferente?
- **Sin cheques:** el precio no se coteja. ¿Debe compararse con otro medio de pago (constancia de transferencia)?
- **Otros documentos:** tarjeta de propiedad, SOAT, papeletas, copia literal y vigencia de poder se pueden subir, pero no tienen reglas propias.
- **Severidad:** las cuatro reglas son ALTA.

## Límites conocidos del motor general en actas vehiculares

- **Nombre que falta (falso):** el compareciente presentado como «PERUANO», sin «DE NACIONALIDAD», no se reconoce como nombre y sale como que falta.
- **Domicilio de los representantes:** se pide aunque el acta solo declara el de las empresas.
- **Estado civil:** con el nombre mal escrito, se toma de otra persona.
