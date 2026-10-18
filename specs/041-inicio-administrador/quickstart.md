# Quickstart: validar F53

Prerrequisitos: entorno de `specs/001-base-devsecops/quickstart.md` y
PostgreSQL local. Solo datos ficticios.

## Pruebas automáticas

```bash
python -m pytest tests/test_inicio.py tests/test_shell.py
python -m ruff check .
python -m ruff format --check .
```

Esperado: en verde. `tests/test_inicio.py` cubre:

- las cifras por tipo suman el total y excluyen archivados (FR-001);
- elementos retirados ausentes en el Inicio del administrador (FR-002);
- enlaces de cada tipo a su lista (FR-003);
- 12 semanas, con las vacías en 0 y un kardex confrontado tres veces en una
  semana contando 1 (FR-004);
- últimas confrontaciones: un kardex por fila, usuaria y orden (FR-005);
- avisos: solo para quien subió el documento, sin límite de antigüedad, sin
  nombre de archivo, y desaparecen al archivar (FR-007 a FR-010);
- el Inicio del Usuario conserva sus métricas y «Nueva confrontación» (FR-011).

## Revisión manual

1. Levantar el ERP local (ver memoria «ERP local en Windows»).
2. Entrar como administrador: comprobar las cifras, el gráfico y la lista
   contra la lista de kardex y la de transferencias.
3. Entrar como usuaria, subir un archivo ilegible ficticio, salir del kardex y
   abrir Inicio: debe verse el aviso. Como administrador no debe verse.
4. Revisar la pantalla contra las 10 heurísticas (`/speckit-checklist`) y a
   ancho de móvil.
