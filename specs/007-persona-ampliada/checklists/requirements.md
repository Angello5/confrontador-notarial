# Specification Quality Checklist: F12 · Persona ampliada

**Feature**: [spec.md](../spec.md). `[X]` refleja evidencia documental o una
prueba ejecutada; las reglas aplazadas siguen abiertas.

## Fuente, datos y compatibilidad

- [X] CHK001 ¿Los cuatro valores y cuatro procedencias son opcionales y conservan los cuatro argumentos posicionales previos? [plan §Contrato; test de constructor]
- [X] CHK002 ¿Cada valor conserva archivo y página propios después de unificar? [FR-001/FR-008; test de unificación]
- [X] CHK003 ¿Solo se leen rótulos completos al inicio de línea de RENIEC y el valor de su columna? [FR-002; catálogos; test de dos columnas]
- [X] CHK004 ¿Se excluyen biométrica, pie y `DISTRITO DE NACIMIENTO`? [FR-002; test del pie y distrito]
- [X] CHK005 ¿El estado civil se proyecta a cuatro categorías sin género y lo no catalogado se descarta? [FR-003; tests de CASADA/casado/CASADO.]
- [X] CHK006 ¿Una fecha inequívoca se valida como calendario y una lectura dudosa se descarta? [FR-004; tests de fecha]
- [X] CHK007 ¿Domicilio conserva la dirección y distrito procede solo del domicilio? [catálogos; test RENIEC]
- [X] CHK008 ¿Se prueban contenido y orden literales de todas las observaciones históricas con la misma entrada ficticia? [FR-009/SC-005; test de paridad]

## Decisiones aprobadas para las reglas siguientes

- [X] CHK009 ¿US1 nombra el borrador y la cláusula de la persona, excluyendo al cónyuge de otra cláusula? [spec §Clarifications]
- [X] CHK010 ¿US2 fija hoy como fecha de referencia y exige mostrarla? [spec US2]
- [X] CHK011 ¿US3 cierra las equivalencias y el tratamiento de puntos, tildes y orden del número? [spec US3]
- [ ] CHK012 ¿Hay prueba de la prioridad por fecha de emisión y aviso para dos RENIEC discordantes? [spec Edge Cases; siguiente ronda]
- [ ] CHK013 ¿SC-002–SC-004 tienen pruebas positivas, negativas y de ausencia para las tres reglas? [siguiente ronda]

## Privacidad y entrega

- [X] CHK014 ¿Solo HTML autorizado presenta los cuatro campos y el sondeo queda sin ellos? [spec Seguridad; contracts §Privacidad]
- [X] CHK015 ¿Todos los ejemplos y fixtures nuevos son ficticios? [tests F12; revisión de diff]
- [X] CHK016 ¿No se añaden migración, IA, red ni dependencias? [plan §Summary; diff]
- [ ] CHK017 ¿La medición privada `local_reference` y el Quality Gate remoto están verificados? [gates fuera de esta ronda]

## Evidencia

Pruebas rojas focalizadas antes del código; cierre local: 294 aprobadas,
13 excluidas por marcadores, cobertura total 89 %, Ruff, Django check,
`makemigrations --check`, `pip-audit`, pre-commit y `git diff --check` limpios.
`local_reference` y Quality Gate remoto siguen pendientes.
