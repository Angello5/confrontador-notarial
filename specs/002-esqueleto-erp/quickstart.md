# Quickstart de validación: F2

## Prerrequisitos

- Python 3.13 y dependencias instaladas desde los locks con hashes del repositorio.
- Para ejecutar Django fuera de pytest, configurar `DJANGO_SECRET_KEY` mediante
  el entorno del servidor; sin ella la aplicación no inicia. pytest usa una
  clave fija solo en el proceso de pruebas.
- PostgreSQL para validación del backend de producción; CI levanta PostgreSQL como service container en el job `tests`. Su imagen está fijada por digest y se actualiza manualmente: Dependabot no gestiona `services.image`.
- La conexión PostgreSQL usa `POSTGRES_DB`, `POSTGRES_USER`,
  `POSTGRES_PASSWORD`, `POSTGRES_HOST` y `POSTGRES_PORT`; los valores por
  defecto sirven para desarrollo local. En CI se configuran desde el service
  container.
- Assets de AdminLTE 4, Bootstrap 5 y Alpine.js versionados en `static/vendor/`; sin conexión CDN.
- En F8 se confirmará el despliegue con HTTPS interno en la LAN; `SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE` siguen `DEBUG` y se habilitan fuera del modo debug.

## Validación automática en CI

Desde la raíz del repositorio, el job `tests` existente instala los locks y corre generador/pytest de acuerdo con el workflow. Las pruebas Django usan PostgreSQL y datos ficticios; el job `tests` conserva el mismo job existente y aprovisiona la base con service container.

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest -m 'not local_reference' --cov --cov-report=term --cov-report=xml:coverage.xml
```

Resultado esperado: lint, formato y todas las pruebas pasan; cobertura XML no está vacía.

## Escenarios manuales y de integración

1. Aplicar migraciones en PostgreSQL y crear el primer administrador desde el comando de gestión en el servidor. El comando solicita una clave sin imprimirla ni escribirla en logs.
2. Iniciar sesión con Administrador; comprobar `/admin/`, dos roles permitidos y que no existan opciones de negocio F3/F4.
3. Crear una cuenta ficticia Usuario con clave temporal; iniciar sesión y confirmar que primero solo permite cambio de clave. Después, verificar que `/` muestra el layout y que `/admin/` deniega acceso.
4. Desactivar esa cuenta en `/admin/`; verificar que su sesión abierta no puede realizar otra solicitud autenticada. Reactivarla y verificar que requiere un nuevo inicio de sesión.
5. Confirmar que una operación no puede desactivar al propio Administrador ni al último Administrador activo, incluso mediante petición directa o acción administrativa; ejecutar además dos desactivaciones concurrentes y comprobar que al menos un Administrador sigue activo.
6. Ejecutar login y cambio de clave con teclado, verificar etiquetas y foco; probar estados de error, confirmación, ruta de regreso, idioma y ausencia de assets de CDN.
7. Fallar cinco veces el ingreso de una cuenta ficticia; confirmar que `/` y `/admin/` rechazan la clave correcta durante 15 minutos con el mismo mensaje genérico. Confirmar que un ingreso correcto luego del vencimiento reinicia el estado, que Administrador puede desbloquearla desde `/admin` y que el contador concurrente no pierde incrementos.
8. Desde el formulario de cambio de clave de `/admin`, asignar una clave temporal ficticia y comprobar que la cuenta queda obligada a cambiarla y que su sesión anterior deja de ser válida.
