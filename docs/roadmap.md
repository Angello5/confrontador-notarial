# Roadmap del ERP Notarial

El sistema se construye por **fases** (F1, F2…). Cada fase es una funcionalidad
pequeña que se termina completa antes de empezar la siguiente: pasa por el
ciclo de Spec Kit en su propio worktree de Orca y se integra a `main` por Pull
Request. Las reglas están en `.specify/memory/constitution.md`.

| Fase | Qué se construye | Resultado visible | Depende de | Decisión que se toma |
|---|---|---|---|---|
| **F1 · terminada** | Base DevSecOps | Cada PR corre tests, SonarQube y escaneos de seguridad; `main` protegida | — | SonarQube Cloud privado, análisis desde CI |
| **F2 · terminada (PR #16)** | Esqueleto del ERP | Login, menú lateral según rol, AdminLTE 4 | F1 | Roles |
| **F3 · terminada (PR #17)** | Migración del código actual | extraer, verificar, léxico y ortografía como núcleo puro con pytest; mismo resultado medido; T028 depende del CI remoto | F1 | — |
| **F4 · en curso** | Expedientes | Subir archivos desde la PC, extracción en segundo plano, borrado del archivo al terminar | F2, F3 | Retención del texto extraído: **indefinida**, con supresión a solicitud (constitución 1.6.0) |
| **F5** | Confrontación | Observaciones en pantalla, agrupadas por capa | F4 | — |
| **F6** | Historial y auditoría | Quién confrontó qué, cuándo y con qué hash | F5 | — |
| **F7** | Informe exportable | Descargar o imprimir las observaciones | F5 | Formato |
| **F8** | Despliegue | Funciona en el Windows Server, con respaldo diario | F5 | VM + Docker o nativo |
| **F9** | Catálogo por tipo de acto | Campos a verificar definidos por tipo (donación, mutuo…) | F5 | Tipos de acto iniciales |

F1 terminó con el [PR #8](https://github.com/Angello5/confrontador-notarial/pull/8)
y el [PR #14](https://github.com/Angello5/confrontador-notarial/pull/14): Quality
Gate y protección de `main` verificados. F2 terminó con el
[PR #16](https://github.com/Angello5/confrontador-notarial/pull/16). F3 terminó con el
[PR #17](https://github.com/Angello5/confrontador-notarial/pull/17).

Criterio de MVP (del README): medir cobertura sobre 10 expedientes cerrados.

## Prompts de arranque para `/speckit-specify`

**F1 · Base DevSecOps**
> Cada Pull Request y cada push a main ejecutan automáticamente: lint con ruff
> (incluidas reglas de seguridad), tests con cobertura, análisis de SonarQube
> con Quality Gate, auditoría de dependencias (pip-audit) y búsqueda de secretos
> (gitleaks). Un PR no se puede mergear si algo falla. Antes del primer análisis
> se eliminan de los tests los DNI y apellidos reales, reemplazándolos por datos
> ficticios. También se configura pre-commit y Dependabot.

**F2 · Esqueleto del ERP**
> Los usuarios de la notaría inician sesión y ven un layout con menú lateral
> cuyas opciones dependen de su rol. Un administrador crea y desactiva usuarios
> y les asigna rol. Sin funcionalidad de negocio todavía.

**F3 · Migración del código actual**
> Convertir los módulos actuales (extraer, verificar, léxico, ortografía) en un
> núcleo de funciones puras, sin interfaz, conservando exactamente el resultado
> medido en el expediente de referencia. Los tests pasan a pytest. La capa de
> prosa se mueve a experimental/.

**F4 · Expedientes**
> Un usuario crea un expediente y sube desde su PC las fuentes (documentos del
> cliente, minuta) y el borrador. El servidor extrae el texto en segundo plano,
> muestra el avance y borra los archivos al terminar, conservando solo el hash
> de cada uno.

**F5 · Confrontación**
> Con el texto extraído, el sistema ejecuta las capas de regla, léxico y
> ortografía y muestra las observaciones agrupadas por capa, con la ubicación
> en el borrador y el valor esperado según la fuente.
