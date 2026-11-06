# F69 · Sentido frente a la minuta: sin falsas alarmas por cortes y más legible

**Fecha**: 2026-11-02
**Estado**: implementado; cobertura con datos ficticios y medición con la capa activa en local.
**Alcance**: `nucleo/sentido.py`, `expedientes/sentido.py`, `templates/expedientes/_sentido.html`, `static/css/erp.css` y `nucleo/catalogo_reglas.toml`.

## Origen

El usuario vio que varias anotaciones eran falsas alarmas, con textos de la minuta cortados, y pidió otro enfoque y que se vea digerible. Eligió mantener la sección aparte, sin enmendar la constitución (principio I).

Medición en local, solo conteos: en EXP-72136, 9 anotaciones. Comparar oración contra oración fallaba cuando el corte caía distinto en cada documento, por la puntuación pegada, una cifra suelta o una letra suelta.

## Comportamiento

### Filtro

- **FR-001**: Antes de anotar, se busca el texto en el documento completo del otro lado. Si cada texto está en el otro, no hay anotación (F61, `esta_en`). F69 hace que esta búsqueda ignore:
  - la puntuación pegada a una palabra o sola (`EL.`, `,`);
  - las cifras sueltas, que juzgan las reglas (principio I);
  - las letras sueltas de lectura, salvo «Y», «O», «A», «E» y «U».
- **FR-002**: Sigue siendo un cambio real toda palabra agregada, quitada o cambiada: en medio o en el borde de la oración, incluida una negación.
- **FR-003**: «Y»/«O» y «NO»/«LO» ya no cuentan como la misma palabra mal leída (corrige F61).

### Pantalla

- **FR-004**: Cada anotación muestra solo las palabras que cambian, resaltadas, con 5 palabras de contexto a cada lado y «…» para lo demás. Si no hay nada que resaltar, muestra hasta 30 palabras.
- **FR-005**: No se resaltan la puntuación, las cifras sueltas, las letras mal leídas ni lo que hay tras un corte de oración. Lo agregado o quitado en un borde se resalta solo si no hay otra diferencia.
- **FR-006**: La cláusula completa, «Dice minuta» y «Dice proyecto», queda en un desplegable «Ver cláusula completa».
- **FR-007**: El informe no cambia.

### Recálculo

- **FR-008**: El catálogo sube a `2026.11.02-18`: los kardex se vuelven a confrontar y analizar, y dejan de mostrarse las anotaciones anteriores.

## Seguridad

Sin cambios: la capa sigue sin autoridad y no toca hallazgos, huella ni documento. La lógica nueva es código determinista, sin modelos. Lo que se muestra son tramos de las oraciones ya guardadas.

## Medición

| Medida en EXP-72136 | Antes | Después |
|---|---|---|
| Anotaciones | 9 | 3 |

Las 3 restantes tienen palabras distintas en medio o en el borde. Que sean errores jurídicos reales lo decide el abogado. Es un solo caso: falta medir con más kardex, y `specs/043-capa-sentido/spec.md` recoge la medición de los errores sembrados de F61, que no se repitió aquí con modelos reales.

## Verificación

- `tests/test_sentido_nucleo.py`: cortes, cifras y letras sueltas ignorados; negación, palabra cambiada en el borde, «Y»/«O» y varias palabras siguen siendo cambios; tramos de pantalla.
- `tests/test_sentido_expedientes.py`: la pantalla resalta lo que cambia y pliega la cláusula.
