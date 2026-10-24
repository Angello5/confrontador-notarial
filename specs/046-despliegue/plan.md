# Implementation Plan: F8 · Despliegue en el servidor de la notaría

**Branch**: `feat/f8-despliegue` | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

## Summary

El ERP se instala de forma nativa en SQLSERVER (Windows Server 2019), junto a su SQL Server 2016:

- **IIS** atiende HTTPS con el certificado de la CA del dominio, redirige HTTP, sirve los estáticos y, con HttpPlatformHandler, arranca y supervisa la web (`waitress`).
- **El Programador de tareas de Windows** mantiene vivo el worker y ejecuta, con una cuenta de servicio sin privilegios, la limpieza y el respaldo diarios y una verificación cada 5 minutos.
- **Un lanzador PowerShell** carga la configuración y las claves desde un archivo protegido.
- **Tres archivos de estado** alimentan los avisos del Inicio del Administrador y del Visor de eventos.
- **La actualización** prepara cada versión aparte y cambia un enlace al final, con un respaldo previo a las migraciones.

Detalle en [research.md](research.md).

## Technical Context

- **Language/Version**: Python 3.13 (ERP) y Windows PowerShell 5.1 (scripts de servidor, incluido en Windows Server 2019).
- **Primary Dependencies**:
  - Django 5.2 y `mssql-django` 1.8.0 (F63);
  - **nueva**: `waitress` 3.0.2, sin dependencias en ejecución;
  - **del sistema**: IIS con URL Rewrite y HttpPlatformHandler, ODBC Driver 18, `sqlcmd` y LibreOffice.
- **Storage**: SQL Server 2016, base `confrontador` (F63). Sin cambios de esquema. Estado de operación en archivos ([data-model.md](data-model.md)).
- **Testing**:
  - pytest para la lógica Python nueva: avisos, latido y `LOGGING`;
  - análisis sintáctico de los `.ps1` con PowerShell, que existe en los runners del CI;
  - validación de extremo a extremo en un servidor de prueba con los escenarios de [quickstart.md](quickstart.md).
- **Target Platform**: SQLSERVER (Windows Server 2019, Xeon Bronze 3204 de 6 núcleos, 64 GB), en la LAN de la notaría.
- **Project Type**: monolito Django on-premise.
- **Performance Goals**: hasta 10 usuarias, pantallas en menos de 2 s (SC-006). Un proceso web con 8 hilos y un worker.
- **Constraints**:
  - sin internet en ejecución;
  - sin claves en la línea de comandos ni en el repositorio;
  - comparte el servidor con SQL Server y otros sistemas;
  - el desarrollador opera a distancia.
- **Scale/Scope**: un servidor. Unos 12 archivos nuevos (scripts y `web.config`) y cambios pequeños en `settings`, el worker y el Inicio.

## Constitution Check

| Principio | Cómo se cumple |
|---|---|
| I. Determinismo | El núcleo no cambia. La medición del expediente de referencia se repite en el servidor de prueba. |
| II. Núcleo puro | Nada de despliegue entra en `nucleo/`. Los avisos se leen en `expedientes/services.py` y la vista solo los muestra. |
| III. Pruebas primero | Avisos (umbrales y ausencia de `ERP_ESTADO_DIR`), latido del worker y rotación de registros empiezan con pruebas que fallan. |
| IV. Privacidad | Respaldos con ACL restringida y en el mismo servidor. Registros rotados sin datos personales. Temporales limpiados a diario. El texto extraído solo vive en la base y en su respaldo. |
| V. Simplicidad | Componentes de Windows en lugar de terceros: IIS, Programador de tareas, Visor de eventos. Una sola dependencia Python nueva (`waitress`) y un solo lanzador para la web, el worker y las tareas. |
| VI. Seguridad | HTTPS con la CA del dominio. Solo 443/80 abiertos a la LAN. Cuenta de servicio sin privilegios. Claves en un archivo con ACL. Funciona sin internet. |
| VII. DevSecOps | `waitress` con hash y auditada por `pip-audit`. Los scripts se analizan en el CI. gitleaks sigue cubriendo el repositorio. Sin imágenes de contenedor que escanear. |
| VIII. Usabilidad | Avisos con el componente existente del Inicio y lenguaje llano (spec, UX). |
| Restricciones técnicas | Constitución 2.2.0 (enmendada en esta rama): despliegue nativo en Windows, servicios con cuenta propia, HTTPS de la CA del dominio y respaldo diario de 30 días. |

Resultado: sin violaciones.

## Estructura

```text
config/settings.py                 # STATIC_ROOT, LOGGING rotado (ERP_REGISTROS_DIR), ERP_ESTADO_DIR
expedientes/services.py            # avisos_sistema(): lee los archivos de estado
expedientes/management/commands/procesar_documentos.py  # toca worker.latido en cada vuelta
core/views.py, templates/core/home.html  # avisos del sistema en el Inicio del Administrador
requirements.in, requirements.txt  # + waitress (tzdata/colorama al final, a mano)
scripts/windows/
  erp.env.ejemplo   comun.ps1     iniciar.ps1   web.config
  instalar.ps1      actualizar.ps1
  respaldar.ps1     restaurar.ps1   verificar.ps1
static/mantenimiento.html          # página de IIS durante una actualización
templates/500.html                 # error del servidor en español
tests/test_despliegue.py           # avisos, latido, LOGGING y sintaxis de los .ps1
docs/arquitectura/erp-notarial-c4.drawio  # vista de despliegue nativa
docs/roadmap.md, README.md, AGENTS.md
```

## Complexity Tracking

| Complejidad | Por qué | Alternativa descartada |
|---|---|---|
| Dependencia nueva `waitress` | El ERP no tiene servidor WSGI de producción, y `runserver` no sirve para producción. | gunicorn (no corre en Windows); uvicorn (ASGI y más dependencias). |
| Siete scripts PowerShell | Cada uno es una operación que el desarrollador repite a distancia: instalar, arrancar, actualizar, respaldar, restaurar y verificar. | Pasos manuales en una guía (no reproducibles ni verificables). |
| Módulos IIS de Microsoft (URL Rewrite, HttpPlatformHandler) | HTTPS con la CA del dominio, redirección y supervisión del proceso web. | Servicio propio con `pywin32`, o proxy de terceros. |

## Riesgos

- **SQL Server 2016 sin soporte** (F63): ya informado.
- **El servidor no alcanza GitHub/PyPI en el mantenimiento**: paquete con código y wheels (research R9).
- **Edición Express**: sin SQL Server Agent. El respaldo no depende de él (R5).
- **HttpPlatformHandler**: Microsoft lo recomienda para Python, pero es un módulo antiguo. Si dejara de estar disponible, la alternativa es el ASP.NET Core Module o un servicio con `pywin32`, sin cambiar el resto.
- **Validación**: los escenarios de extremo a extremo necesitan un servidor de prueba con IIS y la CA del dominio. En este equipo de desarrollo solo se prueba la parte Python y la sintaxis de los scripts.
