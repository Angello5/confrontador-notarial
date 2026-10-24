-- F63 · Base, login y usuario del ERP en el SQL Server de la notaría.
-- Lo ejecuta el administrador con una cuenta con permisos de servidor:
--   sqlcmd -S <servidor> -E -b -v ERP_CLAVE="<clave>" -i scripts/sqlserver/crear_base.sql
-- La clave llega por variable y nunca se escribe en este archivo.
-- Contrato: specs/045-sql-server/contracts/configuracion.md
-- La clave no puede llevar comillas simples.
:on error exit
SET NOCOUNT ON;

DECLARE @version int = CAST(SERVERPROPERTY('ProductMajorVersion') AS int);
DECLARE @edicion nvarchar(128) = CAST(SERVERPROPERTY('Edition') AS nvarchar(128));
PRINT CONCAT('SQL Server ', CAST(SERVERPROPERTY('ProductVersion') AS nvarchar(32)), ', ', @edicion);
IF @version < 13
BEGIN
    RAISERROR('Se necesita SQL Server 2016 o posterior.', 16, 1);
    RETURN;
END;
IF @edicion LIKE N'%Express%'
    PRINT 'Aviso: la edición Express limita cada base a 10 GB.';

IF DB_ID(N'confrontador') IS NOT NULL OR SUSER_ID(N'confrontador') IS NOT NULL
BEGIN
    RAISERROR('La base o el login «confrontador» ya existen; no se cambió nada.', 16, 1);
    RETURN;
END;
GO

-- Distingue mayúsculas y tildes, como exige el ERP (research R2).
CREATE DATABASE confrontador COLLATE Modern_Spanish_100_CS_AS;
GO

CREATE LOGIN confrontador
    WITH PASSWORD = N'$(ERP_CLAVE)', CHECK_POLICY = ON, DEFAULT_DATABASE = confrontador;
GO

USE confrontador;
CREATE USER confrontador FOR LOGIN confrontador;
-- db_owner solo en su base: las migraciones crean y cambian tablas. Sin roles de servidor.
ALTER ROLE db_owner ADD MEMBER confrontador;
GO

PRINT 'Base y login del ERP creados.';
