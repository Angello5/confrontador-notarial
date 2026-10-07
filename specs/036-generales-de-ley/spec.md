# F42 · Pestaña «Generales de ley»

**Fecha**: 2026-10-07  
**Estado**: implementado en la pantalla de confrontación y en los informes; cobertura con datos ficticios.  
**Alcance**: `expedientes/services.py` (`capa_de`, `resultado_de_corrida`), `templates/expedientes/confrontacion.html` y `static/js/reporte-docx.js`.

## Origen

El usuario pidió el 2026-10-07 que la pestaña «Identidad» pase a llamarse «Generales de ley», el término notarial para «toda la información del cliente». Hasta ahora esa pestaña solo recibía los documentos cruzados o sin titular. Los nombres, DNI, estado civil y domicilios caían en «Datos». En un expediente real la pestaña quedaba en 0 y «Datos» tenía las 6 observaciones.

## Comportamiento implementado

- **Generales de ley** (clave interna `IDENTIDAD`, sin cambios para no tocar el informe ni las preferencias guardadas) recibe:
  - las observaciones de persona (`DOCUMENTO_CRUZADO`, `DOCUMENTO_SIN_TITULAR`);
  - de las reglas, los campos del compareciente, sea persona natural o jurídica: `NOMBRE`, `DNI`, `SIN_FICHA`, `NOMBRE_MARCA_AGUA`, `RUC`, `RAZON_SOCIAL`, `DOMICILIO_FISCAL`, `ESTADO_CIVIL_DISCREPANTE`, `CONYUGE_NO_MENCIONADO`, `CONYUGE_BIEN_PROPIO`, `MENOR_DE_EDAD`, `DOMICILIO_NO_ENCONTRADO`, `DOMICILIO_HABILITACION`, `GENERO`, `PARTIDA` y `DIRECCION`.
- **Datos** conserva los datos del acto: `MONTO`, `NUMERO_EN_LETRAS`, `AREA`, `DATO_REGISTRAL`, `CORRELATIVO`, `COPROPIEDAD`, `ANEXO` y `PARRAFO`.
- La pestaña se decide al mostrar la corrida. No cambia los hallazgos guardados, su huella ni el catálogo de reglas, así que no se recalcula nada.
- El orden y la numeración de las observaciones no cambian: las correcciones propuestas siguen apuntando a la misma observación.
- El informe Word, el PDF imprimible y el Excel usan la misma agrupación.

## Decisión del usuario (2026-10-07)

- **`DIRECCION`** mezcla domicilios de personas y direcciones de inmuebles («domicilio o bien»), y **`PARTIDA`** puede ser la del poder inscrito del representante o la del inmueble. El usuario decidió que ambas van en «Generales de ley».
