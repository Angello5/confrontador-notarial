# Contratos de interfaz: F2

No se expone API pública ni se crean pantallas de gestión propias. Django admin es la interfaz nativa para las operaciones administrativas.

| Ruta | Acceso | Resultado esperado |
|---|---|---|
| `/accounts/login/` | Público | Login en español; cuenta inválida o inactiva obtiene mensaje genérico sin filtrar existencia. Si `force_password_change=true`, redirige a cambio de clave antes de mostrar el ERP. |
| `/accounts/password-change/` | Sesión autenticada con cambio pendiente | Solicita y valida nueva clave; éxito limpia el indicador y lleva al inicio. Todas las demás rutas internas, incluido `/admin/`, permanecen bloqueadas mientras exista cambio pendiente. |
| `/` | Sesión autenticada y cambio completo | Layout AdminLTE en español con navegación visible permitida por los permisos del rol. No hay módulos de negocio en F2. |
| `/admin/` | Administrador con `is_staff` y permisos nativos | Admin Django para crear, asignar rol, desactivar y reactivar cuentas. Rechaza intentos directos sin permiso, auto-desactivación y desactivación del último Administrador activo. |

Login, cambio de clave e inicio usan etiquetas accesibles, teclado/foco visible, mensajes de estado y salida, español, navegación consistente y assets locales. La confirmación de guardado y el error de validación permanecen en la página; una denegación nunca revela si otro usuario existe. Las acciones de desactivación requieren confirmación en Django admin.
