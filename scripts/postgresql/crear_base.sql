-- Base, rol y permisos del ERP en el PostgreSQL 17 de la notaría.
-- Lo ejecuta el administrador con el superusuario:
--   psql -U postgres -v ON_ERROR_STOP=1 -v erp_clave="<clave>" -f scripts/postgresql/crear_base.sql
-- La clave llega por variable y nunca se escribe en este archivo.
\if :{?erp_clave}
\else
    \echo 'Falta la variable erp_clave (-v erp_clave="...").'
    \quit
\endif

SELECT current_setting('server_version_num')::int >= 170000 AS version_ok \gset
\if :version_ok
\else
    \echo 'Se necesita PostgreSQL 17 o posterior.'
    \quit
\endif

SELECT EXISTS (SELECT FROM pg_database WHERE datname = 'confrontador')
    OR EXISTS (SELECT FROM pg_roles WHERE rolname = 'confrontador') AS existe \gset
\if :existe
    \echo 'La base o el rol «confrontador» ya existen; no se cambió nada.'
    \quit
\endif

CREATE ROLE confrontador LOGIN PASSWORD :'erp_clave';

-- Colación ICU determinista: distingue mayúsculas y tildes, y ordena la «ñ»
-- después de la «n».
CREATE DATABASE confrontador
    OWNER confrontador
    ENCODING 'UTF8'
    LOCALE_PROVIDER icu
    ICU_LOCALE 'es-PE'
    LOCALE 'C'
    TEMPLATE template0;

-- Sin roles de servidor: el ERP solo es dueño de su base.
REVOKE ALL ON DATABASE confrontador FROM PUBLIC;

\echo 'Base y rol del ERP creados.'
