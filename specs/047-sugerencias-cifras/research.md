# Research · F64 Sugerencias en cifras y cuotas

## 1. Dónde va la sugerencia

- **Decision**: al final de la observación, entre paréntesis, después del «debe decir» de siempre (ver [contracts/observaciones.md](contracts/observaciones.md)).
- **Rationale**: `nucleo/correccion.py` y el adaptador leen solo `[CAMPO] «hallado» debe decir «esperado»`; la cola no los afecta. Las observaciones guardadas no tienen cola y se siguen viendo como hoy (FR-009).
- **Alternatives considered**: cambiar el «debe decir» por el texto sugerido (rompe la comparación con las corridas guardadas y las estadísticas de errores); un campo nuevo en la base (migración sin necesidad).

## 2. Letras mal escritas

- **Decision**: cada palabra del tramo en letras que no está en el vocabulario se cambia por la más parecida (`rapidfuzz`, el mismo puntaje mínimo de 75 con que `_cola_en_letras` ya la acepta). Una palabra numérica pegada a «Y» («TREINTAY») se separa. Si el valor resultante es la cifra, se sugiere ese texto; si hay empate entre dos palabras con distinto valor, no se sugiere.
- **Rationale**: reutiliza el reconocimiento que ya existe; no inventa: solo se sugiere si las letras corregidas y la cifra coinciden.
- **Alternatives considered**: generar las letras desde la cifra (cambiaría también palabras bien escritas y el estilo del proyecto).

## 3. Escribir un número en letras

- **Decision**: `letras_de(n)` para enteros de 0 a 999 999 999 999, en mayúsculas sin tildes, como el texto normalizado que ya compara el núcleo («TREINTA Y SEIS», «VEINTIUNO», «CIENTO UNO», «UN MILLON»). Antes de «SOLES» o «DOLARES», «UNO» final pasa a «UN». Los céntimos se escriben como en el proyecto («Y 50/100»); con decimales en «PUNTO» o «COMA» se sugiere solo la cifra.
- **Rationale**: es el inverso de `numero_en_letras`; la prueba de ida y vuelta (`numero_en_letras(letras_de(n)) == n`) lo valida en todo el rango.
- **Alternatives considered**: `num2words` (dependencia nueva para 25 líneas).

## 4. Cuándo la minuta «trae el dato»

- **Decision**: se reúnen los valores de la minuta con la misma unidad: porcentajes (cifra con % o letras con «POR CIENTO»), montos (`montos_de`), áreas (las mismas expresiones del área) y, sin unidad, solo los pares «letras (cifra)». Desempata si contiene exactamente uno de los dos valores del proyecto.
- **Rationale**: un número suelto sin unidad aparece en fechas, DNI y partidas; exigir el par evita desempates falsos.
- **Alternatives considered**: buscar por concepto (precio, plazo): F30 ya lo hace para montos y no cubre porcentajes ni plazos.

## 5. Reconocer un reparto en todos los actos

- **Decision**: una oración con dos o más porcentajes es un reparto si cada porcentaje va precedido, en su tramo, por el nombre de una parte de los recaudos, o si la oración usa términos de reparto: copropiedad, cuota, acciones y derechos, acciones, participaciones, aporte, herencia, heredero, legítima. Nunca si usa interés, mora, penalidad, tasa, comisión, descuento, IGV o impuesto. Se mantienen «CADA UNO», el 200 % y la cuota que suma las demás.
- **Rationale**: es el criterio que confirmó el usuario; deja fuera los porcentajes que no reparten nada.
- **Alternatives considered**: sumar todo porcentaje de la oración (falsas alarmas en intereses y moras).

## 6. Cuota de cada persona en la minuta

- **Decision**: en cada reparto, la cuota es de la persona nombrada en el tramo que la precede. En la minuta se arma el mismo mapa nombre → cuota. Se sugiere por persona solo si la minuta reparte entre las mismas personas y su reparto suma 100 %.
- **Rationale**: si las personas no coinciden, no hay una sugerencia segura (edge case de la spec).
- **Alternatives considered**: sugerir el faltante a la última persona (inventa).
