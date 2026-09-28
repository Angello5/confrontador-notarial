# Tasks: F22 · RUC y direcciones

**Fuentes**: `spec.md`, `plan.md`. Solo datos ficticios (`9000xxxx`, `2000000000x`, direcciones inventadas).

## Phase 1 — pruebas rojas

- [ ] T001 Catálogo `RUC` desde rótulos, prefijo inválido y SISGEN fuera (FR-001, `tests/test_ruc_direcciones.py`).
- [ ] T002 RUC con un dígito cambiado, de 10 dígitos y ajeno → `[RUC]`; copia correcta y errónea a la vez → una observación; RUC correcto → nada (FR-002).
- [ ] T003 `[RUC] FALTA` solo para RUC de la minuta (FR-003).
- [ ] T004 Catálogo `DIRECCION` (prosa, ficha, RENIEC; «DISTRITO DE DOMICILIO» fuera) y `[DIRECCION]` por aparición; abreviatura equivalente, dirección sin parecida → nada (FR-004, FR-005).
- [ ] T005 Sin `DOMICILIO_NO_ENCONTRADO` duplicado (FR-006); paridad F13/F15 (pruebas existentes).

## Phase 2 — implementación y entrega

- [ ] T006 Implementación en `nucleo/verificar.py`; adaptador de `services.py` sin cambios (prueba de adaptación).
- [ ] T007 Fixtures, suite con cobertura, Ruff, `check`, `makemigrations --check`, `git diff --check`; commits locales sin push.
- [ ] T008 Medir SC-001, SC-002 (revisor, fuera del repositorio).
