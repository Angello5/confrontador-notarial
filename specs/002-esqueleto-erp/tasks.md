# Tasks: F2 · Esqueleto del ERP

**Input**: Design documents in `specs/002-esqueleto-erp/`.

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/ui.md`, `quickstart.md`.

**Tests**: Django auth/session/authorization rules require tests first with fictional accounts. Keep them in the existing `pytest` invocation within CI job `tests`.

**Organization**: Setup, Foundation, then independently testable user stories in spec priority order, then polish. Each phase closes with a validation checkpoint and local commit. Implement no F3 behavior.

## Phase 1: Setup

- [X] T001 Add pinned Django 5.2 LTS, psycopg, django-crispy-forms and crispy-bootstrap5 direct dependencies in `requirements.in`; add pytest-django in `requirements-dev.in`; compile hash-pinned `requirements.txt` and `requirements-dev.txt`.
- [X] T002 [P] Vendor AdminLTE 4, its Bootstrap 5 assets, and Alpine.js into `static/vendor/`; record exact upstream versions, licenses and SHA-256 values in `static/vendor/README.md`.
- [X] T003 Configure Django test discovery in `pyproject.toml` and PostgreSQL service container in the existing `tests` job in `.github/workflows/ci.yml`; make pytest collect Django tests without adding a CI job.
- [X] T004 **Checkpoint**: run dependency lock verification, `ruff check`, `ruff format --check`, and existing tests; review `requirements.in`, `requirements-dev.in`, both lock files, `static/vendor/`, `pyproject.toml`, and `.github/workflows/ci.yml`; commit this stage locally as `feat(f2): set up Django test foundation`.

## Phase 2: Foundational

- [X] T005 Create the Django project settings, URL configuration and WSGI/ASGI entry points in `config/settings.py`, `config/urls.py`, `config/wsgi.py` and `config/asgi.py`; use environment variables with stdlib parsing for PostgreSQL and PostgreSQL-backed tests.
- [X] T006 Define the project user model based on `AbstractUser`, its initial migration, role group seed migration and database-session configuration in `accounts/models.py`, `accounts/migrations/0001_initial.py`, `accounts/migrations/0002_seed_roles.py` and `config/settings.py`.
- [X] T007 Add shared test settings and fictional-account fixtures in `tests/conftest.py`; verify Django checks, migration application and that exactly Administrador and Usuario groups are available against PostgreSQL.
- [X] T008 **Checkpoint**: run `python manage.py check`, migrations, pytest, lint and format checks; review `config/`, `accounts/models.py`, `accounts/migrations/`, and `tests/conftest.py`; commit this stage locally as `feat(f2): add auth foundation`.

## Phase 3: User Story 1 - Ingresar al ERP (Priority: P1) 🎯 MVP

**Goal**: una cuenta habilitada ingresa, cambia su clave temporal si aplica y ve el layout permitido; una cuenta desactivada o sin autorización no accede.

**Independent test criteria**: comprobar login público, rechazo genérico de credenciales inválidas/inactivas, obligación del cambio temporal, bloqueo de otras rutas antes del cambio, inicio autenticado, navegación por permisos y denegación servidor-side de rutas no autorizadas.

- [X] T009 [P] [US1] Add failing tests for valid/invalid/inactive login, generic errors, redirects and protected routes in `tests/test_login.py`.
- [X] T010 [P] [US1] Add failing tests for mandatory initial password change, password validation and route blocking in `tests/test_password_change.py`.
- [X] T011 [P] [US1] Add failing tests for role-based home/menu rendering, access control and accessibility-visible labels in `tests/test_shell.py`.
- [X] T012 [US1] Implement `force_password_change` and `session_version` fields with migrations in `accounts/models.py` and `accounts/migrations/0003_account_security_state.py`.
- [X] T013 [US1] Implement login, password-change forms, views and URL routes using Django auth in `accounts/forms.py`, `accounts/views.py`, `accounts/urls.py` and `config/urls.py`.
- [X] T014 [US1] Implement middleware that restricts pending-change sessions across every internal route, including `/admin/`, to logout/password change in `accounts/middleware.py` and register it in `config/settings.py`.
- [X] T015 [US1] Create Spanish login and password-change templates with AdminLTE 4, crispy-bootstrap5, keyboard labels, visible focus, help, confirmations and clear recovery messages in `templates/registration/login.html` and `templates/registration/password_change_form.html`.
- [X] T016 [US1] Create the permission-filtered Spanish ERP shell with minimal empty F2 navigation in `templates/core/base.html`, `templates/core/home.html`, `core/views.py` and `core/urls.py`.
- [X] T017 [US1] **Checkpoint**: confirm T009–T011 fail before implementation, then run the US1 tests, Django checks, lint and format; review `accounts/`, `core/`, `templates/`, and `tests/test_login.py`, `tests/test_password_change.py`, `tests/test_shell.py`; commit this stage locally as `feat(f2): add login and ERP shell`.

> Nota de revisión de T009–T011: cinco pruebas de login/layout (pendiente en `/admin`, cuenta sin rol con 403, etiquetas en español y disponibilidad local de AdminLTE/Alpine) se incorporaron junto con la implementación; no se atribuye el orden TDD retroactivamente.

## Phase 4: User Story 2 - Administrar cuentas (Priority: P1)

**Goal**: el Administrador crea cuentas con clave temporal, gestiona roles desde Django admin y revoca sesiones al desactivar, con salvaguardas contra auto-desactivación y pérdida del último Administrador.

**Independent test criteria**: con cuentas ficticias probar alta con rol único, primer cambio de clave, revocación efectiva de sesiones al desactivar, reactivación con nueva autenticación, denegación de acciones directas por Usuario y rechazo del propio operador o del último Administrador activo.

- [X] T017a [US2] Add failing tests for five consecutive login failures, generic response for locked/nonexistent accounts, successful reset, `/admin` coverage and concurrent PostgreSQL attempts in `tests/test_login_lockout.py` (verified red before T017b).
- [X] T017b [US2] Implement database-backed login lockout fields, migration and shared Django authentication backend in `accounts/models.py`, `accounts/migrations/0004_login_lockout.py` and `accounts/backends.py`.

- [X] T018 [P] [US2] Add failing tests for creating accounts with username, temporary password, required role and no email; include group tampering attempts and administrative unlock in `tests/test_account_admin.py` (verified red before T020).
- [X] T019 [P] [US2] Add failing tests for instant session invalidation across deactivation/reactivation, `session_version` in `get_session_auth_hash`, and protection against self-disable/last-admin removal in `tests/test_account_lifecycle.py` (verified red before T020–T021).
- [X] T019a [US2] Add failing tests for one-time bootstrap creation, mandatory first password change, no password output and duplicate active Administrator rejection in `tests/test_bootstrap_admin.py` (verified red before T022).
- [X] T019b [US2] Add a failing test for role assignment updating staff status and invalidating existing sessions via `session_version` in `tests/test_account_role_change.py` (verified red before T021).
- [X] T020 [US2] Implement account creation/edit forms and native `UserAdmin` limited to the two role groups and minimum account fields; allow Administrators to clear the login lockout fields with the «Desbloquear intentos de ingreso» action from the account list and disable account/role-group deletion in `accounts/forms.py` and `accounts/admin.py`.
- [X] T021 [US2] Implement transactional deactivation/reactivation and role changes, locking active Administrators, incrementing `session_version` (used by `get_session_auth_hash`) and rejecting self/last-administrator transitions in `accounts/admin.py` and `accounts/models.py`.
- [X] T022 [US2] Implement `bootstrap_admin` command that creates the first staff Administrator with a one-time temporary password and mandatory first-login change, without a default or logged password in `accounts/management/commands/bootstrap_admin.py`.
- [X] T023 [US2] Use Spanish locale for native Django admin confirmations and validation messages in `config/settings.py`; verify role-specific menu links and admin action feedback in `tests/test_account_admin.py` and `tests/test_shell.py`.
- [X] T024 [US2] **Checkpoint**: confirm T017a, T018–T019 fail before implementation; run lockout, account admin/lifecycle and auth integration tests, concurrent lockout and last-administrator tests, lint, format and migrations against PostgreSQL; review `accounts/` and auth/account tests; commit this stage locally as `feat(f2): manage accounts in Django admin`.

## Phase 5: Polish and cross-cutting validation

- [X] T025 [P] Document PostgreSQL configuration, bootstrap command and manual login/password/admin scenarios in `specs/002-esqueleto-erp/quickstart.md`.
- [X] T026 [P] Generate the Nielsen and accessibility review checklist for login, password change, ERP shell and native Django admin in `specs/002-esqueleto-erp/checklists/ux.md`.
- [X] T027 Verify no external runtime/CDN calls, real personal data, secrets, or F3 behavior; audit dependency locks and asset licenses in `requirements.txt`, `requirements-dev.txt`, `static/vendor/README.md`, and the F2 source tree.
- [X] T028 **Final checkpoint**: ejecutar el checkpoint local de `AGENTS.md` (Django check, migraciones, generación de fixtures, pytest con cobertura, Ruff, pip-audit estricto y pre-commit); los controles remotos y el Sonar Quality Gate quedan para el PR; revisar `specs/002-esqueleto-erp/` y el árbol F2; commit local de esta corrección como `fix(f2): address final review`.

Nota TDD de la revisión final: `4ee8e36` entró con dos pruebas en rojo; la aserción del desbloqueo cambió en el commit de corrección.

## Dependencies

- Setup (T001–T004) → Foundation (T005–T008) → US1 (T009–T017) → US2 (T018–T024) → Polish (T025–T028).
- US1 requires Foundation because Django settings, custom user model and tests must exist first.
- US2 requires US1's authentication routes and custom user state; the lockout backend test (T017a) must be committed red before T017b, which precedes account lifecycle administration. US1 remains independently usable as the MVP before US2 is completed.

## Parallel opportunities

- T002 can run alongside dependency declaration/locking in T001 because assets are separate from Python locks.
- T009, T010 and T011 target different test files and can be authored in parallel after Foundation.
- T017a is committed red, then T017b is implemented before T018–T019; T018 and T019 target separate test files and can be authored in parallel.
- T025 and T026 edit separate documentation files and can run in parallel.

## Implementation strategy

Deliver Setup and Foundation first. Build and validate US1 as the MVP, then add US2 without weakening US1. Complete each phase checkpoint, test, review, and local commit before starting the next phase. Run no implementation task from this planning work.
