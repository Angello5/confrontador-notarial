# Checklist Nielsen y accesibilidad: F5 · Confrontación

**Propósito**: revisar que la implementación cumpla el contrato Nielsen y los
mínimos de accesibilidad. `[X]` significa comprobado por pruebas, revisión de
plantillas o contrato; la validación visual y las mediciones privadas siguen
siendo evidencia externa cuando corresponda.

**Feature**: [contracts/ui.md](../contracts/ui.md) y [spec.md](../spec.md)

## Visibilidad y vocabulario

- [X] CHK001 La acción y cada resultado tienen estados `TRABAJANDO`, advertencia, resultado, no disponible y error seguro. [Heurística 1, contracts §Estados]
- [X] CHK002 Los grupos muestran recuento de observaciones y el estado vacío no parece un fallo. [Heurística 1/8, contracts §Estados]
- [X] CHK003 La advertencia de borrador ajeno al expediente se distingue visualmente de una observación de redacción. [Heurística 1/9, Spec §UX]
- [X] CHK004 La interfaz usa expediente, fuente, borrador, campo, hallado, esperado y línea; no muestra task, worker o hash. [Heurística 2, contracts §Mensajes]

## Control, prevención y eficiencia

- [X] CHK005 El botón solo aparece habilitado con documentos necesarios listos y texto disponible; el servidor repite la validación. [Heurística 3/5, contracts §Disponibilidad]
- [X] CHK006 Cada borrador se confronta por separado y existe un retorno claro al detalle del expediente. [Heurística 3/6, contracts §Ruta]
- [X] CHK007 La acción usa POST con CSRF y no permite modificar umbral ni fuentes desde el navegador. [Heurística 5/VI, contracts §Ruta]
- [X] CHK008 La pantalla muestra solo las filas necesarias, agrupadas por regla y ortografía, sin volcar el texto completo. [Heurística 7/8, contracts §Agrupación]

## Consistencia, errores y ayuda

- [X] CHK009 Se conserva el layout, breadcrumbs, componentes y assets locales de AdminLTE 4 de F2. [Heurística 4, Constitución VIII]
- [X] CHK010 Los mensajes dicen qué ocurrió y qué hacer: esperar, revisar expediente, volver a subir o intentar nuevamente. [Heurística 9, contracts §Estados]
- [X] CHK011 La ayuda diferencia faltante, alterado, no coincidente y sin sugerencia sin inventar reglas de negocio. [Heurística 10, contracts §Agrupación]
- [X] CHK012 La pantalla comunica que el resultado no se guarda y que la acción se puede repetir. [Heurística 3, Spec §FR-011]

## Accesibilidad y privacidad visible

- [X] CHK013 Todas las tablas tienen encabezados, todas las acciones tienen texto y los estados usan `role`/`aria-live` apropiados. [Accesibilidad, contracts §Mensajes]
- [X] CHK014 La navegación por teclado, foco visible y orden lógico de lectura están definidos para botón, paneles y tablas. [Accesibilidad, Constitución VIII]
- [X] CHK015 El significado de los estados no depende solo del color; cada estado tiene texto. [Accesibilidad, contracts §Estados]
- [X] CHK016 El fragmento se limita al hallazgo necesario y nunca se muestra texto completo, rutas, hashes o datos personales en mensajes. [Privacidad, Constitución IV]
- [X] CHK017 No se cargan recursos CDN ni se envía el contenido a servicios externos. [Seguridad/Dependencia, Constitución VI/VII]

## Evidencia de implementación

Validación local del 2026-09-20: pruebas UI F5, revisión de plantillas y
`git diff --check` ejecutados en esta rama. No se declara validación visual de
navegador ni Quality Gate remoto.
