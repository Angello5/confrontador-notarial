# Data Model: F53 · Inicio del administrador

**Sin cambios de esquema ni migraciones.** Todo se calcula a partir de modelos
existentes en `expedientes/models.py`.

## Modelos leídos

| Modelo | Campos usados | Para |
|---|---|---|
| `Expediente` | `tipo` (`NOTARIAL` / `VEHICULAR`), `codigo`, `archivado_el`, `creado_por` | Cifras por tipo, filas de confrontaciones, avisos |
| `Documento` | `estado` (`ERROR`), `subido_por`, `expediente` | Avisos de documento ilegible |
| `Corrida` | `expediente`, `usuario`, `creado_el` | Actividad semanal y últimas confrontaciones |
| `User` | `get_full_name()`, `username` | Nombre de la usuaria que ejecutó |

## Estructuras devueltas por los servicios

- **`cifras_por_tipo(usuario)`** → `{"notariales": int, "vehiculares": int,
  "total": int}`; `total == notariales + vehiculares`. Solo kardex visibles y
  activos.
- **`actividad_semanal(hoy=None, semanas=12)`** → lista de 12
  `{"inicio": date (lunes), "kardex": int}`, de la más antigua a la actual,
  con las semanas sin actividad en 0.
- **`ultimas_confrontaciones(limite=5)`** → hasta 5
  `{"expediente": Expediente, "usuario": str, "fecha": datetime}`, un kardex
  activo por fila, de la más reciente a la más antigua.
- **`avisos_documentos_ilegibles(usuario)`** → lista de `Expediente` activos
  con al menos un documento `ERROR` subido por `usuario`, ordenados por código.

## Reglas

- Un kardex archivado no cuenta en cifras, filas ni avisos. Sus corridas sí
  cuentan en la actividad semanal.
- La actividad cuenta **kardex distintos** por semana (lunes a domingo, hora de
  Lima).
- Los avisos dependen solo de `subido_por`, nunca de la visibilidad del rol.
