# Feature Specification: F18 · Lectura de fichas RENIEC escaneadas

**Feature Branch**: `feature/f18-lectura-reniec`

**Created**: 2026-09-27

**Status**: Implementado e integrado (PR #48)

**Input**: Principio del propietario: la información de las personas sale de las fichas RENIEC y biométricas, y el sistema DEBE cubrir las fichas **escaneadas** (OCR), no solo las digitales. El revisor midió las 55 fichas reales: el OCR sí lee los valores, pero el lector no los asocia a su rótulo en cuatro casos: ruido dentro del año, valor en la línea siguiente, nombre desplazado por otra columna y ficha RENIEC sin nombre legible.

## Principio

**Un valor leído por el OCR bajo su rótulo pertenece a ese rótulo**, aunque el escaneo lo haya desplazado a la línea siguiente o le haya metido ruido entre dígitos. Nunca se toma un valor que sea otro rótulo.

## Requirements *(mandatory)*

- **FR-001 (fecha)**: Las fechas RENIEC (`FECHA DE NACIMIENTO`, `FECHA DE EMISION`) DEBEN tolerar puntos o espacios entre dígitos (`12/05/1.978`, `12/05/1 978`) antes de validarse. La validación de F12 no cambia: fecha inequívoca o nada.
- **FR-002 (línea siguiente)**: Si un rótulo RENIEC de F12 no trae valor en su celda ni en la celda siguiente, el valor DEBE ser la primera celda de la línea siguiente, salvo que esa línea sea otro rótulo (`Texto:` al inicio). Para `DIRECCION` el valor DEBE además tener un dígito o una abreviatura de vía de F12 (`AV`, `JR`, `CA`, `PSJ`, `MZ`, `LT`, …).
- **FR-003 (nombres)**: Si el valor de `NOMBRES`, `APELLIDO PATERNO` o `APELLIDO MATERNO` está vacío o no es alfabético (el OCR pegó una hora o un número de otra columna), DEBE tomarse la línea siguiente si es alfabética y no es rótulo. Tampoco DEBE tomarse si es un valor de `SEXO` o `ESTADO CIVIL` (`FEMENINO`, `MASCULINO`, `SOLTERO/A`, `CASADO/A`, `VIUDO/A`, `DIVORCIADO/A`): ocurre cuando una marca de agua tapó el nombre y el rótulo `Sexo:`, y la ficha queda sin nombre legible en vez de con un nombre falso.
- **FR-004 (RENIEC sin nombre)**: Una ficha RENIEC con documento legible y sin nombre legible, cuando existe un ancla con ese **documento exacto**, DEBE incorporar sus campos F12 (estado civil, fecha de nacimiento, domicilio, distrito) al ancla como una ficha RENIEC más: regla de emisión más reciente y revisión manual por conflicto de F12, procedencia de esa página. El nombre sigue siendo el del ancla. Sin ancla con ese documento, nada cambia.
- **FR-005**: Núcleo puro y determinista; solo cambia `nucleo/verificar.py`. Sin dependencias, migraciones ni cambios del sondeo JSON.
- **FR-006**: Solo datos ficticios en tests (DNI `9000xxxx`, nombres y direcciones inventadas).

## Success Criteria *(mandatory)*

Medidos por el revisor con el guion privado sobre las 55 fichas, solo recuentos:

- **SC-001**: Fichas con persona completa: **49 → 50**.
- **SC-002**: Fichas RENIEC con fecha de nacimiento **21 → 24**; con domicilio **18 → 22**; con estado civil **23 → 24**.
- **SC-003**: FR-004 aporta hasta **7 campos** de **3 fichas** sin nombre legible.
- **SC-004**: La salida literal de `revisar()`, `correspondencia()`, `diagnostico()` y `revisar_parrafos()` sobre los fixtures ficticios es idéntica antes y después.

## Assumptions

- "Rótulo" es el patrón `Texto:` al inicio de la línea (3 a 40 letras, espacios o puntos y dos puntos), como en el formato de `docs/catalogo-fuentes.md`. Un rótulo sin dos puntos no se reconoce como rótulo en la línea siguiente.
- FR-004: la ficha sin nombre se une al ancla como una ficha más: su página entra en las procedencias del ancla y deja de listarse como adjunto solo-documento.
- Deuda: corregir el OCR en origen; FR-002 y FR-003 solo miran una línea hacia abajo.
