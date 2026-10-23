# F62 · Cookies propias del ERP

**Fecha**: 2026-10-23  
**Estado**: implementado.

## Origen

El usuario reportó el 2026-10-23: «cada vez que le doy un click me manda al login». En el equipo corrían dos aplicaciones Django: el ERP en `127.0.0.1:8000` y otra en `127.0.0.1:8001`. Los navegadores separan las cookies por host, no por puerto, y las dos usaban `sessionid`. La otra aplicación recibía la sesión del ERP, no la reconocía en su base de datos y respondía borrándola. En el siguiente clic, el ERP ya no tenía sesión. El log lo muestra: una petición del ERP con sesión y, dos segundos después, la siguiente sin ella.

## Comportamiento

- **FR-001**: la cookie de sesión del ERP se llama `confrontador_sesion` y la de CSRF, `confrontador_csrftoken`.
- **FR-002**: una cookie `sessionid` de otra aplicación en el mismo host no cierra la sesión del ERP, y el ERP no la borra.

Al desplegar el cambio, las sesiones abiertas se cierran una vez, porque la cookie anterior deja de leerse.

## Seguridad

- Siguen vigentes `Secure` (fuera de DEBUG), `HttpOnly` en la sesión y el almacenamiento en base de datos.
- Ningún JavaScript lee las cookies por su nombre: los formularios llevan el token CSRF en un campo oculto.
