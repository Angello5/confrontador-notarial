# Tasks: F64 · Sugerencias en cifras y cuotas

**Input**: `specs/047-sugerencias-cifras/` (spec, plan, research, contrato, quickstart)

**Tests**: primero (principio III). Cada prueba se escribe y se ve fallar antes del código.

## Fase 1 · Base

- [X] T001 Agregar en `docs/roadmap.md` la «Continuación autorizada · 2026-10-30» con F64 y su alcance en `specs/047-sugerencias-cifras/`.

## Fase 2 · Fundamentos (bloquean las historias)

- [X] T002 Pruebas de `letras_de` en `tests/test_sugerencias_cifras.py`: casos fijos («TREINTA Y SEIS», «VEINTIUNO», «CIENTO UNO», «MIL», «UN MILLON», «DOS MILLONES») e ida y vuelta `numero_en_letras(letras_de(n).split()) == n` en una muestra del rango 0 a 999 999 999 999.
- [X] T003 Implementar `letras_de(n)` en `nucleo/verificar.py`, junto a `numero_en_letras` (research §3).
- [X] T004 Pruebas del formato de la cola en `tests/test_sugerencias_cifras.py`: `parsear_observacion_regla` separa `minuta`, `sugerencia` y `detalle` de «   (…)»; una observación sin cola da la misma fila que hoy (contrato, FR-009).
- [X] T005 Implementar el parseo de la cola en `expedientes/services.py` (`parsear_observacion_regla` / `_observacion_regla`) sin cambiar `hallado` ni `esperado`.

## Fase 3 · Historia 1 · Letras mal escritas (P1) 🎯 MVP

**Independent test**: «TREINTA Y SEI POR CIENTO (36%)» y «TREINTAY SEIS (36) MESES» sugieren el texto correcto; «TREINTA Y SEI (37)» no es errata.

- [X] T010 [US1] Pruebas del núcleo en `tests/test_sugerencias_cifras.py`: historia 1, escenarios 1 a 3, en porcentaje, monto con «Y 00/100 SOLES» y área.
- [X] T011 [US1] Pruebas de `aviso_de` en `tests/test_sugerencias_cifras.py`: «Las letras están mal escritas. Se sugiere: …» y la línea «Letras mal escritas: … → …».
- [X] T012 [US1] Implementar en `nucleo/verificar.py` la reparación de erratas (research §2) y la cola `(letras mal escritas; se sugiere «…»)` en `_numeros_en_letras` y `_areas_en_letras`.
- [X] T013 [US1] Implementar el caso errata en `aviso_de` de `expedientes/services.py`.
- [X] T014 [US1] Ajustar las expectativas de `tests/test_errores_borrador.py` (SEIZ, SES) y `tests/test_reglas_f30.py` al texto con cola.

## Fase 4 · Historia 2 · Desempata la minuta (P1)

**Independent test**: el mismo proyecto con tres minutas (36 %, 35 %, sin dato) da los tres avisos de la spec; igual para un área y un monto.

- [X] T020 [US2] Pruebas del núcleo en `tests/test_sugerencias_cifras.py`: historia 2, escenarios 1 a 4; un número suelto en la minuta (fecha, DNI) no desempata; la minuta con los dos valores no desempata.
- [X] T021 [US2] Pruebas de `aviso_de`: «La minuta dice … Se sugiere corregir las letras / la cifra: …» y «La cifra dice … y las letras dicen … La minuta no trae este dato: revise cuál corresponde.»
- [X] T022 [US2] Implementar en `nucleo/verificar.py` los valores de la minuta por unidad (research §4) y pasar `minutas` de `revisar` a `_numeros_en_letras` y `_areas_en_letras`; cola con `las letras dicen`, `la minuta dice`/`la minuta no trae el dato` y `se sugiere`.
- [X] T023 [US2] Implementar los dos casos en `aviso_de` de `expedientes/services.py`.

## Fase 5 · Historia 3 · Cuotas en todos los actos (P1)

**Independent test**: copropiedad, aporte a sociedad y sucesión con una cuota cambiada, con y sin reparto en la minuta; intereses y moras no avisan.

- [X] T030 [US3] Pruebas del núcleo en `tests/test_sugerencias_cifras.py`: historia 3, escenarios 1 a 5, más «CADA UNO», 200 % y personas distintas entre minuta y proyecto.
- [X] T031 [US3] Pruebas de `aviso_de`: con sugerencia por persona y «La minuta no trae el reparto»; el texto fijo deja de decir «de copropiedad».
- [X] T032 [US3] Implementar en `nucleo/verificar.py` el criterio de reparto (research §5), el mapa nombre → cuota en proyecto y minuta (research §6) y la cola; `revisar` pasa los nombres del catálogo y `minutas` a `_copropiedad`.
- [X] T033 [US3] Implementar los dos casos de cuotas en `aviso_de` y actualizar el texto fijo de `COPROPIEDAD` en `_AVISOS` de `expedientes/services.py`.

## Fase 6 · Cierre

- [X] T040 Medición privada en los kardex locales (plan, sección Medición): conteos antes y después, revisión a mano de cada aviso nuevo de cuotas, ajuste del criterio si hay falsas alarmas. Anotar solo los conteos en `spec.md`.
- [X] T041 Actualizar `specs/040-resumen-errores/spec.md` (tabla de avisos de F60) para remitir a F64 cuando hay sugerencia.
- [X] T042 Suite completa, Ruff (check y format) y cobertura de `nucleo/verificar.py` y `expedientes/services.py` sin bajar.
- [X] T043 Revisar el diff: sin datos reales ni secretos.

## Dependencias

- Fase 2 antes de las historias: T003 (`letras_de`) lo usan las historias 1 y 2; T005 (cola) lo usan las tres.
- Historias 1 → 2: comparten `_numeros_en_letras`; se hacen en orden. La historia 3 es independiente de las otras dos (otra función) y puede ir en paralelo.
- T040 después de las tres historias.

## Paralelo

- T002 y T004 (pruebas de distinta capa).
- Historia 3 (T030–T033) en paralelo con las historias 1 y 2.

## Estrategia

MVP: fases 2 y 3 (errata), la sugerencia sin duda posible. Luego la historia 2, la 3 y la medición.
