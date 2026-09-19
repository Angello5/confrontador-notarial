# Data Model: F2 · Esqueleto del ERP

## Cuenta de usuario

Modelo de proyecto basado en `django.contrib.auth.models.AbstractUser`; conservar `username` como identificador único de inicio de sesión y el hash de contraseña de Django. Campos adicionales:

| Campo | Tipo | Regla |
|---|---|---|
| `force_password_change` | boolean, requerido, default false | Para una cuenta creada por Administración con clave temporal vale true hasta que la persona cambie la clave en su primer ingreso. |
| `session_version` | entero positivo, requerido, default 0 | Aumenta al desactivar la cuenta o asignar una clave temporal desde `/admin`; participa en el hash de autenticación y vuelve irrecuperables las sesiones anteriores. |
| `failed_login_attempts` | entero positivo, requerido, default 0 | Cuenta fallos consecutivos de autenticación con bloqueo transaccional por fila. |
| `login_locked_until` | fecha/hora nullable | Rechaza autenticación hasta cumplir 15 minutos; NULL cuando la cuenta no está bloqueada. Un ingreso correcto o desbloqueo administrativo restablece ambos campos. |

El campo nativo `is_active` determina si se permite autenticar. No se guardan claves temporales en claro ni datos personales adicionales; el campo de correo heredado de Django no se solicita ni se usa en F2 y permanece vacío. La clave temporal se entrega fuera de la aplicación por el administrador creador y no se envía por correo. `bootstrap_admin` aplica el mismo cambio obligatorio que las cuentas creadas en Django admin.

## Rol

Usar `Group` y `Permission` de Django, sin entidad propia. Solo existen los grupos de negocio `Administrador` y `Usuario`; cada cuenta F2 pertenece a exactamente uno. `Administrador` requiere `is_staff=True` para acceder a `/admin` y permisos nativos mínimos sobre cuentas y grupos; la bandera `is_superuser` no se usa para usuarios ordinarios. Los permisos determinan el menú y se vuelven a comprobar en servidor.

## Relaciones y transiciones

- Cuenta N:1 Rol mediante la relación `User.groups` de Django, restringida y validada también en servidor a exactamente uno de los dos grupos de negocio.
- Creación administrativa: `username` único, cuenta activa, clave temporal hasheada con Django, `force_password_change=true`, rol requerido.
- Primer cambio de clave válido: la clave pasa por el validador nativo de Django; limpiar `force_password_change` y renovar el hash de sesión de acuerdo con el flujo de cambio de contraseña.
- Desactivación: atómicamente establecer `is_active=false` e incrementar `session_version`; bloquear las filas activas del grupo Administrador en la transacción y rechazar si el operador se apunta a sí mismo o si la operación deja cero cuentas activas.
- Reactivación: `is_active=true`; las sesiones anteriores siguen invalidadas. El restablecimiento de una clave no se incluye en F2 porque no hay correo.
- Bloqueo de ingreso: el backend de autenticación bloquea la fila de usuario en PostgreSQL, incrementa `failed_login_attempts` por fallo y tras el quinto fija `login_locked_until` a 15 minutos; una autenticación correcta o desbloqueo administrativo limpia ambos valores. Cuentas inexistentes reciben respuesta genérica sin persistir contador.
- Borrado: las cuentas se conservan y se desactivan; el Django admin no ofrece borrado de cuentas ni grupos de rol.
- Alta inicial: el comando de gestión crea una sola cuenta Administrador con clave temporal y cambio obligatorio; falla si ya existe un Administrador activo.
- Cambio administrativo de clave: `/admin/<id>/password/` fija `force_password_change=true` e incrementa `session_version`, revocando sesiones abiertas.

## Persistencia

Migración inicial del modelo de usuario antes de las migraciones propias de F2. Sesiones con el backend de base de datos estándar de Django. El sistema conserva únicamente la cuenta y el rol; no registra claves temporales ni valores de contraseña en eventos o logs.
