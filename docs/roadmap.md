# Roadmap del ERP Notarial

Cada funcionalidad pasa por el ciclo completo de Spec Kit en su propio worktree
de Orca y se integra a `main` por Pull Request. Reglas en
`.specify/memory/constitution.md`.

| # | Funcionalidad | Depende de | Decisión que se toma aquí |
|---|---|---|---|
| F0 | Esqueleto Django, login, roles, layout AdminLTE 4 | — | Roles concretos |
| F1 | Migración del núcleo existente a funciones puras con pytest | — | — |
| F2 | Expediente: subida de archivos, worker, extracción temporal | F0, F1 | Retención del texto extraído |
| F3 | Confrontación e informe en pantalla | F2 | — |
| F4 | Historial y auditoría | F3 | — |
| F5 | Informe exportable | F3 | Formato (PDF / impresión) |
| F6 | Despliegue en el Windows Server | F3 | VM + Docker o nativo |
| F7 | Catálogo declarativo de campos por tipo de acto | F3 | Tipos de acto iniciales |

F0 y F1 pueden avanzar en paralelo (worktrees distintos).

Criterio de MVP (del README): medir cobertura sobre 10 expedientes cerrados.

## Prompts de arranque para `/speckit-specify`

**F0**
> Esqueleto del ERP: los usuarios de la notaría inician sesión y ven un layout
> con menú lateral cuyas opciones dependen de su rol. Un administrador crea,
> desactiva usuarios y les asigna rol. Sin funcionalidad de negocio todavía.

**F1**
> Convertir los módulos actuales (extraer, verificar, léxico, ortografía) en un
> núcleo de funciones puras, sin interfaz, conservando exactamente el resultado
> medido en el expediente de referencia. Los tests pasan a pytest y usan solo
> datos ficticios; se eliminan de las aserciones los DNI y apellidos reales. La
> capa de prosa se mueve a experimental/.

**F2**
> Un usuario crea un expediente y sube desde su PC las fuentes (documentos del
> cliente, minuta) y el borrador. El servidor extrae el texto en segundo plano,
> muestra el avance y borra los archivos al terminar, conservando solo el hash
> de cada uno.

**F3**
> Con el texto extraído, el sistema ejecuta las capas de regla, léxico y
> ortografía y muestra las observaciones agrupadas por capa, con la ubicación
> en el borrador y el valor esperado según la fuente.
