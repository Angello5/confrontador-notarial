# Implementation Plan: F2 · Esqueleto del ERP

**Branch**: `feature/f2-esqueleto` | **Date**: 2026-09-18 | **Spec**: [spec.md](spec.md)

**Input**: `specs/002-esqueleto-erp/spec.md`, incluidas las respuestas registradas en Clarifications.

## Summary

Entregar login, cambio obligatorio de clave temporal, bloqueo temporal de ingreso y layout base con navegación por permisos, más administración de cuentas mediante el Django admin nativo. Se usarán dos grupos de negocio (`Administrador`, `Usuario`), autenticación/sesiones Django, PostgreSQL en producción y assets locales AdminLTE 4 + Alpine.js. Sin funciones de negocio, vistas propias de gestión, correo o IA.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Django 5.2 LTS (último parche soportado al implementar), `psycopg[binary]`, `django-crispy-forms`, `crispy-bootstrap5`; AdminLTE 4, Bootstrap 5 y Alpine.js vendorizados en `static/vendor/`, sin CDN.

**Storage**: PostgreSQL en producción y en pruebas Django de F2 mediante service container en el job `tests` existente.

**Testing**: pytest + pytest-django y pytest-cov, con datos ficticios y PostgreSQL service container en el job `tests` actual; incluir pruebas concurrentes del bloqueo y la regla del último Administrador.

**Target Platform**: servidor on-premise accesible por LAN; CI existente Ubuntu 24.04, Python 3.13.

**Project Type**: aplicación web Django monolítica con plantillas.

**Performance Goals**: no se define latencia objetivo para el flujo síncrono de acceso; no hay procesamiento en segundo plano dentro de F2.

**Constraints**: sin dependencia externa en tiempo de ejecución, sin CDN, correo, SPA, API pública, IA ni pantallas propias de administración. Mantener los cinco controles y la puerta Sonar del CI sin crear jobs nuevos. Login, cambio de clave y layout deben cumplir VIII de la constitución y A11Y-001. No usar suberusuario para cuentas ordinarias; persistir claves solo como hashes. Nunca datos reales en tests, fixtures o logs.

**Scale/Scope**: hasta 10 cuentas del ERP; dos roles; ambos ven «Inicio», solo Administrador ve el enlace «Administración»; login, cambio inicial de clave, layout/navegación y gestión de cuenta/rol en Django admin. No funcionalidades F3 en adelante.

## Constitution Check

| Principio | Comprobación del diseño |
|---|---|
| I. Determinismo y sin IA | No hay modelos de lenguaje, servicios IA ni reglas variables; las respuestas de autenticación usan el mismo resultado ante estado equivalente. |
| II. Núcleo de dominio puro | F2 no modifica el núcleo ni sus adaptadores. Vistas de login/cambio/layout se mantienen delgadas; administración nativa de Django. |
| III. Pruebas primero | Pruebas Django ficticias deben reproducir primero el fallo para acceso, cambio inicial, autorización, revocación de sesión y reglas del último Administrador. |
| IV. Privacidad | No se almacenan claves temporales en claro, correo ni documentos; mensajes de login genéricos y logs sin contraseñas, nombres o contenido de casos reales. |
| V. Simplicidad | Monolito Django existente, grupos/permisos nativos, plantillas y Admin. No se añaden API, SPA, cola, caché ni abstracciones de un solo uso. La necesidad de cada dependencia está descrita en Complexity Tracking. |
| VI. Seguridad y control de acceso | Dos grupos, `is_staff` técnico más grupo Administrador para Django Admin, autorización servidor en cada ruta; creación inicial por comando; cambio de clave obligatorio; sesiones invalidadas al desactivar; bloqueo de ingreso en PostgreSQL y guardas contra auto-desactivación y último Administrador. |
| VII. DevSecOps | Tests en job `tests` existente; lint, formato, SAST/Sonar, SCA y secretos siguen en el workflow sin relajar gates. Locks mantienen hashes. No escanear/añadir dependencias sin actualización de locks. |
| VIII. Usabilidad | Se especifican estados, mensajes, vocabulario español, navegación consistente, validación, confirmación, foco, teclado y ayuda para login, cambio de clave y layout. Revisar las 10 heurísticas con checklist antes del merge. |

**Resultado previo a investigación**: compatible. PostgreSQL de CI valida el mismo backend de producción y la regla concurrente de seguridad.

## Project Structure

### Documentación de esta funcionalidad

```text
specs/002-esqueleto-erp/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/ui.md
├── checklists/requirements.md
├── checklists/ux.md            # lista generada por las tareas de F2
└── tasks.md
```

### Código previsto para implementación posterior

```text
config/                         # settings, urls, ASGI/WSGI del proyecto Django
accounts/
├── models.py                   # AbstractUser de proyecto e indicadores de sesión/claves
├── backends.py                 # autenticación común con contador y bloqueo persistente
├── apps.py                     # permisos mínimos del grupo Administrador tras migraciones
├── admin_site.py               # acceso nativo limitado a staff del grupo Administrador
├── admin.py                    # personalización acotada del Django UserAdmin nativo
├── forms.py                    # formularios Django auth, renderizados con crispy-bootstrap5
├── views.py                    # login, cambio inicial de clave e inicio
├── middleware.py               # obliga a cambiar clave antes del resto del ERP
├── management/commands/
│   └── bootstrap_admin.py      # aprovisiona el primer Administrador
└── migrations/                 # modelo de usuario desde la migración inicial
config/apps.py                  # configura el AdminSite nativo del proyecto
tests/test_login_lockout.py     # persistencia, respuestas genéricas y concurrencia del bloqueo
core/
├── urls.py                     # rutas de login, cambio de clave e inicio
└── views.py                    # inicio autenticado
templates/
├── registration/               # login/cambio de clave en español
└── core/                       # layout AdminLTE y navegación por permisos
static/vendor/                  # versiones locales anotadas; sin CDN
requirements.in                 # dependencias directas de Django y formularios
requirements.txt                # lock con hashes generado desde requirements.in
requirements-dev.in             # pytest-django
requirements-dev.txt            # lock de desarrollo con hashes
pyproject.toml                  # configuración de pytest/pytest-django
.github/workflows/ci.yml        # conservar job tests y pasos/gates existentes
```

**Structure Decision**: Mantener un proyecto Django monolítico, una app `accounts` para la autenticación y el ciclo de vida del usuario, y una app `core` mínima para layout. El árbol es destino planificado, no creado por este trabajo. No crear app separada para cada página ni contrato de API pública.

## Constitution Check después del diseño

Pasan I–VIII: roles y administración concuerdan con la enmienda VI, no hay pantallas administrativas propias, los controles de cuenta se fuerzan también en servidor y la interfaz (login, cambio, layout y Admin nativo) tiene revisión Nielsen y accesibilidad. No se requiere exención constitucional. Complejidad añadida queda limitada a framework/driver/formularios/assets necesarios para el stack definido y pruebas Django.

## Complexity Tracking

| Elemento | Motivo | Alternativa más simple considerada y razón para descartarla |
|---|---|---|
| Django y `psycopg[binary]` | Son el framework y el driver requeridos por la constitución para la aplicación y PostgreSQL de producción; el repo F1 aún no los contiene. | Flask/SQLite no cumple stack ni backend de producción exigidos. |
| `django-crispy-forms` y `crispy-bootstrap5` | La constitución exige formularios con crispy-bootstrap5 para las pantallas propias. | Formularios Django sin crispy no cumplirían el stack establecido. |
| pytest-django | Integra fixtures/configuración y ciclo de DB de Django en las pruebas existentes con pytest. | Configurar manualmente cada test requeriría más código y produciría una integración incompleta. |
| AdminLTE 4 y Alpine.js locales | Requisitos de interfaz de la constitución; UI local sin CDN. | No incluirlos incumple el stack; no se añade otro toolkit ni gestor JS de runtime. |
| PostgreSQL service container en job `tests` | Las transacciones con bloqueo que garantizan el contador de intentos y conservar un Administrador deben probarse con la semántica del motor de producción y frente a operaciones concurrentes. Se conserva el job único de tests y sus gates actuales. | SQLite no implementa los bloqueos de fila de PostgreSQL y no demostraría ambas reglas bajo concurrencia. No se añaden jobs ni servicios externos persistentes. |
| `force_password_change` y `session_version` en el usuario | Hacen verificables el cambio temporal obligatorio y la invalidación inmediata incluso después de reactivar una cuenta. | Borrar sesiones requiere recorrerlas y acopla el flujo a su almacén; cambiar la clave temporal invalida sesiones pero altera credencial y no permite reactivación limpia. |
