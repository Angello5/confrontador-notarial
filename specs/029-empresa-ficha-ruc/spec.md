# F35 · Empresa y partidas contra los recaudos

**Fecha**: 2026-10-04  
**Estado**: implementado en el núcleo; cobertura con datos ficticios.  
**Alcance**: `nucleo/verificar.py`, `nucleo/correccion.py`, catálogo de reglas y pruebas puras.

## Origen

Una auditoría visual de los 10 expedientes de prueba encontró errores reales que la confrontación no veía:

- partidas escritas como «PARTIDA ELECTRÓNICA NÚMERO …» o «PARTIDA: …»;
- la razón social de una empresa mal escrita;
- el número de su domicilio legal cambiado.

También encontró partidas de antecedentes registrales que se exigían al borrador sin corresponder.

El usuario decidió el 2026-10-04 que la información del cliente está en los recaudos. Contra ellos se compara el borrador. La razón social y el domicilio legal de una empresa se corroboran contra su ficha RUC.

## Comportamiento implementado

- **Partida en todos sus formatos**:
  - Se lee tras `PARTIDA`, `PARTIDA ELECTRONICA`, `PARTIDA REGISTRAL`, `FICHA` o `FICHA REGISTRAL`.
  - El rótulo de número es opcional (`N°`, `NUMERO`, `NRO`), igual que los dos puntos.
  - Acepta el prefijo `P` de las partidas de predios (`P01234567`).
  - Una partida del borrador que no está en las fuentes produce `[PARTIDA]`, con la más parecida como «debe decir».
- **Partida exigible**: el FALTA de partida se limita a las partidas que menciona la minuta, como el de montos en F24. Las fuentes traen también antecedentes registrales (fichas anteriores, sucesiones) que no deben aparecer en el borrador. Sin minuta no hay FALTA de partida.
- **Ficha RUC**: de los recaudos se leen el RUC, la razón social y el domicilio fiscal. Se reconocen dos formatos:
  - el *Reporte de Ficha RUC* (razón social y, debajo, el RUC);
  - la constancia CIR (`FICHA RUC : <ruc>` y la razón social en hasta dos líneas).

  El domicilio se arma con vía, número, manzana, lote, departamento, interior, otras referencias y zona. Puede continuar en la página siguiente.
- **Razón social**: en el borrador se toman las palabras que preceden a cada forma societaria, abreviada o desarrollada (`E.I.R.L.`, `S.A.C.`, `S.C.R.L.`, `S.R.L.`, `S.A.A.`, `S.A.`). Se comparan con la razón social de la ficha sin su forma societaria. Si se parecen al menos un 85 % sin ser iguales, se emite `[RAZON_SOCIAL]` con el nombre de la ficha. Anclar la comparación a la forma societaria evita confundir un nombre de una palabra con otra palabra parecida (`TRANSFERIR`).
- **Domicilio fiscal**:
  - Se compara el domicilio que sigue al RUC en el borrador (`… <ruc>, CON DOMICILIO LEGAL EN …`) hasta el distrito, la provincia, el departamento o la representación.
  - Sus cifras deben estar en el domicilio de la ficha, y el número de la ficha debe estar en él.
  - Si no se cumple, se emite `[DOMICILIO_FISCAL]` con el domicilio de la ficha.
  - Una ficha sin cifras en su domicilio no permite comparar.

Las reglas están catalogadas en `nucleo/catalogo_reglas.toml` con versión `2026.10.04-1`. `RAZON_SOCIAL` y `DOMICILIO_FISCAL` tienen severidad ALTA.

La corrección automática se ofrece para la razón social y la partida, con la ficha o la fuente como respaldo. No se ofrece para el domicilio fiscal, porque la ficha lo trae en formato SUNAT y no en la redacción notarial.

## Medición

Se confrontaron sin guardar los 10 expedientes de prueba y se comparó el resultado con la corrida vigente:

- 4 errores reales más: 2 partidas, 1 razón social y 1 domicilio fiscal.
- 1 partida antes reportada como ausente, ahora señalada en su número incorrecto.
- 4 falsos positivos menos: partidas de antecedentes.
- Ningún falso positivo nuevo.

## Límites actuales

- **Formatos de ficha**: solo se leen los dos descritos. La consulta web de SUNAT y otras constancias no se leen.
- **Sin ficha RUC en los recaudos**: no se comprueban la razón social ni el domicilio de esa empresa. Ocurre, por ejemplo, con la entidad que otorga el crédito.
- **Razón social**: no se detectan una errata en la propia forma societaria, un nombre que el borrador escribe sin forma societaria ni un nombre al que le falte una palabra entera.
- **Domicilio fiscal**: se compara solo cuando sigue al RUC con «DOMICILIO EN», «DOMICILIO LEGAL EN» o «DOMICILIO FISCAL EN». No se distingue un cambio entre cifras que la ficha también tiene (por ejemplo, el piso por la oficina). La comparación es por cifras, no por nombre de vía.

## Verificación

`tests/test_empresa_ficha_ruc.py` usa fichas RUC inventadas en los dos formatos. Cubre:

- partidas con número, dos puntos, rótulo registral y prefijo de predio;
- FALTA de partida limitado a la minuta;
- razón social distinta, igual en forma abreviada o desarrollada, y de una sola palabra;
- domicilio con número cambiado y domicilio correcto;
- exclusión del domicilio fiscal de la corrección automática.
