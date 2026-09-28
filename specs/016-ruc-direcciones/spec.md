# Feature Specification: F22 · RUC y direcciones

**Feature Branch**: `Angello5/RUC-y-direcciones-f22-ruc-direcciones`

**Created**: 2026-09-28

**Status**: Draft

**Input**: Contrato, Anexo A.3: el software verifica por código, contra los documentos fuente, «b. Número de Registro Único de Contribuyentes» y «f. Direcciones», «sobre cada aparición del dato en el borrador, y no sobre su mera existencia». Anexo B P-02: el 100 % de estos datos alterados en el borrador se detecta con su valor correcto construido desde la fuente; P-05: cero observaciones sobre datos correctos. Hoy el RUC no se verifica (solo descarta formularios SISGEN) y la dirección solo se comprueba para el domicilio RENIEC de personas con ficha (`DOMICILIO_NO_ENCONTRADO`, por presencia).

## Principio

**Cada aparición del dato en el borrador se compara con las fuentes.** Una copia correcta en otra cláusula no tapa una copia errónea. El reconocimiento sigue anclado a un rótulo, como el DNI de F19.

## Requirements *(mandatory)*

- **FR-001 (catálogo RUC)**: En las páginas fuente no descartadas (SISGEN y blancas no aportan), un número de 11 dígitos exactos precedido de un rótulo de RUC (`RUC`, `R.U.C.`, `REGISTRO UNICO DE CONTRIBUYENTE(S)`, con `N°`, `NUMERO` o `NRO` y `:` opcionales) cuyo prefijo sea `10`, `15`, `16`, `17` o `20` entra en la proyección `RUC` del catálogo. [NEEDS CLARIFICATION: prefijos válidos; por defecto 10/15/16/17/20.]
- **FR-002 (RUC en el borrador)**: En el borrador, un número de 9 a 13 dígitos tras un rótulo de RUC es una mención. Si es exactamente un RUC de las fuentes, no hay observación. Si no, observación `[RUC]` con hallado = el número y esperado = el RUC de las fuentes a menor distancia de Levenshtein si hay uno a ≤ 2 (empate: el menor), o «no coincide con ninguna fuente». Una observación por aparición.
- **FR-003 (RUC que falta)**: Un RUC de las fuentes que no aparece en el borrador da `[RUC] FALTA` solo si viene de la minuta (misma política que F16 para nombres: `nombres_exigibles()` incluye los RUC de los textos dados; sin `exigibles`, se exigen todos).
- **FR-004 (catálogo DIRECCION)**: En las páginas fuente no descartadas, el tramo tras un rótulo `DOMICILIO`, `DOMICILIO LEGAL`, `DOMICILIO FISCAL`, `DIRECCION`, `CON DOMICILIO EN` o `DOMICILIADO(A) EN` (no «… DE DOMICILIO», que rotula distrito, provincia o departamento) hasta el fin de cláusula es una dirección de la proyección `DIRECCION`, si tiene un dígito o una palabra de vía. También entran los domicilios RENIEC ya leídos de las personas.
- **FR-005 (DIRECCION en el borrador)**: En el borrador, el tramo tras `CON DOMICILIO EN`, `DOMICILIADO(A) EN` o `DOMICILIO LEGAL EN` hasta el fin de cláusula es una mención. Fin de cláusula: `, DISTRITO`, `, PROVINCIA`, `, DEPARTAMENTO`, `;`, fin de línea o un punto seguido de espacio que no cierra una abreviatura (palabra de hasta 4 letras, p. ej. `AV.`, `JR.`, `MZ.`). Ambos lados se reducen a las palabras de `_direccion_tokens` (abreviaturas equivalentes de F12; `#` = `INTERIOR`) sin `N°`/`NRO`/`NUMERO`.
- **FR-005a (ronda 2, el borrador puede agregar)**: Si todas las palabras de alguna dirección de las fuentes están en la mención, no hay observación: el borrador puede desarrollar abreviaturas y **agregar** interior, distrito o referencia.
- **FR-005b (solo sustituciones)**: Si no, se busca la dirección de las fuentes cuyas palabras que faltan tienen **todas** pareja en la mención: un número por otro número que la fuente no trae, o una palabra (≥ 4 letras) por otra a 1-2 letras de distancia; y con al menos tantas palabras comunes como faltantes. Una palabra que falta sin pareja significa que es otra dirección: nada. Con pareja, se observa `[DIRECCION]` (esperado = esa dirección) si hay un número sustituido o una palabra sustituida que **no** es ruido OCR de la fuente. Ruido OCR: la palabra del borrador aparece en el texto de las fuentes, o la de la fuente aparece menos de dos veces en él (una lectura única no confirmada). Si no se puede decidir, no se observa. [NEEDS CLARIFICATION: el núcleo no tiene diccionario de direcciones (hunspell se carga fuera del núcleo y hoy está apagado); por defecto, «palabra de diccionario» = palabra que aparece al menos dos veces en el texto de las fuentes no descartadas, o palabra de vía de F12.]
- **FR-006 (sin duplicar)**: `DOMICILIO_NO_ENCONTRADO` (F12) no se emite para una persona cuyo domicilio ya es el esperado de una observación `[DIRECCION]`.
- **FR-007**: Todo en `nucleo/verificar.py`; `services.py` no cambia (su adaptador ya interpreta «debe decir», «no coincide» y «FALTA»). El catálogo añade las claves `RUC` y `DIRECCION` al final; `revisar()` acepta el dict legado de cuatro claves. Sin dependencias ni migraciones.
- **FR-008**: Núcleo puro y determinista. Solo datos ficticios en tests (DNI `9000xxxx`, RUC `2000000000x`, direcciones inventadas).

## Success Criteria *(mandatory)*

- **SC-001**: RUC y direcciones alterados en el borrador se detectan uno a uno, con el valor de la fuente, aunque otra aparición sea correcta (P-02).
- **SC-002**: Ninguna observación sobre RUC o direcciones correctos (P-05).
- **SC-003**: Salida literal de `revisar()` idéntica en los fixtures de paridad sin RUC ni direcciones.

## Assumptions

- Ronda 2 (medición del revisor: 5 falsos positivos de 5 con la similitud `fuzz.ratio` de la ronda 1): la comparación pasa a inclusión de palabras más sustituciones explícitas. Un tramo del borrador que arrastra texto tras la dirección solo añade palabras y no observa.
- Una dirección alterada cuya fuente es una sola lectura (una palabra cambiada que aparece una única vez en las fuentes) no se observa: se prefiere perder la observación antes que dar un falso positivo (P-05). Los números sí se observan siempre.
- Las direcciones que faltan no se observan (FR-005 solo mira apariciones).
