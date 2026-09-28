# Feature Specification: F19 · Errores del borrador fuera de la comparecencia

**Feature Branch**: `feature/f19-errores-borrador`

**Created**: 2026-09-27

**Status**: Draft

**Input**: El revisor comparó el expediente de referencia con errores intencionados (lista oficial de 8) con la confrontación actual: se detectan 3 (nombres alterados junto a «DE NACIONALIDAD»). Faltan 5 por tres huecos: (A) DNI con un dígito de menos en el borrador, que `RE_DNI_DOC` no reconoce porque exige 8 dígitos; (B) nombre mal escrito fuera de «DE NACIONALIDAD» (p. ej. «EN REPRESENTACION DE …»); (C) número en letras distinto de su cifra entre paréntesis.

## Principio

**Lo que el borrador dice de un dato de las fuentes se compara con la fuente, esté donde esté.** El reconocimiento sigue anclado: a un rótulo de DNI, a un nombre de las fuentes o a una cifra entre paréntesis.

## Requirements *(mandatory)*

- **FR-001 (DNI)**: En el borrador, un número de 6 a 10 dígitos precedido de un rótulo de DNI (`DNI`, `D.N.I.`, `DOCUMENTO NACIONAL DE IDENTIDAD`, con `N°`, `NUMERO` o `NRO` opcionales) es una mención de DNI. Si tiene 8 dígitos se verifica como hasta ahora. Si no, observación `[DNI]` con hallado = el número y esperado = el DNI de las fuentes a menor distancia de Levenshtein si hay uno a ≤ 2 (empate: el menor), o «no coincide con ninguna fuente».
- **FR-002 (DNI)**: Un número sin rótulo de DNI no se toca. En las fuentes se sigue exigiendo el DNI de 8 dígitos exactos.
- **FR-003 (NOMBRE)**: Para cada nombre conocido (proyección `NOMBRE`: anclas, adjuntos, menciones, cónyuges), se busca en el borrador la ventana del mismo número de palabras más parecida (`fuzz.ratio`), excluyendo las ventanas que se solapan con una aparición exacta de cualquier nombre conocido. Si su similitud es ≥ 85, observación `[NOMBRE]` con hallado = la ventana y esperado = el nombre de la fuente.
- **FR-004 (NOMBRE)**: No se repite una ventana ya observada o reconocida por las reglas de F5 (junto a «NACIONALIDAD», tras «CASADO CON» o en la carátula).
- **FR-005 (NUMERO_EN_LETRAS)**: En el borrador, un número en letras en español (0 a 999 999, con `Y dd/100` opcional) seguido de una cifra entre paréntesis (con `S/` opcional) debe valer lo mismo, céntimos incluidos (ausentes = `00`). Si no, o si alguna palabra del número no se reconoce (mal escrita, similitud ≥ 75 con una palabra numérica), observación `[NUMERO_EN_LETRAS]` con hallado = el texto y esperado = la cifra.
- **FR-006 (NUMERO_EN_LETRAS)**: Sin al menos una palabra numérica exacta delante del paréntesis no hay observación (p. ej. «CLAUSULA PRIMERA (1)»).
- **FR-007**: Los tres detectores viven en `nucleo/verificar.py` dentro de `revisar()` y usan el formato de salida existente; `services.py` no cambia (su adaptador ya interpreta «debe decir» y «no coincide»). Sin dependencias, migraciones ni cambios de plantilla (la columna Campo muestra el código tal cual).
- **FR-008**: Núcleo puro y determinista. Solo datos ficticios en tests (DNI `9000xxxx`, nombres inventados).

## Success Criteria *(mandatory)*

- **SC-001**: En el expediente de referencia, 8 de 8 errores intencionados detectados (hoy 3).
- **SC-002**: Sin falsos positivos nuevos en los demás expedientes medidos por el revisor.
- **SC-003**: Salida literal de `revisar()` idéntica sobre los fixtures ficticios de paridad (F13, F15), que no contienen estos casos.

## Assumptions

- El `FALTA` del valor esperado se sigue ocultando en `services.py` cuando hay una discrepancia con el mismo esperado (sin cambio).
- FR-003 da una observación por nombre conocido como máximo: la ventana más parecida.
- FR-005 suma los valores de las palabras (`MIL` multiplica lo acumulado); no valida el orden gramatical.
