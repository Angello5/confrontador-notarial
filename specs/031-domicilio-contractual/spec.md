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
