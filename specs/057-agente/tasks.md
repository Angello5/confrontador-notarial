# Tasks: F75 · Agente de estudio de título

**Tests**: primero (principio III).

## Fase 1 · Base

- [X] T001 Roadmap: F75 en la «Continuación autorizada · 2026-11-04» de `docs/roadmap.md`.
- [X] T002 App `agente`, ajustes `AGENTE_*` e interruptor en `config/settings.py`.

## Fase 2 · Historia 1 y 2 · Consulta (P1) 🎯 MVP

- [X] T010 [US1] `tests/test_agente.py`: interruptor, login/rol, adjuntos (tamaño, formato, firma), auditoría sin contenido, argv y entorno, errores.
- [X] T011 [US1] `agente/services.py`: lectura de adjuntos, contexto de documentos, proveedores `claude` y `codex`, cupo, timeout.
- [X] T012 [US1] `agente/views.py`, `urls.py`, `templates/agente/consulta.html` y entrada «Agente» en el menú.
- [X] T013 [US2] `agente/prompt/`: system prompt breve y fuentes del Perú.
- [X] T014 Medición real con `claude -p` y una pregunta sin datos personales (~20 s, 2 fuentes).

## Fase 3 · Pendiente

- [X] T015 Rediseño a estudio de título (2026-11-10): sin selector de kardex; adjuntos ≤ 10 MB (PDF, Word, imágenes) y texto pegado; el agente deduce qué falta; migración `0002` (quita `expediente`, añade `adjuntos`).
- [X] T016 Recorte no silencioso (2026-11-11): `AGENTE_MAX_CONTEXTO`, aviso al adjuntar y en la respuesta, «AVISO DEL SISTEMA» al modelo, regla 5 del prompt; probado con límite de 300 caracteres.
- [ ] T020 Decidir la enmienda 3.0.0 y la aceptación de la notaría (spec, «NEEDS CLARIFICATION»).
- [X] T021 `codex` probado con la sesión ChatGPT (CLI 0.167.1, `--ignore-user-config`, esfuerzo bajo, ~25 s). Sigue pendiente correrlo en un usuario del sistema aislado antes de cualquier uso fuera de desarrollo.
- [ ] T022 Medir calidad con 10 estudios de título sobre documentos ficticios; ajustar `prompt/`.
- [ ] T023 Decidir cuentas de empresa o API para producción; despliegue en el servidor (F8).
