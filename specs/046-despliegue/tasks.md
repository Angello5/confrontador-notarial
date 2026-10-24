# Tasks: F8 · Despliegue en el servidor de la notaría

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/servidor.md](contracts/servidor.md), [quickstart.md](quickstart.md)

**Tests**: obligatorios por el principio III para la lógica Python nueva (avisos, latido, registros) y análisis sintáctico de los scripts. Los escenarios de extremo a extremo se validan en un servidor de prueba con la [guía](quickstart.md).

**Formato**: `[ID] [P?] [Story] Descripción`. `[P]` indica que la tarea va en otro archivo y no depende de una tarea pendiente.

## Phase 1: Setup

- [x] T001 Enmendar la constitución a 2.2.0: despliegue nativo en Windows, que resuelve `TODO(DESPLIEGUE)` (`.specify/memory/constitution.md`).
- [ ] T002 `waitress==3.0.2` en `requirements.in`; su bloque con hashes de PyPI en `requirements.txt`, sin regenerar el resto, con `colorama` y `tzdata` al final. `pip_audit --strict` limpio.
- [ ] T003 [P] Plantilla `scripts/windows/erp.env.ejemplo` con todas las variables de `specs/046-despliegue/contracts/servidor.md`, sin valores secretos.

## Phase 2: Foundational (bloquea todas las historias)

- [ ] T004 [P] Pruebas en `tests/test_despliegue.py`, con `config.settings` cargado en un subproceso como en `tests/test_foundation.py`:
  - con `ERP_REGISTROS_DIR`, `LOGGING` usa `RotatingFileHandler` de 5 MB × 10 en esa carpeta; sin ella, consola;
  - `STATIC_ROOT` toma `ERP_STATIC_ROOT` o `BASE_DIR / "staticfiles"`.

  Deben fallar antes de T005.
- [ ] T005 `config/settings.py`: `STATIC_ROOT`, `LOGGING` (R8) y `ERP_ESTADO_DIR`, que vale `None` si no está definido.
- [ ] T006 [P] Prueba en `tests/test_despliegue.py`: cada `scripts/windows/*.ps1` se analiza sin errores con el parser de PowerShell (`pwsh` o `powershell`); se salta si no hay PowerShell.
- [ ] T007 `scripts/windows/iniciar.ps1`:
  - `-Rol web`: lee `C:\ProgramData\ConfrontadorNotarial\erp.env` (líneas `NOMBRE=valor`, ignora `#`), define las variables en su proceso y ejecuta `waitress-serve --listen=127.0.0.1:$env:HTTP_PLATFORM_PORT --url-scheme=https --threads=8 config.wsgi:application`;
  - `-Rol worker`: `manage.py procesar_documentos --continuo`;
  - `-Rol tarea -Comando <cmd>`: `manage.py <cmd>`.

  Ninguna clave pasa por la línea de comandos.

**Checkpoint**: configuración de producción y lanzador listos.

## Phase 3: User Story 1 · Las usuarias entran desde sus PC (P1) 🎯 MVP

**Goal**: HTTPS con el nombre interno desde las PC de la LAN.

**Independent Test**: `quickstart.md` escenarios 1 y 2.

- [ ] T008 [P] [US1] `scripts/windows/web.config`:
  - `httpPlatform` → `powershell.exe -NoProfile -ExecutionPolicy Bypass -File iniciar.ps1 -Rol web`, con `processesPerApplication=1` y `stdoutLogEnabled=false`;
  - regla de URL Rewrite HTTP→HTTPS (301);
  - `/static/` servido desde `C:\ConfrontadorNotarial\staticfiles`, sin pasar por Python;
  - `httpErrors` para 502 y 503 con la página estática `scripts/windows/mantenimiento.html`: en español, con los estilos del ERP incrustados y sin términos técnicos. Dice «El sistema se está actualizando o no está disponible en este momento. Intente de nuevo en unos minutos.» (UX de la spec).
- [ ] T009 [US1] `scripts/windows/instalar.ps1 -Version <tag>`, como administrador:
  - crea las carpetas de `specs/046-despliegue/data-model.md` con sus ACL;
  - copia el logo de la notaría a `C:\ConfrontadorNotarial\staticfiles\marca\logo.png`, que se comparte entre versiones porque `collectstatic` se ejecuta sin `--clear` y no lo borra, y deja `ERP_LOGO=/static/marca/logo.png` en `erp.env` (FR-014);
  - registra el origen `ConfrontadorNotarial` en el Visor de eventos;
  - prepara `versiones\<tag>` (código, `.venv` con `--require-hashes`, `collectstatic`) y el enlace `actual`;
  - crea el grupo de aplicaciones con la cuenta de servicio y `loadUserProfile=true`, y el sitio de IIS (443 y 80) apuntando a `actual`;
  - crea la regla de firewall TCP 443/80 limitada a `LocalSubnet`.
- [ ] T010 [US1] En el servidor de prueba: escenarios 1 (2 PC, HTTPS sin avisos, confrontación ficticia) y 2 (fuera de la LAN no responde) de `specs/046-despliegue/quickstart.md`.

## Phase 4: User Story 2 · El ERP se mantiene en marcha solo (P1)

**Goal**: la web y el worker arrancan con el servidor y vuelven solos; los avisos de FR-017 alertan si algo se detiene.

**Independent Test**: escenarios 3, 4 y 10.

- [ ] T011 [P] [US2] Pruebas en `tests/test_despliegue.py`:
  - **latido**: con `ERP_ESTADO_DIR`, cada vuelta de `procesar_documentos` actualiza la fecha de `worker.latido`; sin ella, no crea nada;
  - **`avisos_sistema()`**:
    - latido de más de 10 minutos → aviso de procesamiento;
    - `respaldo.ok` ausente, ilegible o de más de 26 horas → aviso de respaldo;
    - `certificado.vence` a 30 días o menos → aviso con la fecha DD/MM/AAAA;
    - sin `ERP_ESTADO_DIR` → `[]`;
    - los textos no tienen rutas ni términos técnicos.

  Deben fallar antes de T012 y T013.
- [ ] T012 [US2] `expedientes/management/commands/procesar_documentos.py`: `procesar_vuelta` toca `worker.latido` en `settings.ERP_ESTADO_DIR` si está definido.
- [ ] T013 [US2] `expedientes/services.py::avisos_sistema()` con los umbrales y textos de `specs/046-despliegue/data-model.md`.
- [ ] T014 [US2] Mostrar los avisos de `avisos_sistema()` en el Inicio del rol Administrador, con el componente de aviso existente. Archivos: `core/views.py` y `templates/core/home.html`. El Inicio de las usuarias no cambia. Prueba de vista en `tests/test_despliegue.py`.
- [ ] T015 [US2] `scripts/windows/instalar.ps1`: tareas «Confrontador · procesamiento» (al iniciar el sistema, reintento cada 1 min hasta 999, sin límite de duración), «Confrontador · diario» (02:00) y «Confrontador · verificación» (cada 5 min), con la cuenta de servicio y sin sesión iniciada (`specs/046-despliegue/contracts/servidor.md`).
- [ ] T016 [US2] `scripts/windows/verificar.ps1`:
  - revisa la web (HTTPS 200 en `/accounts/login/`), el latido, la base (`check --database default`), `soffice --version`, la capa de sentido si está activa y el certificado (`IIS_CERTIFICADO`);
  - **recursos (FR-013)**: avisa si SQL Server no tiene tope de memoria (`max server memory (MB)` en su valor por defecto, 2147483647, según `sys.configurations`) o si el tope deja menos de 6 GB libres al resto del servidor;
  - **disco**: avisa si al disco de `C:\ConfrontadorNotarial`, al de `EXPEDIENTES_TEMP_DIR` y `EXPEDIENTES_ORIGINALES_DIR` o al de `RESPALDO_DIR` les queda menos del 10 % libre (parámetro `-UmbralDisco`, por defecto 10, para probarlo);
  - escribe `certificado.vence`;
  - registra cada problema en el Visor de eventos;
  - sin argumentos, imprime el resumen (FR-015).
- [ ] T017 [US2] En el servidor de prueba: escenarios 3 (reinicio, menos de 5 min), 4 (worker terminado a la fuerza, menos de 2 min) y 10 (tres avisos en menos de 15 min, que desaparecen al corregir).

## Phase 5: User Story 3 · Respaldo diario y restauración probada (P1)

**Goal**: respaldo diario de la base y los originales, 30 días, restauración probada.

**Independent Test**: escenarios 5 y 6.

- [ ] T018 [P] [US3] `scripts/windows/respaldar.ps1`:
  - `BACKUP DATABASE confrontador TO DISK = '<RESPALDO_DIR>\confrontador-AAAAMMDD.bak' WITH CHECKSUM, INIT` con `sqlcmd`, leyendo la clave de `erp.env`;
  - `robocopy /MIR` de los originales a `originales-AAAAMMDD`;
  - borra lo de más de 30 días;
  - escribe `respaldo.ok` si todo salió bien y registra un error en el Visor de eventos si no.
- [ ] T019 [P] [US3] `scripts/windows/restaurar.ps1 -Fecha AAAAMMDD [-Prueba]`:
  - sin `-Prueba`: detiene la web y el worker, `RESTORE ... WITH REPLACE`, restaura los originales y arranca;
  - con `-Prueba`: restaura en `confrontador_prueba_restauracion`, compara las huellas SHA-256 de los originales e informa, sin tocar producción.
- [ ] T020 [US3] La tarea «Confrontador · diario» ejecuta `iniciar.ps1 -Rol tarea -Comando limpiar_temporales` y luego `respaldar.ps1` (`scripts/windows/instalar.ps1`).
- [ ] T021 [US3] En el servidor de prueba: escenarios 5 (7 días, retención) y 6 (restauración de prueba en menos de 1 h).

## Phase 6: User Story 4 · El desarrollador instala y actualiza a distancia (P2)

**Goal**: actualización y vuelta atrás reproducibles, que nunca quedan a medias.

**Independent Test**: escenarios 7 y 8.

- [ ] T022 [US4] `scripts/windows/actualizar.ps1`:
  - `-Version <tag>`: prepara `versiones\<tag>` (código, `.venv` con `--require-hashes` o los wheels del paquete, `collectstatic`), ejecuta `respaldar.ps1`, detiene la web y el worker, `migrate`, cambia el enlace `actual` al final, arranca y ejecuta `verificar.ps1`;
  - `-VolverA <tag>`: restaura el respaldo previo y vuelve a enlazar `<tag>` (research R9).
- [ ] T023 [US4] En el servidor de prueba: escenarios 7 (actualizar y volver atrás, menos de 15 min cada uno) y 8 (sesión cortada a mitad).

## Phase 7: User Story 5 · Funciona sin internet (P2)

**Goal**: todos los recursos en el servidor.

**Independent Test**: escenario 9.

- [ ] T024 [US5] Pasos de aprovisionamiento en `specs/046-despliegue/quickstart.md` §3: OCR y diccionario como la cuenta de servicio; LibreOffice en el PATH del sistema. En el servidor de prueba, escenario 9: un día sin internet, todos los formatos y ninguna conexión saliente del ERP.

## Phase 8: User Story 6 · Mantenimiento diario sin intervención (P3)

**Goal**: temporales limpios y registros acotados.

**Independent Test**: escenario 12.

- [ ] T025 [US6] En el servidor de prueba, escenario 12: tras una semana, sin temporales de más de 24 h y registros rotados de 5 MB × 10, sin DNI, nombres ni texto.

## Phase 9: Polish & Cross-Cutting

- [ ] T026 [P] `docs/arquitectura/erp-notarial-c4.drawio`: vista de despliegue nativa (research R11).
- [ ] T027 [P] `docs/roadmap.md` (entrada F8), `README.md` y `AGENTS.md`: enlace a `specs/046-despliegue/quickstart.md` y mención de `waitress`.
- [ ] T028 Escenario 11 (10 sesiones a la vez, menos de 2 s) en el servidor de prueba (SC-006).
- [ ] T029 Puertas: `ruff check`, `ruff format --check`, `pytest`, `pip_audit --strict` y `pre-commit run --all-files` en verde; estado de `specs/046-despliegue/spec.md` actualizado.

## Dependencies & Execution Order

- **Setup (T001–T003)** → **Foundational (T004–T007)** → historias.
- **US1** (T008–T010) es el MVP. **US2** (T011–T017) y **US3** (T018–T021) dependen de Foundational y de T009 (`instalar.ps1`).
- **US4** (T022–T023) depende de US3 (`respaldar.ps1`).
- **US5** (T024) y **US6** (T025) dependen de US1 y US2.
- `tests/test_despliegue.py` lo comparten T004, T006, T011 y T014: una tras otra.
- `scripts/windows/instalar.ps1` lo comparten T009, T015 y T020: una tras otra.
- Las tareas «En el servidor de prueba» (T010, T017, T021, T023, T024, T025, T028) necesitan un servidor con IIS y la CA del dominio. No se pueden hacer en el equipo de desarrollo.

## Parallel Example

```text
Tras T007, en paralelo:
  T008 [US1] scripts/windows/web.config
  T018 [US3] scripts/windows/respaldar.ps1
  T019 [US3] scripts/windows/restaurar.ps1
  T026       docs/arquitectura/erp-notarial-c4.drawio
```

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1. El ERP se abre por HTTPS desde las PC.
2. US2 y US3, los otros P1: siempre en marcha, con avisos y con respaldo probado.
3. US4: actualizaciones a distancia.
4. US5, US6 y Polish.
5. En el equipo de desarrollo se completan el código y los scripts (T002–T009, T011–T016, T018–T020, T022 y T026–T027) con sus pruebas. Las validaciones en servidor quedan para cuando la notaría dé el servidor de prueba o la ventana de instalación.
