# Contrato · Observaciones con sugerencia (F64)

El núcleo devuelve texto; el adaptador (`parsear_observacion_regla`) lo convierte en una fila y `aviso_de` en el aviso de pantalla. F64 agrega una cola entre paréntesis. Sin cola, todo funciona como antes.

## Núcleo → adaptador

```text
[CAMPO] «hallado» debe decir «esperado»   (detalle)
```

`detalle` son partes separadas por «; », en este orden y todas opcionales:

| Parte | Cuándo |
|---|---|
| `letras mal escritas` | historia 1 |
| `las letras dicen «35%»` | historia 2: valor de las letras, con su unidad |
| `las cuotas suman 90 %` | historia 3 (ya existía) |
| `la minuta dice «36 %»` | la minuta desempata |
| `la minuta no trae el dato` | historia 2.3 y 3.3 |
| `se sugiere «…»` | errata (historia 1) y cuotas (historia 3) |
| `se sugiere corregir las letras «…»` / `se sugiere corregir la cifra «…»` | historia 2, la minuta desempata |

Ejemplos (datos ficticios):

```text
[NUMERO_EN_LETRAS] «TREINTA Y SEI POR CIENTO (36%)» debe decir «36%»   (letras mal escritas; se sugiere «TREINTA Y SEIS POR CIENTO (36%)»)
[NUMERO_EN_LETRAS] «TREINTA Y CINCO POR CIENTO (36%)» debe decir «36%»   (las letras dicen «35%»; la minuta dice «36%»; se sugiere corregir las letras «TREINTA Y SEIS POR CIENTO (36%)»)
[NUMERO_EN_LETRAS] «TREINTA Y CINCO POR CIENTO (36%)» debe decir «36%»   (las letras dicen «35%»; la minuta no trae el dato)
[COPROPIEDAD] «20%, ANA RUIZ EL 20% Y LUIS SOTO EL 50%» debe decir «100 %»   (las cuotas suman 90 %; la minuta dice «LUIS SOTO 60 %»; se sugiere «LUIS SOTO 60 % (dice 50 %)»)
```

`«esperado»` no cambia: sigue siendo la cifra (o «100 %»), para que `nucleo/correccion.py`, las corridas guardadas y las estadísticas lo lean igual. Los tres campos siguen en `_SIN_TEXTO_CORRECTO`.

## Adaptador → pantalla

La fila gana una clave opcional, `detalle`, con el texto entre paréntesis. `aviso_de` lo lee y arma:

| Caso | «Qué verificar» | Línea de la lista |
|---|---|---|
| Errata | «Las letras están mal escritas. Se sugiere: …» | «Letras mal escritas: hallado → sugerencia» |
| Desempata la minuta | «La minuta dice 36 %. Se sugiere corregir las letras (o la cifra): …» | «Cifra y letras no coinciden: hallado → sugerencia» |
| Sin dato | «La cifra dice 36 % y las letras dicen 35 %. La minuta no trae este dato: revise cuál corresponde.» | «Cifra y letras no coinciden: hallado» |
| Cuotas con sugerencia | «Las cuotas suman 90 %. La minuta dice LUIS SOTO 60 %. Se sugiere: LUIS SOTO 60 % (dice 50 %).» | «Las cuotas no suman 100 %: hallado → sugerencia» |
| Cuotas sin dato | «Las cuotas suman 90 %. La minuta no trae el reparto: revise cuál corresponde.» | «Las cuotas no suman 100 %: hallado» |
| Fila sin claves nuevas | el texto de F60, como hoy | como hoy |
