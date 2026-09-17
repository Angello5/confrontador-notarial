<!--
Sync Impact Report
- Version: 1.1.0 → 1.2.0 (MINOR: se añade el principio VIII Usabilidad)
- Principios añadidos: VIII. Usabilidad según las heurísticas de Nielsen
- Secciones modificadas: Flujo de desarrollo (requisitos de UX en specs con
  interfaz y revisión heurística antes del merge)
- Historial: 1.1.0 añadió VII DevSecOps; 1.0.0 ratificación inicial
- Plantillas: plan-template.md lee la constitución en "Constitution Check" (sin cambios necesarios)
- TODO pendientes:
  - TODO(SONAR): SonarQube Cloud vs SonarQube Server autoalojado. Decidir en F1.
  - TODO(ROLES): roles concretos. Decidir en F2.
  - TODO(RETENCION_TEXTO): ¿se conserva el texto extraído (caché de OCR)? Decidir en F4.
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
  quién, cuándo y estado. Nunca el archivo original.
- Texto extraído: NO se persiste hasta que se decida lo contrario
  (TODO(RETENCION_TEXTO), a resolver en F4 y enmendar aquí).
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
  (Groups/permissions). Roles concretos: TODO(ROLES), se definen en F2.
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
  falla. Como mínimo, en código nuevo: 0 vulnerabilidades, 0 bugs nuevos
  críticos o bloqueantes, 100 % de Security Hotspots revisados y cobertura
  mínima de 80 %.
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
- **Código enviado a análisis:** antes de cualquier análisis en la nube, el
  repositorio NO debe contener datos personales reales (incluidos los tests).
  Herramienta: TODO(SONAR), se decide en F1.

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
- **Prueba de concepto Streamlit** (`app.py`, `app_ortografia.py`): se mantiene
  hasta que el ERP alcance paridad funcional y luego se elimina.

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

**Version**: 1.2.0 | **Ratified**: 2026-09-16 | **Last Amended**: 2026-09-17
