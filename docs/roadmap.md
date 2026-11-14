# Roadmap del ERP Notarial

El sistema se construye por **fases** (F1, F2…). Cada fase es una funcionalidad
pequeña que se termina completa antes de empezar la siguiente: pasa por el
ciclo de Spec Kit en su propio worktree de Orca y se integra a `main` por Pull
Request. Las reglas están en `.specify/memory/constitution.md`.

## Estado al 2026-11-14

Integrado en `main` hasta F74 (F66–F74 en el PR #136) y los ajustes
posteriores (#137–#142). F17 no existe: la numeración la saltó. F72 está
reservada para el flujo entre dos personas.

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
| **F46** · Administración con la marca | El admin de cuentas con colores, sello y nombre de la notaría; «Cuentas» en español | Cabecera blanca con línea verde, también en modo oscuro | #95 | 038 |
| **F47** · Menú «Expedientes» | «Expedientes» agrupa «Kardex» y «Transferencia vehicular» en la barra lateral | «Expedientes» es solo rótulo de grupo; matiza a F36 únicamente en el menú | #94 | 039 |
| **F48** · Total de errores al corregir | Sin «Revisión N» en la cabecera; la ventana de correcciones muestra el total de observaciones y bloquea las no corregibles | No cambia qué es corregible (F21); el número de corrida sigue en el informe | #96 | 040 |
| **F49** · Administración interactiva | Fondo blanco, recuadros de cuentas, filas y acciones con respuesta visual, foco visible | Sin JavaScript ni dependencias; revisión de diseño y accesibilidad WCAG AA | #98 | 038 |
| **F50** · Texto leído con versiones anteriores | El borrador `.docx` se relee solo; aviso para volver a subir los demás documentos; reextraer y suprimir con códigos repetidos | Se releen los borradores; minuta y recaudos se vuelven a subir; la supresión actúa solo sobre el kardex activo | #99 | 033 |
| **F51** · Persona sin ficha | Un solo aviso «Persona sin ficha» por persona; rótulos legibles en lugar de códigos | Sin ficha en los recaudos basta el aviso MEDIA, sin la ALTA de documento | #100 | 032 |
| **F52** · Visor: ubicación y recuadros | Las observaciones de persona se marcan sobre el nombre en su línea; recuadros con el ancho real de cada carácter | — | #101 | 026 |
| **F53** · Inicio del administrador | Cifras por tipo que suman el total, actividad por semana o por mes que se actualiza sola cada minuto, indicadores de calidad (gravedad, usuarias con más errores, errores frecuentes, correcciones), últimas confrontaciones y aviso de documento ilegible para quien lo subió | Sin «Pendientes de confrontar»; kardex distintos por periodo; errores atribuidos a quien creó el kardex; mismos archivos no suman dos veces | #105 | 041 |
| **F54** · Ingreso con la marca | Pantalla de ingreso con la marca más grande y la banda completa | — | #109 | 042 |
| **F55** · «TV» en lugar de «kardex» | «Transferencia vehicular» / «TV» en los textos de ese flujo | — | #107 | 037 |
| **F56** · Observaciones con el dato a la vista | El dato a la vista y una sola pestaña «Todas» | — | #108 | 040 |
| **F57** · Ranking por digitadora | Ranking de errores por digitadora y versión imprimible | — | #110 | 041 |
| **F58** · Signo sin cerrar y domicilio OCR | Aviso comprensible de signo sin cerrar y de anexo que no se puede comprobar; domicilio leído por OCR con puntuación alterada | — | #114 (domicilio) | 033, 031 |
| **F59** · Total y hora en la lista | Total de errores y hora real de actualización en la lista | — | #113 | 019 |
| **F60** · Avisos legibles | Los avisos se entienden sin interpretar «Dice / Debe decir» | — | #115 | 040 |
| **F61** · Capa de sentido | «Sentido frente a la minuta», con modelos locales no generativos, sin autoridad y apagada por defecto | Alternativa B del Informe de Evaluación v1.1 (constitución 2.0.0) | #117 | 043 |
| **F62** · Cookies propias | Cada clic ya no lleva al login por la cookie de otra app Django | — | #118 | 044 |
| **F63** · SQL Server (revertida) | La base del ERP pasó a SQL Server | Revertida a PostgreSQL 17 por el PR #126 (2026-11-03); constitución 2.3.0 | #122 | 045 |
| **F64** · Sugerencias en cifras y cuotas | Los avisos de cifra y letras, área y cuotas dicen lo hallado y la sugerencia | Suma de cuotas en todos los actos que reparten; todo por código | #130 | 047 |
| **F65** · Lista compacta | Resultado sin panel de detalle; cada fila muestra lo hallado y lo correcto | Solo presentación | #131 | 048 |
| **F66** · Letras mal escritas | «TREINTA Y SEI (36)» se puede corregir si las letras reparadas valen lo mismo que la cifra | Si valen distinto, decide el abogado | #136 | 049 |
| **F67** · Icono de la pestaña | Isotipo «E» en la pestaña del navegador | La imagen no se versiona; `ERP_ICONO` | #136 | 050 |
| **F68** · Avisos de lectura compactos | «Lectura que necesita revisión» en una línea desplegable | El informe impreso la conserva completa | #136 | 051 |
| **F69** · Sentido sin falsas alarmas | Búsqueda contra el documento completo; la pantalla muestra solo lo que cambia | Sección aparte; sin enmienda a la constitución | #136 | 052 |
| **F70** · Menú de iconos en la confrontación | Panel izquierdo reducido en esa pantalla | Se abre con el puntero o el teclado | #136 | 053 |
| **F71** · Lista sin fragmento y pruebas aisladas | Sin fragmento bajo cada observación; las pruebas usan carpetas propias | El informe impreso conserva el fragmento | #136 | 054 |
| **F73** · Rediseño de cuatro pantallas | Filtros en el Inicio, siguiente paso en el kardex, modal con vista previa del informe, detalle desplegado | Elegido en Claude Design | #136 | 055 |
| **F74** · DNI del cónyuge y registro de otra entidad | Un registro de personas ya no se observa frente a uno de bienes; el nombre tras «CASADO CON» no toma el DNI | — | #136 | 056 |

### En curso o pendientes

| Fase | Qué se construye | Resultado visible | Depende de | Decisión que se toma |
|---|---|---|---|---|
| **F32 · parcial (PR #69)** | Vista del borrador con errores resaltados | Hecho para `.docx`. Escaneados y demás formatos (T018–T024) pendientes | F21, F31 | Conservar el borrador en cualquier formato exige la constitución 1.8.0, redactada y pendiente de aprobación |
| **F8** | Despliegue | Funciona en el Windows Server, con respaldo diario. En curso: constitución 2.2.0, spec, plan y tareas integrados (#124); 1 de 29 tareas hechas (`specs/046-despliegue/`) | F5 | Resuelta: nativo en Windows con IIS + waitress y PostgreSQL 17 (constitución 2.3.0) |
| **F9** | Catálogo por tipo de acto | Campos a verificar definidos por tipo (donación, mutuo…) | F5 | Tipos de acto iniciales. La transferencia vehicular (F43–F45) ya tiene flujo propio |
| **F10** | Capa de léxico | Erratas detectadas contra el corpus de escrituras firmadas | F5 | De dónde sale el corpus |

### Pendiente fuera de las fases

- **Mediciones privadas del revisor**, fuera del repositorio: 007 T027, 011 T007,
  016 T008, 018 T006 y 021 T006.
- **Criterio de MVP** (del README): medir cobertura sobre 10 expedientes cerrados.
- **Aclaraciones abiertas** (`[NEEDS CLARIFICATION]`): severidades, versión y
  orden de hallazgos en `specs/014-manifiesto-auditoria/spec.md`; FR-005 en
  `specs/015-capa-correccion/spec.md`; prioridad de procesamiento y progreso
  por página en `docs/ocr-tiempos-2026-10-02.md`; qué cuenta como total en
  `specs/040-resumen-errores/spec.md`; supresión de un kardex solo archivado o
  con el código repetido entre kardex y transferencia vehicular en
  `specs/033-linguistico-tipeo/spec.md`.
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

## Continuación autorizada · 2026-10-16

F46–F49: el usuario pidió el admin con la marca, «Expedientes» como submenú con «Kardex» y «Transferencia vehicular», quitar «Revisión N» de la cabecera del resultado con el total de errores al corregir y las no corregibles bloqueadas, y luego el admin con fondo blanco y más interactivo usando las skills de diseño. Se hicieron en paralelo, cada una en su worktree y PR.

F50–F52: a partir del kardex privado 72193. Las «mayúsculas mezcladas» venían de texto leído antes de F39; el usuario decidió releer los borradores `.docx` (únicos archivos conservados por la constitución), avisar para volver a subir la minuta y los recaudos, y que la supresión (Ley 29733) actúe solo sobre el kardex activo. Para una persona sin ficha basta el aviso MEDIA. El visor ubica las observaciones de persona y ajusta el ancho de los recuadros.

Además, los enlaces a CSS y JS llevan versión (`?v=`, PR #97) para que el navegador no use hojas viejas tras actualizar. En SonarCloud se activó la regla `css:S9423` («!important»): se reanalizó `main` para que las líneas existentes no cuenten como nuevas.

## Continuación autorizada · 2026-10-18

F53: Inicio del administrador. Tras revisar la pantalla como notario, el usuario pidió que las cifras cuadren con el total, separar kardex y transferencias vehiculares, ver la actividad por semana y quién ejecutó cada confrontación, y quitar «Procesando», «Con error», «Requieren su atención» y «Control administrativo». Descartó la tarjeta «Pendientes de confrontar» porque la confrontación es automática (F26), y decidió contar kardex distintos por semana. Quien sube un documento ilegible recibe el aviso en su Inicio, sea cual sea su rol; el Inicio de las usuarias no cambia en lo demás. Alcance en `specs/041-inicio-administrador/`.

Ampliación del mismo día: ver la actividad por semana (12 semanas) o por mes (año en curso), actualización automática cada minuto con animaciones suaves, e indicadores de calidad: observaciones por gravedad, confrontaciones y errores por usuaria, errores más frecuentes y correcciones aplicadas. El usuario decidió atribuir los errores a quien creó el kardex («la que crea el kardex es la que debe confrontar») y que confrontar de nuevo con los mismos archivos no sume.

## Continuación autorizada · 2026-10-22

F61: capa de sentido (CR-01, Alternativa B). La notaría eligió el verificador semántico local del Informe de Evaluación v1.1, y el usuario pidió implementarlo completo. Pidió también que la concordancia de género y número la haga spaCy con análisis gramatical, y que el NLI funcione bien en el servidor. La constitución pasa a 2.0.0: la capa de sentido es la única con modelos, sin autoridad, local y con interruptor apagado por defecto. Quedan pendientes la instalación y medición en SQLSERVER (26/10), la revisión legal de la licencia de spaCy y la validación del umbral con la notaría. Alcance en `specs/043-capa-sentido/`.

F62: cookies propias del ERP. El usuario reportó que cada clic lo mandaba al login: otra app Django en el mismo host borraba la cookie `sessionid`. Alcance en `specs/044-cookies-propias/`.

## Continuación autorizada · 2026-10-24

**Revertida el 2026-11-03 (PR #126):** la base volvió a PostgreSQL 17 y el despliegue pasó a IIS con waitress; el usuario lo confirmó el 2026-11-14 y la constitución pasa a 2.3.0. Lo que sigue es el registro histórico de F63.

F63: base de datos en SQL Server. La notaría exige que la base del ERP esté en SQL Server 2016, el motor de su servidor SQLSERVER. El usuario confirmó que el ERP se conecta con un login propio de SQL Server. La edición se confirma en la instalación (se asume Standard). La constitución pasa a 2.1.0. No hay datos que trasladar: el despliegue es F8. Aviso a la notaría: SQL Server 2016 está fuera de soporte extendido desde el 14/07/2026 y solo recibe parches con ESU de pago. Alcance en `specs/045-sql-server/`.

## Continuación autorizada · 2026-10-30

F64: sugerencias en cifras y cuotas. El usuario pidió que los avisos de cifra y letras, área y cuotas digan, resumido y en lenguaje sencillo, lo que encontraron en la minuta y la sugerencia concreta. Decidió que la suma de cuotas se revise en todos los actos que reparten entre personas (copropiedad, aportes, herencias y otros), sin intereses, moras ni tasas, y que el aviso no elija cuando la minuta no trae el dato. Todo por código, sin modelos. Alcance en `specs/047-sugerencias-cifras/`.

F65: lista de observaciones compacta. El usuario pidió quitar el panel de detalle de la pantalla de resultado, porque repite lo que dice la lista, y que cada fila muestre en pequeño lo hallado y lo correcto. Sumó cuatro mejoras de la revisión de interfaz: la sugerencia en su propia línea, resaltar solo lo que cambia, contadores de severidad sin cortes y un sello de reemplazo si el logo no carga. Solo presentación. Alcance en `specs/048-lista-compacta/`.

## Continuación autorizada · 2026-11-02

F66: letras mal escritas en la corrección automática. El usuario pidió poder corregir «TREINTA Y SEI (36)», que salía bloqueada. Solo entra cuando las letras reparadas valen lo mismo que la cifra; si valen distinto sigue decidiendo el abogado. Sube el catálogo para recalcular las confrontaciones guardadas. Alcance en `specs/049-correccion-letras/`.

F67: icono de la notaría en la pestaña del navegador, con el isotipo «E» de la guía de marca. La imagen no se versiona, como el logo; se configura con `ERP_ICONO`. Alcance en `specs/050-icono-pestana/`.

F68: avisos de lectura compactos. El usuario pidió reducir «Lectura que necesita revisión» en el resultado. Pasa a una línea desplegable, igual que el de versión anterior, también en el kardex; el informe impreso conserva completo el de lectura. Alcance en `specs/051-avisos-lectura-compactos/`.

F69: sentido sin falsas alarmas. El usuario vio anotaciones por oraciones cortadas y pidió otro enfoque, sin falsas alarmas y digerible. La búsqueda contra el documento completo ignora puntuación, cifras y letras sueltas, sin perder palabras reales, y la pantalla muestra solo lo que cambia. Mantuvo la sección aparte: no se enmienda la constitución. Alcance en `specs/052-sentido-sin-falsas-alarmas/`.

F70: menú de iconos en la confrontación. El usuario pidió que el panel izquierdo se achique en esa pantalla, para dar espacio al documento. Se abre sobre el contenido con el puntero o el teclado. Alcance en `specs/053-menu-iconos-confrontacion/`.

F71: lista sin fragmento y pruebas aisladas. El usuario pidió quitar el fragmento bajo cada observación; el informe impreso lo conserva. Las pruebas pasan a usar carpetas propias, porque en un equipo con datos borraban originales reales. Alcance en `specs/054-lista-sin-fragmento/`.

F73: rediseño de cuatro pantallas. El usuario eligió en Claude Design: barra de filtros en el Inicio (periodo y persona), columna con el siguiente paso en el kardex, modal amplio con vista previa del informe y detalle desplegado en la lista del resultado. F72 queda reservada para el flujo entre dos personas. Alcance en `specs/055-rediseno-pantallas/`.

F74: DNI del cónyuge y registro de otra entidad. Los usuarios, al validar con casos reales, reportaron que el sistema cambiaba «Registro de Personas Jurídicas» por el registro del bien y que asignaba a la esposa el DNI del esposo en la fórmula «CASADO CON». Un registro de personas ya no se observa frente a uno de bienes, y el nombre tras «CASADO CON» nunca se queda con el DNI. Alcance en `specs/056-conyuge-y-registro/`.

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
