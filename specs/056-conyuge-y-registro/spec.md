# F74 · DNI del cónyuge y registro de otra entidad

**Fecha**: 2026-11-06
**Estado**: implementado; cobertura con datos ficticios.
**Alcance**: `nucleo/verificar.py`, `nucleo/catalogo_reglas.toml` y `tests/test_reglas_f30.py`.

## Origen

Los usuarios validaron el sistema con casos reales y reportaron:

1. En transferencias vehiculares, el sistema propone cambiar «Registro de Personas Jurídicas», válido para la empresa del acto, por «Registro de Propiedad Vehicular».
2. En kardex de personas casadas, con la redacción «DON X.- CASADO CON DOÑA Y, … IDENTIDAD NUMERO …», el sistema asigna a la esposa el DNI del esposo y genera una alerta de severidad alta.

## Comportamiento

- **FR-001**: Un registro del borrador que pertenece al otro grupo que el de las fuentes no se observa. Los grupos son registros de bienes (Predios, Propiedad Inmueble, Propiedad Vehicular, Bienes Muebles) y registros de personas (Personas Jurídicas, Personas Naturales, Sociedades, Mandatos y Poderes, Testamentos, Sucesiones Intestadas). Ese registro describe a otra entidad del acto, no al bien.
- **FR-002**: Entre registros del mismo grupo se mantiene la regla de F30: con un único registro en las fuentes, ese es el esperado.
- **FR-003**: Sin observación no hay corrección automática del registro, así que «Aplicar correcciones» ya no lo cambia.
- **FR-004**: El nombre que sigue a «CASADO(A) CON» es una mención del cónyuge: nunca se empareja con el DNI de esa línea ni de esa página. El DNI queda para quien comparece o, si no se identifica, sin titular, como antes.
- **FR-005**: Si esa misma persona comparece con su propio nombre y DNI («DOÑA Y, DE NACIONALIDAD PERUANA, … IDENTIFICADA CON … NUMERO …»), su DNI se le asigna como hasta ahora.
- **FR-006**: Se sube la versión del catálogo para que las confrontaciones guardadas se recalculen con estas reglas.

## Decisión que reemplaza

F30 observaba «Registro de Personas Jurídicas» frente a «Registro de Predios». Por el reporte de los usuarios, ese registro es válido para otra entidad del acto y ya no se observa.

## Fuera de alcance

La ausencia del botón «Aplicar correcciones» en otros casos se revisará con un caso real. Hoy el botón solo aparece cuando hay un «debe decir» con su valor en las fuentes; las observaciones de generales de ley y los avisos de falta no proponen corrección. Que un DNI cruzado real proponga su corrección sería una regla nueva.

## Seguridad

Sin cambios de permisos ni datos. Las pruebas usan solo nombres y números ficticios.

## Verificación

- `tests/test_reglas_f74.py`: registro de otra entidad, mismo grupo, cónyuge en la línea del DNI y cónyuge que comparece.
- `tests/test_reglas_f30.py`: actualizado según FR-001.
