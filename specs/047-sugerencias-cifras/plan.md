# Implementation Plan: F64 · Sugerencias en cifras y cuotas

**Branch**: `feat/f64-sugerencias-cifras` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Tres reglas del núcleo ya detectan el problema: `_numeros_en_letras` (F19), `_areas_en_letras` (F30) y `_copropiedad` (F30). F64 no agrega reglas de detección nuevas salvo ampliar la de cuotas a todos los actos. Lo que cambia es que cada observación lleva, al final, lo que dice la minuta y la sugerencia, y que la pantalla los muestra en el aviso de F60.

- **Letras mal escritas:** `_cola_en_letras` ya reconoce la palabra por similitud, pero `numero_en_letras` devuelve `None`. Se cambia cada palabra no numérica por la más parecida del vocabulario; si así valen la cifra, esa es la sugerencia.
- **Letras distintas:** se buscan en la minuta los valores con la misma unidad. Si trae uno solo de los dos, desempata; la sugerencia se escribe con un generador de números en letras nuevo (`letras_de`).
- **Cuotas:** la regla deja de exigir palabras de copropiedad. Reconoce el reparto por los nombres de las partes o por términos de reparto, y descarta intereses, moras y tasas. Compara la cuota de cada persona con el reparto de la minuta.

Decisiones y alternativas en [research.md](research.md); formato de la observación en [contracts/observaciones.md](contracts/observaciones.md).

## Technical Context

- **Language/Version**: Python 3.13.
- **Primary Dependencies**: las existentes (rapidfuzz para la palabra más parecida). Ninguna nueva.
- **Storage**: sin cambios de modelo ni migraciones. La observación sigue siendo texto en `Corrida.hallazgos`.
- **Testing**: pytest con frases ficticias (núcleo y pantalla). Medición privada en los kardex locales (`confrontador_audit`), fuera del CI y del repositorio.
- **Target Platform**: la misma del ERP.
- **Performance Goals**: sin efecto apreciable; son búsquedas de texto por observación.
- **Constraints**: determinista; compatible con las observaciones ya guardadas y con `nucleo/correccion.py`.

## Constitution Check

| Principio | Cómo se cumple |
|---|---|
| I. Determinismo | Todo por código, sin modelos. La misma entrada da la misma observación. Cuando no hay con qué desempatar, no se sugiere un valor. |
| II. Núcleo puro | La lógica va en `nucleo/verificar.py`; recibe los textos de la minuta que `revisar` ya recibe. `expedientes/services.py` solo presenta. |
| III. Pruebas primero | Cada caso de las historias empieza con una prueba que falla (núcleo y `aviso_de`). |
| IV. Privacidad | Pruebas con datos ficticios. La medición local solo informa conteos; no guarda ni versiona textos de los kardex. |
| V. Simplicidad | Se amplían tres funciones y `aviso_de`; un generador de letras de unas 25 líneas. Sin tablas, sin dependencias, sin campos nuevos en la base. |
| VI. Seguridad | Sin entradas nuevas ni endpoints. |
| VII. DevSecOps | Ruff, cobertura y Quality Gate como siempre. |
| VIII. Usabilidad | Ver la sección UX de la spec. |

Sin violaciones: no hay tabla de complejidad.

## Estructura

```text
nucleo/verificar.py          # letras_de, reparación de erratas, valores de la minuta, reparto de cuotas
expedientes/services.py      # parsear la cola «(…)» de la observación; aviso_de con minuta y sugerencia
tests/test_sugerencias_cifras.py   # nuevo: historias 1 a 3 con datos ficticios
tests/test_errores_borrador.py     # se ajustan las expectativas de NUMERO_EN_LETRAS
tests/test_reglas_f30.py           # se ajustan las de AREA y COPROPIEDAD
docs/roadmap.md              # continuación autorizada 2026-10-30
specs/040-resumen-errores/spec.md  # el aviso de F60 remite a F64 cuando hay sugerencia
```

## Medición en los kardex locales (autorizada por el usuario el 2026-10-30)

Un script privado, fuera del repositorio, recalcula con el núcleo anterior y con el nuevo las reglas de la última corrida de cada borrador de `confrontador_audit` (PostgreSQL local, puerto 55432). Solo imprime conteos:

- avisos por tipo antes y después (ninguno debe desaparecer: SC-004);
- avisos con sugerencia, con «la minuta no trae el dato» y de cuotas fuera de copropiedad;
- oraciones con porcentajes descartadas por intereses, moras o tasas.

Los avisos nuevos de cuotas se revisan a mano uno por uno; si alguno es una falsa alarma, se ajusta el criterio de reparto y se repite. Los conteos van a la spec; ningún texto de los kardex sale de la máquina ni entra al repositorio.
