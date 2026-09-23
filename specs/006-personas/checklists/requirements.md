# Specification Quality Checklist: F11 · Extracción por personas

**Propósito**: verificar trazabilidad de `spec.md`, decisiones del núcleo,
compatibilidad F5 y límites de privacidad. `[X]` requiere evidencia real de
implementación; las decisiones del propietario ya están resueltas.

**Feature**: [spec.md](../spec.md)

## Completitud y trazabilidad

- [ ] CHK001 FR-001 tiene un contrato explícito de `Persona` con nombre y documento asociados, incluidos estados sin uno de los dos. [Spec FR-001, research §1]
- [ ] CHK002 FR-002 limita la asociación a un bloque y no cruza páginas. [Spec FR-002, tasks T007]
- [ ] CHK003 FR-003 tiene `leer_paginas()` y conserva `leer()` como wrapper compatible. [Spec FR-003, tasks T010/T014]
- [ ] CHK004 FR-004 tiene clasificación determinista, precedencia fija y descarte conservador. [Spec FR-004, research §4]
- [ ] CHK005 FR-005 excluye metadatos de consulta sin eliminarlos del texto plano necesario para reglas no identitarias. [Spec FR-005, tasks T016]
- [ ] CHK006 FR-006 excluye bloques de coincidencias SISGEN sin aceptar sus entidades. [Spec FR-006, NC-001]
- [ ] CHK007 FR-007 tolera solo variantes cerradas de la etiqueta y la errata `D.N.1,`. [Spec FR-007, tasks T020/T021]
- [ ] CHK008 FR-008 produce observación de documento cruzado con hallado, esperado y procedencia. [Spec FR-008, contracts §Observaciones]
- [ ] CHK009 FR-009 produce observación de documento sin titular conocido. [Spec FR-009, tasks T009/T028]
- [ ] CHK010 FR-010 conserva archivo y página por cada procedencia. [Spec FR-010, contracts §Personas]
- [ ] CHK011 FR-011 unifica solo por documento exacto o nombre exacto seguro; similitud no unifica. [Spec FR-011, research §6]
- [ ] CHK012 FR-012 no modela personas jurídicas como parte del acto y conserva representante natural solo cuando el bloque lo liga de forma explícita. [Spec FR-012, research §4]
- [ ] CHK013 FR-013 tiene prueba de paridad para partidas, montos y párrafos, aislada del filtro identitario. [Spec FR-013, tasks T008/T018]

## Contrato y compatibilidad

- [ ] CHK014 `Catalogo` expone la relación persona-documento y una proyección de lectura `NOMBRE`, `DNI`, `PARTIDA`, `MONTO`. [plan §Contract]
- [ ] CHK015 `revisar()`, `correspondencia()` y `diagnostico()` aceptan la proyección nueva y entradas legado sin cambiar sus cadenas ni umbrales. [plan §Contract, tasks T006/T008]
- [ ] CHK016 La comparación ligada es una función estructurada separada de las cadenas históricas de `revisar()`. [research §1]
- [ ] CHK017 El texto F4 antiguo sin separador se procesa como un bloque sin inventar fronteras. [research §2, spec FR-015]
- [X] CHK018 El catálogo de la rama está disponible y la contradicción SISGEN está resuelta. [research §Resoluciones aplicadas, tasks T001/T002]

## Seguridad, privacidad y determinismo

- [ ] CHK019 El núcleo no importa Django, OCR, base de datos, sistema de archivos ni `experimental/`. [Constitución I/II]
- [ ] CHK020 No se introducen dependencias nuevas, modelos de lenguaje ni servicios externos. [Constitución I/V]
- [ ] CHK021 Los tests, fixtures, commits y documentos usan únicamente datos ficticios. [Constitución III/IV]
- [ ] CHK022 No se guardan textos descartados ni se escriben personas en logs o mensajes de error. [Constitución IV, contracts §Privacidad]
- [ ] CHK023 Un número aislado, de operador, RUC, partida, transacción, teléfono o correo no se captura como DNI. [research §5, tasks T021]
- [ ] CHK024 Fuzzy matching no aprueba ni unifica personas; los conflictos quedan en `revision_manual`. [research §6]
- [X] CHK025 No hay migración de páginas: la cadena plana usa `\f` y las filas antiguas sin separador se tratan como un bloque. [spec FR-015, tasks T003/T012]

## Decisiones aplicadas

- SISGEN se descarta entero, incluido el documento consultado.
- El cónyuge entra sin documento y solo se verifica su nombre.
- Los grupos manuscritos separados no se unen.
- La página no clasificada se cuenta y lista por archivo y página, sin texto.

## Evidencia

Pendiente de implementación. No se declara suite, lint, migración, cobertura,
Quality Gate remoto ni medición privada como evidencia en esta etapa.
