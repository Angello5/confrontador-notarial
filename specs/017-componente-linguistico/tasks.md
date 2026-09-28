# Tasks: F23 · Componente lingüístico

**Fuentes**: `spec.md`, `plan.md`. Solo datos ficticios (`9000xxxx`, nombres inventados).

## Phase 1 — pruebas rojas

- [X] T001 `redaccion()`: cada regla de FR-004 con caso positivo y negativo; hallazgo solapado con un valor protegido → nada (`tests/test_linguistico.py`).
- [X] T002 `confrontar_borrador`: ortografía reactivada sin reportar nombres, domicilios ni hallados de regla; filas de redacción en `ortografia`, nunca en `regla` (FR-001, FR-002, FR-005).
- [X] T003 Diccionario no aprovisionado → `RESULTADO` con `linguistico_aviso` y filas de redacción (FR-003).
- [X] T004 Pantalla: tarjeta y sección «Lingüístico», aviso visible (FR-006).

## Phase 2 — implementación y entrega

- [X] T005 `redaccion()` en `nucleo/ortografia.py`; orquestación en `services.py`; plantilla.
- [X] T006 Fixtures, suite con cobertura, Ruff, `check`, `makemigrations --check`, `git diff --check`; commits locales sin push.

## Ronda 2 — medición del revisor (2026-09-28)

- [ ] T007 Pruebas rojas: palabra rara en una fuente → sin aviso; ausente de las fuentes → aviso; doble espacio → sin aviso (SC-004).
- [ ] T008 `_capa_linguistica` pasa las palabras de las fuentes a `ortografia.revisar`; se retira la regla «doble espacio».
- [ ] T009 Verificaciones de T006; commit local sin push.
