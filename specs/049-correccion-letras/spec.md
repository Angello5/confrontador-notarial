# F66 · Letras mal escritas en la corrección automática

**Fecha**: 2026-11-02
**Estado**: implementado; cobertura con datos ficticios.
**Alcance**: `nucleo/correccion.py`, `nucleo/catalogo_reglas.toml` y `templates/expedientes/confrontacion.html`.

## Origen

Al aplicar correcciones, «TREINTA Y SEI (36)» salía bloqueada con «No admite corrección automática» aunque no hay duda de qué poner. El usuario pidió que se pueda corregir como las demás observaciones. F21 (FR-005) y F64 (FR-010) dejaban fuera todos los avisos de cifra y letras.

## Comportamiento

- **FR-001**: Una observación de cifra y letras (`NUMERO_EN_LETRAS`) o de área (`AREA`) es corrección automática solo si el núcleo la marcó como **letras mal escritas**: reparadas las palabras, las letras valen lo mismo que la cifra (F64). El erróneo es lo hallado y el correcto, la sugerencia.
- **FR-002**: Si cifra y letras valen distinto, sigue bloqueada aunque haya sugerencia: decide el abogado. Las cuotas (`COPROPIEDAD`) también siguen fuera.
- **FR-003**: La fuente de esta corrección es «Cifra del propio borrador», sin página: no hace falta que el texto aparezca en los recaudos. Es la única excepción a F21 FR-006.
- **FR-004**: En «Aplicar correcciones», la observación se marca y se muestra como las demás: lo hallado tachado → lo correcto, con sus apariciones.
- **FR-005**: Como en toda corrección (F21), el texto reemplazado queda como lo escribe el núcleo: en mayúsculas y sin tildes.
- **FR-006**: El catálogo de reglas sube a `2026.11.02-17`: las confrontaciones guardadas se recalculan, y así también muestran las sugerencias de F64 las que eran anteriores a ella.

## Seguridad

Sin cambios de permisos ni de datos: la decisión sigue siendo de la persona, que puede desmarcar la corrección, y el original no cambia.

## Verificación

- `tests/test_correccion.py` y `tests/test_correccion_expedientes.py`: se propone solo en el caso de FR-001, se aplica en el Word y el aviso sin página no muestra «página None».
- `tests/test_sugerencias_cifras.py`: las cuotas siguen fuera.
