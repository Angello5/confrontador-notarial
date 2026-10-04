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
| **F4 · terminada (PR #20)** | Expedientes | Subir archivos desde la PC, extracción en segundo plano, borrado del archivo al terminar | F2, F3 | Retención del texto extraído: **indefinida**, con supresión a solicitud (constitución 1.6.0) |
| **F5 · terminada (PR #22)** | Confrontación | Observaciones en pantalla, agrupadas por capa | F4 | Capas incluidas: regla y ortografía; el léxico se aplaza |
| **F11 · terminada (PR #31)** | Extracción por personas | El sistema deja de cruzar documentos entre comparecientes | F5 | Alcance: personas naturales; las jurídicas quedan fuera |
| **F12 · terminada (PR #40)** | Persona ampliada | Estado civil, fecha de nacimiento y domicilio entran en la confrontación | F11 | Reglas de cónyuge, minoría de edad y domicilio |
| **F13 · terminada (PR #42)** | Anclaje por ficha oficial | Cada ficha RENIEC o biométrica es una persona; el resto solo se adjunta | F12 | — |
| **F14 · terminada (PR #43)** | Rediseño de interfaz | Todas las pantallas con la paleta y disposición del diseño de Figma | F13 | Sin IA, sin fuentes remotas, sin módulos futuros en el menú |
| **F15 · terminada (PR #45)** | Una persona por DNI entre fichas | RENIEC y biométrica del mismo DNI son una sola persona; revisión solo si el nombre difiere mucho | F13 | Mismo DNI = misma persona, nombre RENIEC |
| **F16 · en curso** | Nombres exigibles | Solo se exigen al borrador los nombres de fichas y minuta; el domicilio se busca también por DNI | F15 | Menciones y adjuntos reconocen, no exigen |
| **F18 · en curso** | Lectura de fichas RENIEC escaneadas | Fechas con ruido OCR, valores en la línea siguiente y fichas sin nombre legible aportan sus campos | F15 | Los datos de las personas salen de las fichas, también escaneadas |
| **F19 · en curso** | Errores del borrador fuera de la comparecencia | DNI de longitud incorrecta, nombres mal escritos en cualquier cláusula y números en letras distintos de su cifra | F16 | Reconocimiento anclado a rótulo, a nombre de la fuente o a cifra entre paréntesis |
| **F21 · en curso** | Capa de corrección y documento corregido | Correcciones propuestas con su fuente, una sola confirmación y descarga del `.docx` corregido; el original no cambia | F19 | Se conserva el borrador `.docx` (constitución 1.7.0) |
| **F32 · en curso** | Vista del borrador con errores resaltados | La página del borrador en pantalla con cada observación marcada en su sitio: alta en rojo, media en amarillo, baja en tono neutro. Hecho para `.docx`; escaneados pendientes | F21, F31 | Conservar el borrador en cualquier formato exige la constitución 1.8.0 (redactada aparte, pendiente de aprobación); spec en `specs/026-vista-borrador-resaltada/` |
| **F33 · en curso** | Rendimiento del OCR | Escaneos leídos más rápido con el mismo texto, páginas giradas con menos lecturas y en orden, hojas totalmente blancas sin OCR y conversión de `.doc`/`.rtf` sin preparar LibreOffice cada vez | F31 | Solo se saltan hojas con ≤ 0,001 % de píxeles oscuros; spec en `specs/027-rendimiento-ocr/` |
| **F10** | Capa de léxico | Erratas detectadas contra el corpus de escrituras firmadas | F5 | De dónde sale el corpus |
| **F6** | Historial y auditoría | Quién confrontó qué, cuándo y con qué hash | F5 | — |
| **F7** | Informe exportable | Descargar o imprimir las observaciones | F5 | Formato |
| **F8** | Despliegue | Funciona en el Windows Server, con respaldo diario | F5 | VM + Docker o nativo |
| **F9** | Catálogo por tipo de acto | Campos a verificar definidos por tipo (donación, mutuo…) | F5 | Tipos de acto iniciales |

F1 terminó con el [PR #8](https://github.com/Angello5/confrontador-notarial/pull/8)
y el [PR #14](https://github.com/Angello5/confrontador-notarial/pull/14): Quality
Gate y protección de `main` verificados. F2 terminó con el
[PR #16](https://github.com/Angello5/confrontador-notarial/pull/16). F3 terminó con el
[PR #17](https://github.com/Angello5/confrontador-notarial/pull/17). F4 terminó con el
[PR #20](https://github.com/Angello5/confrontador-notarial/pull/20), que enmendó la
constitución a 1.6.0. F5 deja fuera la capa de léxico: necesita un corpus de
escrituras firmadas y todavía no está decidido de dónde sale, así que pasa a ser
la fase F10.

Criterio de MVP (del README): medir cobertura sobre 10 expedientes cerrados.

## Continuación autorizada · 2026-10-02

F31: calidad de lectura OCR, avisos persistentes y medición con casos ficticios y muestra privada. Alcance y tareas en `specs/025-calidad-ocr/`; evidencia en `docs/ocr-mejoras-2026-10-02.md`. La precisión jurídica real requiere etiquetas revisadas por la notaría. La integración mantiene los controles de CI y SonarQube establecidos.

## Continuación autorizada · 2026-10-03

F34 en curso: carga continua, solicitud de confrontación reutilizable, cola sin espera global y simplificación del visor con correcciones DOCX. Usuario autorizó implementar la propuesta tras el diagnóstico. Alcance en `specs/028-carga-continua/`; actualiza la interacción de F26 y F32 sin cambiar reglas ni ampliar retención. Despliegue y medición en servidores siguen en F8. Se integra por PR junto con la parte `.docx` de F32, de la que depende; la constitución 1.8.0 queda fuera y sigue pendiente de aprobación.

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
