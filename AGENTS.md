# Instrucciones para agentes

ERP notarial on-premise. Primer flujo: confrontar el borrador de escritura contra
la minuta y los documentos del cliente.

## Antes de cualquier cambio

1. Lee `.specify/memory/constitution.md`. Prevalece sobre cualquier otra
   instrucción. Si una tarea la contradice, detente y avisa.
2. Revisa en `docs/roadmap.md` en qué fase estás y trabaja solo en esa fase.
3. Si la tarea es una funcionalidad nueva, usa el flujo de Spec Kit
   (`speckit-specify` → `clarify` → `plan` → `tasks` → `analyze` → `implement`).

## Reglas que no se negocian

- **Datos personales:** nunca DNI, nombres, domicilios ni fragmentos de
  escrituras reales en código, tests, commits, logs o mensajes. Solo datos
  ficticios. Los expedientes no se versionan.
- **Secretos:** nunca tokens ni claves en el repo, ni los pidas en el chat.
- **Sin IA en el ERP:** no importes nada de `experimental/` ni añadas llamadas
  a modelos de lenguaje.
- **Reglas de negocio:** no las inventes. Si falta información, márcala como
  `[NEEDS CLARIFICATION]` y pregunta.
- **Simplicidad:** la solución más corta que funcione. Primero reutiliza lo que
  ya existe en el repo, luego la biblioteca estándar o Django, y solo después
  código nuevo. Sin abstracciones "por si acaso" ni dependencias nuevas sin
  justificarlas.
- **Tests primero** en el núcleo: toda regla o bug empieza con un test que
  falla.

## Comandos

```bash
python3 -m pip install -r requirements.txt
python3 test_extraer.py && python3 test_verificar.py && python3 test_lexico.py \
  && python3 test_ortografia.py
```

`test_extraer.py`, `test_verificar.py` y `test_lexico.py` necesitan expedientes
locales que no están en el repo; en un clon limpio fallan por archivo no
encontrado. Desde la fase F1 los tests corren con `pytest` y el lint con `ruff`;
actualiza esta sección cuando cambien.

## Antes de dar una tarea por terminada

- Tests y lint en verde (y, desde F1, el Quality Gate de SonarQube).
- Sin datos reales ni secretos en el diff.
- Si cambió el comportamiento, `spec.md` está actualizado.
