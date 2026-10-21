<!--
Sync Impact Report
- Version: 1.3.0 → 1.4.0 (MINOR: se adopta el gate disponible en el plan
  gratuito y se documenta su límite de cobertura)
- Principios modificados: VII. DevSecOps (Quality Gate "Sonar way" y
  excepción nativa para cambios de menos de 20 líneas nuevas)
- Motivo: el plan gratuito de SonarQube Cloud no permite gates personalizados;
  se acepta su tolerancia de cambios pequeños y se revisará si cambia el plan
- Historial: 1.3.0 resolvió TODO(SONAR) y autorizó el arranque excepcional de
  F1; 1.2.0 añadió VIII Usabilidad; 1.1.0 añadió VII DevSecOps; 1.0.0
  ratificación inicial
- Plantillas: plan-template.md lee la constitución en "Constitution Check" (sin cambios necesarios)
- Version: 1.4.0 → 1.5.0 (MINOR: se resuelve TODO(ROLES) con dos roles y
  administración de cuentas mediante Django admin)
- Principios modificados: VI. Seguridad y control de acceso (roles concretos,
  administración vía Django admin y salvaguardas de administradores)
- Motivo: F2 requiere definir dos roles y el uso del Django admin nativo para
  administrar cuentas, además de crear el primer Administrador en el servidor
- Fecha: 2026-09-18
- Version: 1.5.0 → 1.6.0 (MINOR: se resuelve TODO(RETENCION_TEXTO) conservando
  el texto extraído de forma indefinida, con supresión a solicitud)
- Principios modificados: IV. Privacidad de datos personales (persistencia del
  texto extraído y comando de supresión)
- Motivo: F4 necesita reutilizar el texto ya extraído para no repetir el OCR al
  reabrir un expediente; el despliegue es on-premise, en la LAN de la notaría y
  sin exposición a internet
- Fecha: 2026-09-20
- Version: 1.6.0 → 1.7.0 (MINOR: se añade la conservación del borrador
  `.docx` como original inalterable)
- Principios modificados: IV. Privacidad de datos personales (excepción a los
  archivos temporales para el borrador `.docx`)
- Motivo: Anexo A.3 del contrato (F21): conservar el documento original en
  versión inalterable y generar el corregido como archivo distinto
- Fecha: 2026-09-28
- Version: 1.7.0 → 1.7.1 (PATCH: se cumple lo previsto para la prueba de
  concepto Streamlit y se elimina)
- Principios modificados: ninguno (sección de stack)
- Motivo: pillow 13 corrige 8 vulnerabilidades en la lectura de imágenes y
  Streamlit exige `pillow<13`; el usuario declaró que el ERP ya supera la
  prueba de concepto
- Fecha: 2026-10-20
- TODO pendientes:
  - TODO(DESPLIEGUE): VM Ubuntu + Docker vs nativo Windows. Decidir en F8.
-->

# Constitución del ERP Notarial (Confrontador)

Sistema interno on-premise para una notaría en Perú (~100 personas, máximo 10
usuarios del sistema). Primer flujo: confrontar el proyecto de escritura contra
la minuta y los documentos del cliente, y señalar las diferencias.

## Principios fundamentales

### I. Determinismo y reproducibilidad (NO NEGOCIABLE)

- Los datos con una única respuesta correcta (DNI, partida registral, montos,
  nombres) se deciden por código, por igualdad exacta contra la fuente.
- La misma entrada DEBE producir siempre la misma salida. Un cambio que rompa
  esto es un defecto, no una mejora.
- El ERP NO usa modelos de lenguaje ni servicios de IA. La capa de prosa
  existente (`revisor_llm.py`, `bench_llm.py`) vive en `experimental/`: el ERP
  no la importa, no la despliega y sus dependencias no entran en el ERP.
- Capas permitidas: **regla** (datos duros), **léxico** (corpus de escrituras
  firmadas), **ortografía** (hunspell `es_PE` + lista de la casa).

### II. Núcleo de dominio puro

- La lógica de negocio (extracción de campos, verificación, léxico, ortografía)
  vive en módulos de funciones puras que NO importan Django, la base de datos,
  el OCR ni el sistema de archivos. Reciben texto o estructuras y devuelven
  resultados.
- La extracción de texto (OCR, docx, pdf…) es un adaptador: entrega texto al
  núcleo y nada más.
- Las vistas son delgadas: validan la entrada, llaman a `services.py` y
  renderizan. Las tareas del worker orquestan (extraer → núcleo → guardar →
  borrar) y no deciden nada del negocio.
- Al migrar el código existente, DEBE preservarse el comportamiento medido
  (expediente de referencia: 8 de 8 errores, 0 falsos positivos, salida
  idéntica en corridas repetidas).

### III. Pruebas primero en el núcleo (NO NEGOCIABLE)

- Toda regla nueva y todo bug del núcleo empieza con un test que falla.
- Los tests del repositorio usan SOLO datos ficticios. Nunca DNI, nombres ni
  fragmentos de escrituras reales.
- La cobertura real se mide contra expedientes de referencia que viven fuera
  del repositorio; un cambio en el núcleo no se mergea si empeora esa medición.
- Las pruebas de integración cubren: subida de archivos, permisos por rol,
  procesamiento en el worker y borrado de archivos temporales.

### IV. Privacidad de datos personales

- Los expedientes contienen datos personales (Ley 29733). Nunca se versionan.
- Los archivos subidos son TEMPORALES: existen solo mientras se procesan, se
  borran en un bloque `finally` y una tarea diaria elimina huérfanos con más de
  24 h. El directorio temporal no se respalda.
- Persistencia mínima: resultados (observaciones), hash SHA-256 de cada archivo,
  quién, cuándo y estado. Nunca el archivo original, salvo la excepción
  siguiente.
- Borrador `.docx` (Anexo A.3 del contrato): se conserva como original
  inalterable, junto con los documentos corregidos generados a partir de él.
  Condiciones:
  - Solo el borrador `.docx`; los documentos del cliente y la minuta siguen
    siendo temporales.
  - Almacenamiento local fuera del repositorio y de `static/`, con permisos
    restrictivos; la ruta nunca se muestra ni se registra y la descarga pasa por
    una vista con permisos.
  - El original no se modifica: su SHA-256 se verifica antes de generar un
    corregido, que siempre es un archivo distinto.
  - La supresión a solicitud (y la eliminación del documento) borra también el
    original y los corregidos.
- Texto extraído: SE PERSISTE de forma indefinida, indexado por el hash SHA-256
  del archivo y la versión del extractor, para no repetir el OCR. Es una caché
  de resultados, no un archivo documental: solo texto, nunca el archivo
  original. Condiciones:
  - La llave DEBE incluir la versión del extractor; un cambio de modelo de OCR
    o de la extracción invalida las entradas anteriores por construcción.
  - DEBE existir un comando de administración que borre el texto de un
    expediente concreto (derecho de supresión, Ley 29733).
  - El texto no sale del servidor ni aparece en logs, mensajes de error o
    respaldos fuera de la base de datos.
- Los logs y mensajes de error no incluyen DNI, nombres ni contenido de
  documentos.

### V. Simplicidad

- Monolito modular: un proyecto Django, una app por módulo del ERP.
- Prohibido sin enmienda: microservicios, SPA (React/Next.js/Vue), API REST,
  HTMX, Redis, capas de caché, CQRS/MediatR, repositorios genéricos sobre el
  ORM.
- Una abstracción (interfaz, clase base) solo existe con al menos dos
  implementaciones reales.
- Toda complejidad adicional se justifica en la sección "Complexity Tracking"
  del plan.

### VI. Seguridad y control de acceso

- Autenticación de Django. Toda vista exige login y permiso explícito por rol
  (Groups/permissions). Existen exactamente dos roles: **Administrador**,
  quien puede administrar cuentas y usar las funciones del ERP, y **Usuario**,
  quien puede usar las funciones del ERP. La gestión de cuentas y roles se hace
  desde el Django admin nativo (`/admin`), sin pantallas propias ni asistente
  de primer uso. El primer administrador se crea con un comando de gestión en
  el servidor. No se permite que un administrador se desactive a sí mismo ni
  que una acción deje el sistema sin ningún administrador activo.
- Validación de archivos por contenido real (no solo extensión) y por tamaño
  máximo, en el servidor.
- Los archivos nunca se sirven como estáticos públicos.
- Auditoría de acciones relevantes: quién confrontó qué, cuándo y con qué hash.
- Funciona 100 % en la LAN, sin dependencias de internet en tiempo de ejecución:
  modelos de OCR, diccionario `es_PE` y assets front se aprovisionan en el
  despliegue.

### VII. DevSecOps: la seguridad se verifica en cada cambio

- La seguridad se comprueba de forma automática y continua, desde el primer
  commit, no al final del proyecto.
- **Pipeline de CI obligatorio** (GitHub Actions) en cada Pull Request y en
  `main`: lint, tests, análisis estático y de seguridad (SAST), dependencias
  vulnerables (SCA) y búsqueda de secretos.
- **SonarQube es la puerta de calidad**: un PR NO se mergea si el Quality Gate
  falla. Se usa **Sonar way**: en código nuevo exige 0 vulnerabilidades, 0 bugs,
  100 % de Security Hotspots revisados y cobertura mínima de 80 %. Sonar way no
  evalúa duplicación ni cobertura en cambios de menos de 20 líneas nuevas; se
  acepta esta limitación del plan gratuito y se revisará si cambia el plan.
- **Secretos:** nunca en el repositorio. `gitleaks` corre en pre-commit y en el
  CI; los tokens (p. ej. `SONAR_TOKEN`) viven en GitHub Secrets o en el `.env`
  del servidor.
- **Dependencias:** `pip-audit` en el CI y Dependabot activado. Una
  vulnerabilidad alta o crítica sin corrección bloquea el merge, salvo
  excepción documentada.
- **Contenedores o imágenes de despliegue:** si se usan, se escanean (p. ej.
  Trivy) antes de desplegar.
- **Hallazgos:** no se marcan como "falso positivo" ni se aceptan sin una
  justificación escrita en el PR.
- **Rama `main` protegida:** solo se integra por PR con el CI en verde.
- **Herramienta:** SonarQube Cloud, con el análisis ejecutado desde el CI
  (Automatic Analysis desactivado) y el proyecto en modo privado.
- **Código enviado a análisis:** antes de cualquier análisis en la nube, el
  repositorio NO debe contener datos personales reales (incluidos los tests).
  Solo se envía el árbol saneado de la revisión analizada; el historial previo
  no se publica ni se analiza, y el repositorio permanece privado.
- **Arranque excepcional (una sola vez, en F1):** el PR que sanea el
  repositorio y añade el pipeline se integra con los cuatro controles ya
  disponibles (lint, tests, dependencias, secretos), porque el Quality Gate no
  puede existir antes de que `main` esté saneada. Desde el PR que activa
  SonarQube, los cinco controles, el gate y la protección de `main` son
  obligatorios sin excepción. Esta cláusula no habilita ninguna otra omisión
  de controles, ni en F1 ni en fases posteriores.

### VIII. Usabilidad: heurísticas de Nielsen

Toda pantalla del ERP cumple las 10 heurísticas de Nielsen, aplicadas así:

1. **Visibilidad del estado del sistema:** todo proceso de más de 1 s muestra
   su estado (pendiente, procesando, listo, error); tras cada acción hay un
   mensaje de confirmación.
2. **Coincidencia con el mundo real:** textos en español y con el vocabulario
   de la notaría (expediente, minuta, borrador, partida), nunca términos
   técnicos (task, hash, worker) en la interfaz.
3. **Control y libertad del usuario:** toda operación en curso se puede
   cancelar, y siempre hay un camino claro para volver atrás.
4. **Consistencia y estándares:** mismos componentes de AdminLTE 4 para la
   misma función en todo el ERP (botón primario, tablas, badges de estado),
   mismo lugar para las mismas acciones.
5. **Prevención de errores:** validar antes de enviar (tipo y tamaño de
   archivo, campos obligatorios) y pedir confirmación antes de acciones
   destructivas o irreversibles.
6. **Reconocer antes que recordar:** menú visible según el rol, migas de pan,
   datos del expediente visibles en cada paso; nada que el usuario deba
   memorizar entre pantallas.
7. **Flexibilidad y eficiencia:** filtros y búsqueda en listados; atajos solo
   donde el uso repetido lo justifique.
8. **Diseño estético y minimalista:** cada pantalla muestra solo lo necesario
   para su tarea; las observaciones se agrupan por capa y gravedad.
9. **Ayudar a reconocer y recuperarse de errores:** mensajes en lenguaje claro
   que dicen qué pasó y qué hacer, sin trazas técnicas ni datos personales.
10. **Ayuda y documentación:** textos de ayuda breves junto a los campos que lo
    requieran, y una guía de uso por flujo.

Además, mínimos de accesibilidad: etiquetas en todos los campos, navegación
con teclado, foco visible y contraste suficiente.

## Restricciones técnicas

- **Backend:** Python + Django (versión LTS vigente), PostgreSQL.
- **Frontend:** plantillas de Django + AdminLTE 4 (Bootstrap 5, sin jQuery) +
  Alpine.js. Assets guardados en `static/vendor/` con su versión anotada; sin
  CDN. Formularios con `crispy-bootstrap5`.
- **Tareas en segundo plano:** worker con cola sobre PostgreSQL (sin Redis).
  El estado se consulta desde la página con Alpine + `fetch` a un endpoint JSON.
- **Extracción:** RapidOCR sobre onnxruntime en CPU; PyMuPDF; lectura de
  `.docx` desde el XML; `.doc` con LibreOffice headless en Linux. La
  configuración de OCR solo cambia con una medición que lo respalde.
- **Formatos:** `.docx`, `.doc`, `.rtf`, `.odt`, `.pdf` (con y sin capa de
  texto), `.xlsx`, `.txt`, `.csv`, imágenes.
- **Dependencias:** versiones fijadas. Ninguna dependencia nueva si la
  biblioteca estándar, Django o una ya instalada lo resuelve.
- **Calidad:** `ruff` (lint + formato, con reglas de seguridad `S`/bandit) y
  `pytest` con cobertura.
- **Seguridad:** SonarQube (Quality Gate), `gitleaks`, `pip-audit`,
  Dependabot, `pre-commit`.
- **Despliegue:** on-premise en el Windows Server de la notaría, dentro de la
  LAN. Mecanismo: TODO(DESPLIEGUE), se decide en F8.
- **Prueba de concepto Streamlit** (`app.py`, `app_ortografia.py`): eliminada
  el 2026-10-20 al declarar el usuario la paridad funcional del ERP.

## Flujo de desarrollo

- Spec Kit por funcionalidad: `/speckit-specify` → `/speckit-clarify` →
  `/speckit-plan` → `/speckit-tasks` → `/speckit-analyze` → `/speckit-implement`.
- La spec manda: si el comportamiento cambia, primero se actualiza `spec.md` y
  después el código.
- Las reglas de negocio las define la notaría, no el agente. Toda duda de
  negocio queda como `[NEEDS CLARIFICATION]` hasta que el usuario responda.
- Un worktree de Orca por funcionalidad; integración a `main` mediante Pull
  Request.
- Puertas de calidad antes del merge (automáticas en el CI): `ruff`, `pytest`,
  Quality Gate de SonarQube, `pip-audit` y `gitleaks` en verde. Además:
  migraciones incluidas, sin datos reales en el diff y, si se tocó el núcleo,
  medición contra el expediente de referencia sin retroceso.
- Cada `spec.md` incluye una sección de requisitos de seguridad (quién puede
  hacer qué, qué datos toca, qué se valida) y cada `plan.md` indica cómo se
  cumplen.
- Cada `spec.md` con interfaz incluye requisitos de UX según el principio VIII
  (estados, mensajes, validaciones, confirmaciones). Antes del merge se revisa
  la pantalla contra las 10 heurísticas (se puede generar la lista con
  `/speckit-checklist`).
- Recomendado: el agente que no implementó revisa el diff contra `spec.md` y
  esta constitución.

## Gobernanza

- Esta constitución prevalece sobre cualquier otra práctica o instrucción del
  proyecto.
- Toda enmienda se hace por Pull Request, con motivo, versión nueva y
  actualización del Sync Impact Report.
- Versionado semántico: MAJOR = se elimina o redefine un principio; MINOR = se
  añade un principio o sección, o se resuelve un TODO; PATCH = redacción.
- El "Constitution Check" de cada `plan.md` verifica los principios I–VIII; una
  violación bloquea el plan o se justifica en "Complexity Tracking".

**Version**: 1.7.1 | **Ratified**: 2026-09-16 | **Last Amended**: 2026-10-20
