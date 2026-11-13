# Feature Specification: F75 · Agente de estudio de título

**Feature Branch**: `feat/f75-agente`

**Created**: 2026-11-04

**Status**: Draft (en desarrollo y prueba; apagado por defecto)

**Input**: User description: "Un módulo nuevo, «Agente», con un agente de IA para abogados, con system prompt y skills para abogados del Perú, que busque en internet y cite sus fuentes (RENIEC, SBS…). El 2026-11-10 el usuario aclaró el propósito: **no es consultar un kardex**, es hacer el **estudio de título**: revisar toda la información del cliente y decir qué falta. Por ahora usa la sesión de Claude o de Codex. Se ve en otro puerto."

## Origen

La notaría quiere que el abogado haga el estudio de título sin leer a mano todo lo reunido del cliente. No hay un archivo único: hay documentos sueltos (partidas, copias literales, DNI, certificados, etc.) y texto. El agente los revisa en conjunto y entrega una conclusión corta, lo que falta y los riesgos. La primera versión giraba en torno a un kardex (selector de expediente); se eliminó porque el estudio no parte de un kardex.

## Decisiones

- **Sin base de conocimiento propia.** El agente es la CLI del proveedor (`claude -p` o `codex exec`) con el system prompt de `agente/prompt/`. No hay API REST, SPA, colas ni caché (constitución V).
- **Skills = archivos `.md`** en `agente/prompt/`. Todos se unen al prompt; añadir una es soltar un archivo. Hoy: `sistema.md` (rol, brevedad, citas) y `fuentes_peru.md` (dónde buscar en RENIEC, SUNARP, SUNAT, SBS, El Peruano…). No existen «plugins» jurídicos peruanos que importar: las skills son nuestras.
- **Entrada: adjuntos y texto pegado, sin kardex.** El abogado adjunta hasta 8 archivos (PDF, Word, imágenes…, **≤ 10 MB** cada uno) y/o pega texto en el chat. Cada archivo se valida (`validar_archivo`: extensión, tamaño y firma), se escribe en un directorio temporal, se lee con el extractor del ERP (`extraccion.leer`, con OCR) y se borra siempre. El servidor devuelve el texto al navegador, que lo reenvía con cada pregunta: **el servidor no guarda ni archivos ni texto**.
- **Qué falta: lo deduce el agente.** Decisión del usuario (2026-11-10): sin lista fija de requisitos. El prompt solo guía qué revisar (titularidad, cargas, descripción del inmueble, identidad y estado civil, poderes, tributos, medios de pago) y exige citar documento y dato, y «No consta» cuando algo no está. Menos reproducible que una lista; si la notaría entrega su lista por tipo de acto, entra como skill nueva.
- **Documentos = datos, no instrucciones** (inyección de prompt): el prompt manda ignorar órdenes dentro de los adjuntos.
- **Respuesta breve:** pregunta puntual, máximo 80 palabras más hasta 3 URLs. Estudio de título: *Conclusión* (una frase), *Falta*, *Riesgos / observaciones* (máx. 5) y *Fuentes*.
- **Herramientas del agente:** solo `WebSearch` (sin `WebFetch`: un documento hostil no puede hacer que el agente abra una URL con datos del cliente). Sin shell, sin edición de archivos, sin MCP. Corre en un directorio vacío y con un entorno mínimo por lista de permitidos. La pregunta y los documentos van por stdin, nunca por argumentos.
- **Proveedor:** `claude` por defecto. `codex` está desactivado: no puede quitarse el shell y su sandbox `read-only` aún lee el disco; solo con `AGENTE_CODEX_PERMITIDO=1` y en un usuario del sistema sin acceso al ERP ni a sus claves (hallazgo de la revisión de seguridad).
- **Entorno del agente:** lista de permitidos (`PATH`, `HOME`…), no de bloqueo.
- **Interruptor:** `AGENTE_ACTIVO` apagado por defecto. Apagado, `/agente/` da 404 y el menú no lo muestra (como F61).
- **Auditoría:** `ConsultaAgente` guarda quién, cuántos adjuntos, proveedor, resultado y segundos. **Nunca** la pregunta, la respuesta ni los documentos.
- **Capacidad:** como máximo `AGENTE_SIMULTANEAS` (2) consultas a la vez; la tercera recibe «reintente» en vez de ocupar un hilo de waitress.

## Enmienda requerida a la constitución (pendiente de aprobación)

Este módulo contradice dos reglas vigentes, por eso **no debe activarse en el servidor de la notaría** hasta que el usuario y la notaría la aprueben:

1. Principio I: «El ERP NO usa modelos de lenguaje generativos ni servicios de IA externos».
2. Principio VI y IV: funciona sin internet y el texto extraído «no sale del servidor».

Texto propuesto (constitución 3.0.0, MAJOR porque redefine el principio I): *«El agente de consulta (F75) es la única capa que usa un servicio de IA generativa externo. Va apagado por defecto; sin autoridad sobre los datos del Anexo A.3 ni sobre los hallazgos; solo el texto que el abogado adjunta o pega; auditoría sin contenido; herramientas limitadas a búsqueda web; la notaría debe aceptar por escrito el envío de ese texto al proveedor (Ley 29733).»*

## [NEEDS CLARIFICATION]

- **Privacidad (Ley 29733):** el texto de los adjuntos sale hacia Anthropic u OpenAI. ¿La notaría lo acepta? ¿Se enmascaran DNI y domicilios antes de enviar? Mientras tanto, probar solo con documentos ficticios.
- **Suscripción personal:** `claude`/`codex` usan la sesión del usuario que los inició. Para producción con varios abogados hay que decidir entre cuentas de empresa o API con clave. Por ahora es solo para desarrollo y prueba.
- **Servidor Windows (F8):** la cuenta que corre IIS debe tener la CLI instalada y con sesión iniciada.
- **Lectura de escaneados:** el agente solo ve lo que el OCR extrajo; un OCR dudoso (F31) produce respuestas dudosas.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Estudio de título (Priority: P1)

El abogado adjunta los documentos del cliente, escribe «haz el estudio de título, compraventa de inmueble» y recibe una conclusión de una frase, la lista de lo que falta y hasta 5 riesgos con su fuente documental.

**Independent Test**: adjuntar una partida ficticia; la respuesta cita el documento y lista lo que no consta.

**Acceptance Scenarios**:

1. **Given** documentos adjuntos, **When** pide el estudio, **Then** la respuesta trae Conclusión, Falta y Riesgos, citando documento y dato.
2. **Given** un dato ausente, **When** se revisa, **Then** aparece en «Falta» y nunca se supone.
3. **Given** un adjunto con una orden dirigida al agente, **When** se analiza, **Then** la ignora y avisa.
4. **Given** un archivo de más de 10 MB o de formato/firma no válidos, **When** se adjunta, **Then** se rechaza con un mensaje claro.

### User Story 2 - Preguntar normativa con fuentes (Priority: P1)

Sin adjuntos, el abogado pregunta por un plazo o requisito. El agente busca en fuentes oficiales y termina con «Fuentes:» y hasta 3 URLs.

### Edge Cases

- La CLI no está instalada o la sesión venció: mensaje claro, sin detalle técnico ni contenido.
- Más de 120 s: se corta y se avisa.
- Más de `AGENTE_SIMULTANEAS` consultas: «El agente está atendiendo otras consultas».
- Contexto de más de `AGENTE_MAX_CONTEXTO` (120 000) caracteres: se recorta, **nunca en silencio**: la pantalla avisa al adjuntar y en la respuesta, el modelo recibe un «AVISO DEL SISTEMA» y debe declarar el estudio parcial en la Conclusión; los documentos que no caben quedan listados como recortados u omitidos.
- Archivo escaneado ilegible: «No se encontró texto legible».

## Requirements

- **FR-001**: Rutas `/agente/`, `/agente/adjuntar/` y `/agente/preguntar/`, con login y rol; 404 si `AGENTE_ACTIVO` está apagado.
- **FR-002**: Solo se envía al proveedor el texto de lo que el abogado adjuntó o pegó; los adjuntos son ≤ 10 MB, máximo 8, validados por contenido y no se guardan.
- **FR-003**: El agente solo puede usar `WebSearch`.
- **FR-004**: Respuestas de hasta 80 palabras más fuentes, impuestas por el system prompt.
- **FR-005**: La auditoría no guarda pregunta ni respuesta.
- **FR-005b**: Si los adjuntos superan el límite de contexto, el abogado y el modelo son avisados con los nombres de los documentos afectados.
- **FR-006**: El entorno del agente solo incluye variables de una lista de permitidos.

## Success Criteria

- **SC-001**: Una pregunta típica se responde en menos de 30 s (medido: ~20–25 s con `claude` y con `codex`).
- **SC-002**: Toda respuesta normativa trae al menos una URL.
