# F37 · Domicilio contractual y tipo de habilitación

**Fecha**: 2026-10-05  
**Estado**: implementado en el núcleo; cobertura con datos ficticios.  
**Alcance**: `nucleo/verificar.py` (regla F12 de domicilio), `expedientes/services.py` (paso de la minuta y rótulo de la referencia) y catálogo de reglas.

## Origen

La auditoría visual de los 10 expedientes de prueba encontró 15 alertas de domicilio: 10 falsas y 5 dudosas. La mayoría se debía a que la comparecencia usa el domicilio que la minuta fija «para efectos de este contrato», no el de RENIEC. El usuario decidió el 2026-10-05:

1. El domicilio contractual que fija la minuta es válido en la comparecencia.
2. El domicilio de la declaración jurada (un recaudo) también es válido.
3. Si el domicilio coincide pero omite o cambia el tipo de habilitación (asentamiento humano, pueblo joven…), corresponde un aviso leve, no un domicilio distinto.

## Comportamiento implementado

- **Domicilio contractual**:
  - De la minuta se leen los domicilios que siguen a «(CON | SEÑALANDO) DOMICILIO PARA (LOS) EFECTOS DE ESTE / DEL PRESENTE CONTRATO EN …», hasta el distrito, la provincia, el departamento u otro domicilio.
  - El domicilio de una persona con ficha se da por encontrado si su línea en el borrador contiene el de RENIEC o uno contractual.
  - No se lee la remisión genérica a «los domicilios indicados en la introducción», porque no fija una dirección.
- **Tipo de habilitación**:
  - Primero se compara sin las palabras del tipo de habilitación: asentamiento humano, pueblo joven, urbanización, asociación, cooperativa, conjunto habitacional, agrupación familiar.
  - Si así coincide, se emite `DOMICILIO_HABILITACION`, de severidad MEDIA, con el domicilio esperado y su referencia («RENIEC» o «Minuta»).
  - «P.J.» se lee como «PUEBLO JOVEN», igual que «ASENT.H.» como «ASENTAMIENTO HUMANO».
- **Sin coincidencia**: se mantiene `DOMICILIO_NO_ENCONTRADO`, con las excepciones previas (representación y observación F22 ya emitida).

Catálogo de reglas `2026.10.05-3`.

## Medición

Confrontación en memoria de los 10 expedientes de prueba, acumulada con la ampliación de F16 del mismo día:

- desaparecen 14 alertas de domicilio, las 10 falsas y 4 de las 5 dudosas;
- quedan 2: una ficha RENIEC con OCR dañado y una declaración jurada manuscrita;
- no hay hallazgos nuevos;
- el expediente con errores sembrados sigue con 8 de 8.

## Límites

- **Declaración jurada**: la decisión 2 no se aplica todavía. Las declaraciones juradas del lote son manuscritas y el OCR no recupera su dirección (ni cifras ni nombre de vía), así que el domicilio declarado no se puede leer.
- **Alcance del domicilio contractual**: se acepta para cualquier persona. La minuta lo suele fijar para «todos» o para una parte, y no se distingue a quién corresponde cada uno.
- **Dirección RENIEC en dos líneas**: se sigue leyendo solo la primera línea. Completarla exige una comparación tolerante al ruido OCR y queda para un cambio aparte.

## Verificación

`tests/test_domicilio_contractual.py` usa datos inventados. Cubre:

- la lectura de domicilios contractuales;
- el domicilio contractual válido, que sin la minuta sigue marcándose;
- el tipo de habilitación omitido o cambiado como aviso leve;
- el domicilio completo sin aviso.

## F58 · Domicilio leído por OCR con puntuación alterada

**Fecha**: 2026-10-20  
**Alcance**: `nucleo/verificar.py` (`_direccion_palabras`, compartida por la regla de domicilio, la de direcciones y el vocabulario de las fuentes) y catálogo de reglas.

### Origen

En un kardex real salía `DOMICILIO_NO_ENCONTRADO` (MEDIA) aunque el borrador traía el domicilio dos veces, abreviado y desarrollado. La ficha RENIEC escaneada se había leído con dos alteraciones del OCR, del tipo `ASENT, H. … MZ. OLT.` (coma en lugar de punto y la letra de la manzana pegada a «LT»). La minuta y otra página del recaudo decían `ASENT. H. … MZ. O LT. …`.

### Diagnóstico

`_direccion_palabras` reconocía «ASENT.H.» y «AA.HH.» solo con punto, y separaba el número pegado a su abreviatura («LT6») pero no la letra pegada a «LT». De la ficha quedaban dos palabras sin pareja en el borrador: «H» y «OLT».

### Comportamiento implementado

- «ASENT, H.» y «AA, HH» se leen como «ASENTAMIENTO HUMANO», igual que con punto.
- Tras «MZ», una sola letra pegada a «LT» se separa: «MZ. OLT.» y «MZ.OLT7» se leen «MANZANA O LOTE» (y el número, si lo hay).
- El cambio está en la función compartida, así que vale para todo domicilio y dirección que se compare con ella.
- Un domicilio distinto (otra habilitación, manzana o lote) se sigue observando.
- Catálogo de reglas `2026.10.20-16`: las confrontaciones guardadas se recalculan.

### Límites

- Solo se separa una letra pegada a «LT» justo después de «MZ». Una manzana de dos caracteres pegada («MZ. A1LT») sigue sin separarse.
- Otras lecturas OCR de la abreviatura («ASENT; H», «A.HH») no se cubren.

### Medición

Medición privada, solo lectura, main frente a esta rama:

- **Base local** (10 expedientes, dos de ellos cargas del caso de referencia): el kardex del reporte pasa de 1 a 0 `DOMICILIO_NO_ENCONTRADO`; los demás no cambian.
- **9 casos de prueba** con el OCR propio del guion: mismas observaciones de personas en main y en la rama.
- `comparar_f19.py`: mismos recuentos por campo (40 observaciones de regla).
- El caso de referencia sigue con 8 de 8 en las dos cargas.

### Verificación

`tests/test_personas.py`, con datos inventados:

- «ASENT, H.» y «AA, HH» entre las equivalencias cerradas;
- `_direccion_palabras` con coma, con la letra pegada a «LT» y con el número pegado, y sin partir una palabra tras «MZ»;
- la regla de domicilio no observa la ficha alterada frente al borrador abreviado o desarrollado, y sí observa un domicilio distinto.
