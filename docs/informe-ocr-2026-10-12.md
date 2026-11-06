# Informe de lectura OCR y capa lingüística · 11 kardex

**Fecha**: 2026-10-12  
**Alcance**: los 11 kardex notariales de prueba, con un borrador real por kardex. Se procesaron en local. Este documento solo trae cifras agregadas, sin datos personales.  
**Complementa**: el informe «Confianza OCR por kardex» (confianza por página y tiempos), que ya se entregó.

## 1. Las 189 páginas con aviso de lectura dudosa

De las 402 páginas leídas por OCR, 189 llevan el aviso «lectura dudosa». En 185 de ellas la página está bien leída en conjunto: el aviso lo provoca una sola línea con confianza menor a 0,65. Las otras 4 quedan por debajo de 0,85 en conjunto.

**Respuesta a la consulta.** Los seis datos que el sistema valida son nombre, DNI, estado civil, domicilio, partida y monto. De esas 189 páginas:

| | Páginas | % |
|---|---:|---:|
| **Tienen comprometido alguno de los seis datos** | **20** | 11 % |
| **Solo tienen un sello, una firma u otra marca sin dato relevante** | **169** | 89 % |
| Total | 189 | 100 % |

### Las 20 páginas con un dato comprometido

| Origen | Páginas | Qué dato |
|---|---:|---|
| Datos escritos a mano en formularios y actas: declaraciones juradas y un acta de matrimonio antigua | 13 | nombres y apellidos, domicilio y estado civil (una casilla marcada a mano) |
| Fotos de DNI | 6 | apellidos, número de DNI de 8 cifras y el nombre en la franja de lectura mecánica |
| Ficha impresa | 1 | un número de 8 cifras que puede ser un DNI |

Una página puede comprometer más de un dato. Por dato: nombre en 13 páginas, domicilio en 4, DNI en 4 y estado civil en 2. Ninguna compromete una partida ni un monto.

Por kardex:

| Kardex | Con dato comprometido | Con aviso |
|---|---:|---:|
| 71291 | 3 | 15 |
| 71691 | 0 | 6 |
| 71823 | 2 | 7 |
| 71856 | 3 | 13 |
| 71950 | 3 | 8 |
| 71998 | 1 | 44 |
| 72136 | 3 | 33 |
| 72145 | 2 | 22 |
| 72156 | 0 | 3 |
| 72193 | 0 | 9 |
| 72198 | 3 | 29 |
| **Total** | **20** | **189** |

### Las 169 páginas sin dato relevante

- **19:** solo marcas sin letras ni números, como casillas, asteriscos y líneas de puntos.
- **150:** texto suelto de sellos, firmas y rúbricas, encabezados y rótulos impresos del formulario, códigos de verificación o fechas.

### Cómo se clasificó

1. **Líneas mal leídas.** Son las de confianza menor a 0,65. En las 4 páginas que quedan por debajo de 0,85 en conjunto, también cuentan las de confianza menor a 0,85.
2. **Candidatas.** Una línea mal leída es candidata a dato comprometido si cumple al menos una condición:
   - coincide con un nombre, DNI, partida, monto o domicilio leídos de los documentos del kardex;
   - tiene la forma de uno de esos datos, por ejemplo 8 cifras;
   - es el valor que sigue a un rótulo de dato, como «Apellidos:», «Domicilio en», «DNI N°» o «Estado civil».
3. **Revisión.** Las candidatas se revisaron una por una con su contexto. También se revisaron todas las líneas mal leídas de las páginas de identidad (DNI y fichas RENIEC) y de las 4 páginas de menor confianza.
4. **El resto.** Las páginas que no tienen ninguna candidata, o cuyas candidatas resultaron ser sellos, firmas, rótulos o fechas, cuentan como «sin dato relevante».

**Lectura:** el aviso de lectura dudosa es muy sensible, porque una sola marca basta para encenderlo. Los datos realmente comprometidos se concentran en lo escrito a mano y en fotos de DNI. Esos documentos conviene pedirlos en copia impresa o en consulta RENIEC en línea.

## 2. Errores lingüísticos que detecta el sistema

La capa lingüística marca errores de escritura del borrador. **No están verificados al 100 %**. Las sugerencias salen de un diccionario, de la cercanía entre palabras y de reglas fijas. El sistema no tiene lógica semántica: no entiende el sentido de la frase. Por eso no puede confirmar si una palabra desconocida es un error, un nombre propio o un término técnico, ni proponer siempre la corrección correcta. Tampoco puede detectar errores que dependen del sentido, como los tiempos verbales.

Para este informe, cada detección de los 11 borradores se revisó a mano.

| Tipo | Detectados | Errores reales | Con la sugerencia correcta |
|---|---:|---:|---:|
| **Tildes**: acento grave en lugar de agudo («CLÀUSULA») | 4 | 4 | 4 |
| **Errores gramaticales** | 12 | 11 | 11 |
| · concordancia de género con RENIEC («LA OTORGANTE» para un varón) | 5 | 5 | 5 |
| · palabra repetida («DE EL EL/LOS») | 5 | 5 | 5 |
| · espacio antes de un signo | 1 | 1 | 1 |
| · comillas sin cerrar (sin sugerencia; no se pudo confirmar) | 1 | — | — |
| **Tiempos verbales** | 0 | — | — |
| **Palabras que no existen** (tipeo) | 8 | 7 | 1 |
| **Total** | **24** | **22** | **16** |

- **Tildes y gramática:** son reglas exactas y su sugerencia acierta siempre (15 de 15).
- **Palabras que no existen:** el sistema detecta bien el error (7 de 8; el falso es un anglicismo válido en su contexto). Pero acierta la corrección solo en 1 de 7. Casi todas son nombres de empresa o de calle mal escritos, y el diccionario no sabe cuál es el correcto. Para esos datos la referencia correcta es la ficha RUC o RENIEC, no el diccionario.
- **Tiempos verbales:** no hay regla. Detectarlos requiere entender la frase, por ejemplo «TIENEN» frente a «TIENE» según el sujeto. Queda fuera del alcance actual.
