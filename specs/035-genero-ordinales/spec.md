# F41 · Concordancia de género con RENIEC y ordinales mal escritos

**Fecha**: 2026-10-05  
**Estado**: implementado en el núcleo; cobertura con datos ficticios.  
**Alcance**: `nucleo/verificar.py`, traducción de observaciones en `expedientes/services.py`, catálogo de reglas y nombre del campo en pantalla.

## Origen

El usuario pidió el 2026-10-05 seguir con dos pendientes de F39:

- **Concordancia de género con la ficha RENIEC.** En un expediente de prueba, el borrador usa el femenino para un otorgante varón («LA OTORGANTE», «QUEDANDO ADVERTIDA»).
- **Números de cláusula mal escritos.** En un borrador con errores sembrados, «OCTAO:» y «DECIO:» no se reconocían como ordinales. La numeración marcaba un salto engañoso en la cláusula siguiente y «DECIO» pasaba sin aviso: el diccionario lo acepta como nombre propio.

## Comportamiento implementado

- **Sexo de RENIEC**:
  - Se lee el rótulo «Sexo:» de la consulta RENIEC y solo vale MASCULINO o FEMENINO.
  - `Persona` suma `sexo` y `procedencia_sexo` al final, y la fusión de registros los conserva.
  - Sin sexo legible no se revisa nada.
- **Comparecencia de cada persona** (`GENERO`, MEDIA):
  - Se revisa el tratamiento justo antes del nombre (SEÑOR/SEÑORA, DON/DOÑA, SR./SRA.).
  - Después del nombre y hasta el de otra persona con ficha, se revisa el primer IDENTIFICADO/A, el primer DOMICILIADO/A y el primer estado civil (CASADO/A, SOLTERO/A, VIUDO/A, DIVORCIADO/A). El segundo estado civil de la línea es de otra persona.
  - No cuentan:
    - el participio después de «haber» o «sido» («haberse identificado» es invariable);
    - los plurales;
    - «de nacionalidad peruana».
- **Fórmulas del notario** (`GENERO`, MEDIA):
  - Son «EL/LA (MISMO/A) OTORGANTE», «EL/LA COMPARECIENTE», «QUEDANDO ADVERTIDO/A», «EL/LA BENEFICIARIO/A FINAL» (con artículo: «sobre beneficiario final» nombra la declaración) y «ESTÁ IDENTIFICADO/A».
  - Se revisan solo si todos los comparecientes con ficha tienen el mismo sexo según RENIEC. Si hay uno con sexo ilegible, o de ambos sexos, no se puede decidir.
  - Los términos del contrato («EL CLIENTE», «EL MUTUATARIO») son definidos y no se revisan.
- **Mensaje**: «<nombre>: <lo hallado>» y «RENIEC: MASCULINO («<forma correcta>»)», con la fuente de la ficha. La fórmula se ubica en el borrador. No hay corrección automática.
- **Ordinal mal escrito** (`CORRELATIVO`, MEDIA):
  - Un rótulo de cláusula que no es un ordinal válido pero se parece al que toca en la numeración (parecido ≥ 85) sale como «OCTAO: debe decir OCTAVO:».
  - Cuenta como ese ordinal, así la cláusula siguiente no salta.
  - Se exige al menos una cláusula antes («PRIMA:» de un seguro se parece a «PRIMERA»). No se marca el plural del ordinal («TERCEROS:»).

Catálogo de reglas `2026.10.05-10`.

## Medición

Confrontación en memoria de los 11 expedientes de prueba, más el borrador con errores sembrados que subió el usuario:

- **Género**:
  - En el expediente con el otorgante varón salen las 5 fórmulas en femenino: «LA OTORGANTE», «LA MISMA OTORGANTE», «QUEDANDO ADVERTIDA», «LA BENEFICIARIA FINAL» y «ESTA IDENTIFICADA».
  - En los demás no hay ninguna.
  - La revisión por persona reconoce el tratamiento y los participios de las 19 personas con sexo legible cuyo nombre está en la comparecencia: sin errores en estos borradores.
- **Ordinales**:
  - En el borrador sembrado, «OCTAO:» y «DECIO:» salen con su corrección.
  - El salto engañoso de «NOVENO:» desaparece. «DECIO» no se detectaba antes.
- **Resto**: la regla y las personas no cambian.

## Límites

- Si el nombre del borrador está mal escrito, no se ubica la comparecencia de esa persona y no se revisa su género. Su nombre ya sale observado.
- Las ocupaciones (ABOGADO/A, EMPRESARIO/A…) no se revisan.
- Un compareciente sin ficha RENIEC no cuenta para decidir el sexo de las fórmulas.

## [NEEDS CLARIFICATION]

- **Severidad**: MEDIA por defecto. ¿Debe ser ALTA?
- **Ocupaciones**: ¿se revisan también?

## Verificación

- `tests/test_genero.py`:
  - la lectura del sexo;
  - la comparecencia en el otro género, con «haberse identificado» y el estado civil de otra persona;
  - las fórmulas con un solo otorgante, con «sobre beneficiario final» y «el cliente»;
  - sin fórmulas con comparecientes de ambos sexos o con sexo ilegible.
- `tests/test_reglas_f30.py`: el ordinal mal escrito y los rótulos parecidos que no son ordinales («PRIMA:», «SEGUN:», «TERCEROS:»).
- `tests/test_personas.py`: `Persona` suma sus campos al final.
