# Roadmap del ERP Notarial

El sistema se construye por **fases** (F1, F2…). Cada fase es una funcionalidad
pequeña que se termina completa antes de empezar la siguiente: pasa por el
ciclo de Spec Kit en su propio worktree de Orca y se integra a `main` por Pull
Request. Las reglas están en `.specify/memory/constitution.md`.

## Estado al 2026-10-12

Integrado en `main` hasta el [PR #88](https://github.com/Angello5/confrontador-notarial/pull/88)
(2026-10-09). F17 no existe: la numeración la saltó.

### Terminadas

| Fase | Resultado visible | Decisión que se tomó | PR | Spec |
|---|---|---|---|---|
| **F1** · Base DevSecOps | Cada PR corre tests, SonarQube y escaneos de seguridad; `main` protegida | SonarQube Cloud privado, análisis desde CI | #8, #14, #15 | 001 |
| **F2** · Esqueleto del ERP | Login, menú lateral según rol, AdminLTE 4 | Roles | #16 | 002 |
| **F3** · Migración del código actual | extraer, verificar, léxico y ortografía como núcleo puro con pytest; mismo resultado medido | — | #17 | 003 |
| **F4** · Expedientes | Subir archivos desde la PC, extracción en segundo plano, borrado del archivo al terminar | Retención del texto extraído: **indefinida**, con supresión a solicitud (constitución 1.6.0) | #20 | 004 |
| **F5** · Confrontación | Observaciones en pantalla, agrupadas por capa | Capas incluidas: regla y ortografía; el léxico se aplaza a F10 | #22 | 005 |
| **F6** · Historial y auditoría | Cubierta por F20: cada corrida guarda usuario, fecha y hashes; pantalla «Historial» por kardex | — | #51 | 014 |
| **F7** · Informe exportable | Cubierta por F29: informe Word de las observaciones | Formato Word (`.docx`), generado en el navegador | #61 | 023 |
| **F11** · Extracción por personas | El sistema deja de cruzar documentos entre comparecientes | Alcance: personas naturales; las jurídicas quedan fuera | #31 | 006 |
| **F12** · Persona ampliada | Estado civil, fecha de nacimiento y domicilio entran en la confrontación | Reglas de cónyuge, minoría de edad y domicilio | #40 | 007 |
| **F13** · Anclaje por ficha oficial | Cada ficha RENIEC o biométrica es una persona; el resto solo se adjunta | — | #42 | 008 |
| **F14** · Rediseño de interfaz | Todas las pantallas con la paleta y disposición del diseño de Figma | Sin IA, sin fuentes remotas, sin módulos futuros en el menú | #43 | 009 |
| **F15** · Una persona por DNI entre fichas | RENIEC y biométrica del mismo DNI son una sola persona; revisión solo si el nombre difiere mucho | Mismo DNI = misma persona, nombre RENIEC | #45 | 010 |
| **F16** · Nombres exigibles | Solo se exigen al borrador los nombres de fichas y minuta; el domicilio se busca también por DNI | Menciones y adjuntos reconocen, no exigen | #46, #73 | 011 |
| **F18** · Lectura de fichas RENIEC escaneadas | Fechas con ruido OCR, valores en la línea siguiente y fichas sin nombre legible aportan sus campos | Los datos de las personas salen de las fichas, también escaneadas | #48 | 012 |
| **F19** · Errores del borrador fuera de la comparecencia | DNI de longitud incorrecta, nombres mal escritos en cualquier cláusula y números en letras distintos de su cifra | Reconocimiento anclado a rótulo, a nombre de la fuente o a cifra entre paréntesis | #49 | 013 |
| **F20** · Manifiesto de auditoría | Cada confrontación deja una corrida inmutable y cada observación lleva severidad | Catálogo de reglas versionado con severidad ALTA, MEDIA o BAJA | #51 | 014 |
| **F21** · Capa de corrección y documento corregido | Correcciones propuestas con su fuente, una sola confirmación y descarga del `.docx` corregido; el original no cambia | Se conserva el borrador `.docx` (constitución 1.7.0) | #54 | 015 |
| **F22** · RUC y direcciones | Cada aparición del RUC y de la dirección en el borrador se compara con las fuentes | Reconocimiento anclado a rótulo, como el DNI de F19 | #53, #66, #67 | 016 |
| **F23** · Componente lingüístico local | Ortografía, tildes y redacción con un componente local | Sin autoridad sobre los datos obligatorios; sin modelos ni dependencias | #50 | 017 |
| **F24** · Montos exigibles | Solo se exigen al borrador los montos de la minuta | — | #52 | 018 |
| **F25** · Panel de expedientes | Abrir, editar y eliminar desde la lista | Eliminar es un archivado lógico | #55 | 019 |
| **F26** · Confrontación automática | La confrontación se hace al terminar la carga | No se repite si las entradas no cambian | #56 | 020 |
| **F27** · Montos por posición | Cada importe se compara con el de la misma posición en la minuta, con moneda y concepto | Las demás fuentes solo deciden cuando el importe no tiene par en la minuta | #57, #68, #76 | 021 |
| **F28** · Kardex reutilizable y notaría configurable | Un kardex archivado libera su código; el nombre de la notaría sale de la configuración | — | #58 | 022 |
| **F29** · Interfaz con la marca | Logo de la notaría, carga múltiple con estado, filtro por severidad e informe Word | — | #61 | 023 |
| **F30** · Reglas de la escritura | Área, números en letras, correlativos, copropiedad, importes por concepto y datos registrales | — | #61, #64, #72 | 024 |
| **F31** · Calidad de lectura OCR | Lectura dudosa distinguida de discrepancia, avisos persistentes y medición | La precisión jurídica real requiere etiquetas revisadas por la notaría | #61, #65 | 025 |
| **F33** · Rendimiento del OCR | Escaneos más rápidos con el mismo texto, páginas giradas con menos lecturas, hojas blancas sin OCR | Solo se saltan hojas con ≤ 0,001 % de píxeles oscuros | #63 | 027 |
| **F34** · Carga continua | Adjuntar sin interrupciones, confrontación solicitada reutilizable y visor simplificado | Sin cambiar reglas ni ampliar retención | #69 | 028 |
| **F35** · Empresa y partidas | Razón social y domicilio legal de la empresa contra su ficha RUC; más formatos de partida | Primera regla para personas jurídicas; la información del cliente está en los recaudos | #70 | 029 |
| **F36** · Interfaz con lenguaje notarial | «Kardex», «Confrontador Notarial», logo y letra mayores, lenguaje de abogado | Solo cambian textos y estilos | #71 | 030 |
| **F37** · Domicilio contractual | El domicilio «para efectos de este contrato» y el de la declaración jurada valen en la comparecencia | Omitir o cambiar el tipo de habilitación es aviso leve | #75 | 031 |
| **F38** · Lectura del borrador y persona sin ficha | Aviso «Sin ficha RENIEC en los recaudos» | Aviso MEDIA; el DNI siempre tiene 8 dígitos | #77, #78 | 032 |
| **F39** · Errores lingüísticos y anexo omitido | Acento grave, texto del `.docx` como se imprime, una alerta por anexo omitido | Se quita la regla de párrafos | #79 | 033 |
| **F40** · Correcciones con avance | Ventana con barra de avance y descarga directa del corregido | — | #80 | 034 |
| **F41** · Género y ordinales | Concordancia de género con la ficha RENIEC y números de cláusula mal escritos | — | #81 | 035 |
| **F42** · Generales de ley | Pestaña con nombres, documentos, estado civil, domicilio, género, RUC y razón social | — | #82 | 036 |
| **F43** · Transferencia vehicular | Submenú bajo «Kardex» que compara boleta informativa, DNI y cheques con el acta | Sin minuta; precio obligatorio en el acta; cheques por monto transferido | #85, #86 | 037 |
| **F44** · Submenú e informe vehicular | Submenú visible e informe Word sin minuta | — | #87 | 037 |
| **F45** · Ajustes vehiculares | Actas en tabla, vehículo a cuenta, propietario persona natural, RUC sin ficha y nombres con «PERUANO» | — | #88 | 037 |
| **F53** · Inicio del administrador | Cifras por tipo que suman el total, actividad por semana o por mes que se actualiza sola cada minuto, indicadores de calidad (gravedad, usuarias con más errores, errores frecuentes, correcciones), últimas confrontaciones y aviso de documento ilegible para quien lo subió | Sin «Pendientes de confrontar»; kardex distintos por periodo; errores atribuidos a quien creó el kardex; mismos archivos no suman dos veces | pendiente | 041 |

### En curso o pendientes

| Fase | Qué se construye | Resultado visible | Depende de | Decisión que se toma |
|---|---|---|---|---|
| **F32 · parcial (PR #69)** | Vista del borrador con errores resaltados | Hecho para `.docx`. Escaneados y demás formatos (T018–T024) pendientes | F21, F31 | Conservar el borrador en cualquier formato exige la constitución 1.8.0, redactada y pendiente de aprobación |
| **F8** | Despliegue | Funciona en el Windows Server, con respaldo diario | F5 | VM + Docker o nativo |
| **F9** | Catálogo por tipo de acto | Campos a verificar definidos por tipo (donación, mutuo…) | F5 | Tipos de acto iniciales. La transferencia vehicular (F43–F45) ya tiene flujo propio |
| **F10** | Capa de léxico | Erratas detectadas contra el corpus de escrituras firmadas | F5 | De dónde sale el corpus |

### Pendiente fuera de las fases

- **Mediciones privadas del revisor**, fuera del repositorio: 007 T027, 011 T007,
  016 T008, 018 T006 y 021 T006.
- **Criterio de MVP** (del README): medir cobertura sobre 10 expedientes cerrados.
- **Aclaraciones abiertas** (`[NEEDS CLARIFICATION]`): severidades, versión y
  orden de hallazgos en `specs/014-manifiesto-auditoria/spec.md`; FR-005 en
  `specs/015-capa-correccion/spec.md`; prioridad de procesamiento y progreso
  por página en `docs/ocr-tiempos-2026-10-02.md`.
- **Versión del ERP**: `ERP_VERSION` sigue en `0.20.0` desde F20 y
  `sonar-project.properties` no define `sonar.projectVersion`.

## Continuación autorizada · 2026-10-02

F31: calidad de lectura OCR, avisos persistentes y medición con casos ficticios y muestra privada. Alcance y tareas en `specs/025-calidad-ocr/`; evidencia en `docs/ocr-mejoras-2026-10-02.md`. La precisión jurídica real requiere etiquetas revisadas por la notaría. La integración mantiene los controles de CI y SonarQube establecidos.

## Continuación autorizada · 2026-10-03

F34 en curso: carga continua, solicitud de confrontación reutilizable, cola sin espera global y simplificación del visor con correcciones DOCX. Usuario autorizó implementar la propuesta tras el diagnóstico. Alcance en `specs/028-carga-continua/`; actualiza la interacción de F26 y F32 sin cambiar reglas ni ampliar retención. Despliegue y medición en servidores siguen en F8. Se integra por PR junto con la parte `.docx` de F32, de la que depende; la constitución 1.8.0 queda fuera y sigue pendiente de aprobación.

## Continuación autorizada · 2026-10-04

F35 en curso: empresa y partidas contra los recaudos. Tras la auditoría visual de los 10 expedientes de prueba, el usuario decidió que la información del cliente está en los recaudos y que la razón social y el domicilio legal de una empresa se corroboran contra su ficha RUC. Es la primera regla para personas jurídicas, que F11 dejó fuera de la extracción de personas. También amplía los formatos de partida y limita su FALTA a la minuta. Alcance y medición en `specs/029-empresa-ficha-ruc/`.

## Continuación autorizada · 2026-10-05

F36: interfaz con lenguaje notarial. El usuario pidió:

- «Kardex» en lugar de «Expedientes»;
- el subtítulo «Confrontador Notarial»;
- el nombre y el logo de la notaría más grandes;
- letra un poco mayor;
- lenguaje técnico de abogado (recaudos, Dice / Debe decir, confrontación, informe).

Solo cambian los textos y los estilos: las URL y los modelos siguen igual. Alcance y glosario en `specs/030-interfaz-notarial/`.

F37: domicilio contractual y tipo de habilitación. El usuario decidió que el domicilio que la minuta fija «para efectos de este contrato» y el de la declaración jurada son válidos en la comparecencia, y que omitir o cambiar el tipo de habilitación es un aviso leve. La declaración jurada manuscrita queda pendiente porque el OCR no la lee. Alcance en `specs/031-domicilio-contractual/`.

F38: lectura del borrador y persona sin ficha. El usuario decidió que, cuando la información del cliente no está en los recaudos, la app diga «Sin ficha RENIEC en los recaudos» como aviso MEDIA, y recordó que el DNI siempre tiene 8 dígitos. Alcance en `specs/032-lectura-borrador/`.

F39: errores lingüísticos y anexo omitido. El usuario pidió quitar la regla de párrafos y centrar la revisión en los errores lingüísticos. El anexo omitido sigue siendo un error, ahora como una sola alerta por anexo. El anexo insertado como recaudo (Recaudos.pdf) no cuenta como omitido. La capa lingüística detecta el acento grave y deja de reportar ruido, y el texto del .docx se lee como se imprime («Todo mayúsculas» de Word). El aviso de persona sin ficha muestra cómo escribe la minuta el nombre. Alcance en `specs/033-linguistico-tipeo/`.

F40: aplicar correcciones con avance y descarga directa. El usuario pidió que, al aplicar las correcciones, aparezca una ventana con una barra de avance del color de la interfaz y que al terminar el archivo ya esté descargado y se indique dónde quedó. Alcance en `specs/034-correcciones-progreso/`.

F41: concordancia de género con RENIEC y ordinales mal escritos. El usuario pidió revisar el género con el sexo de la ficha RENIEC y detectar los números de cláusula mal escritos. Alcance en `specs/035-genero-ordinales/`.

F42: pestaña «Generales de ley». El usuario pidió reunir en ella toda la información del cliente (nombres, documentos, estado civil, domicilio, género, RUC y razón social), que antes caía en «Datos». Alcance en `specs/036-generales-de-ley/`.

F43: transferencia vehicular. El usuario pidió un submenú «Transferencia vehicular» bajo «Kardex», sin minuta, que compare la boleta informativa, los DNI y los cheques con el acta. Alcance en `specs/037-transferencia-vehicular/`.

F44: «Transferencia vehicular» como submenú visible de «Kardex» y el informe Word sin minuta en las transferencias. Alcance en `specs/037-transferencia-vehicular/` (sección F44).

F45: ajustes de la transferencia vehicular con dos actas reales más: actas en tabla, vehículo entregado a cuenta, propietario persona natural, RUC sin ficha y nombres con «PERUANO». Alcance en `specs/037-transferencia-vehicular/` (sección F45).

## Continuación autorizada · 2026-10-18

F53: Inicio del administrador. Tras revisar la pantalla como notario, el usuario pidió que las cifras cuadren con el total, separar kardex y transferencias vehiculares, ver la actividad por semana y quién ejecutó cada confrontación, y quitar «Procesando», «Con error», «Requieren su atención» y «Control administrativo». Descartó la tarjeta «Pendientes de confrontar» porque la confrontación es automática (F26), y decidió contar kardex distintos por semana. Quien sube un documento ilegible recibe el aviso en su Inicio, sea cual sea su rol; el Inicio de las usuarias no cambia en lo demás. Alcance en `specs/041-inicio-administrador/`.

Ampliación del mismo día: ver la actividad por semana (12 semanas) o por mes (año en curso), actualización automática cada minuto con animaciones suaves, e indicadores de calidad: observaciones por gravedad, confrontaciones y errores por usuaria, errores más frecuentes y correcciones aplicadas. El usuario decidió atribuir los errores a quien creó el kardex («la que crea el kardex es la que debe confrontar») y que confrontar de nuevo con los mismos archivos no sume.

## Continuación autorizada · 2026-10-22

F61: capa de sentido (CR-01, Alternativa B). La notaría eligió el verificador semántico local del Informe de Evaluación v1.1, y el usuario pidió implementarlo completo. Pidió también que la concordancia de género y número la haga spaCy con análisis gramatical, y que el NLI funcione bien en el servidor. La constitución pasa a 2.0.0: la capa de sentido es la única con modelos, sin autoridad, local y con interruptor apagado por defecto. Quedan pendientes la instalación y medición en SQLSERVER (26/10), la revisión legal de la licencia de spaCy y la validación del umbral con la notaría. Alcance en `specs/043-capa-sentido/`.

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
