# Checklist Nielsen y accesibilidad: F11 · Extracción por personas

**Propósito**: revisar la interfaz de personas, estados, revisión manual y
privacidad visible. `[X]` exige evidencia de plantilla/prueba; esta etapa deja
todos los ítems pendientes.

**Feature**: [contracts/ui.md](../contracts/ui.md) y [spec.md](../spec.md)

## Visibilidad y vocabulario

- [ ] CHK001 La pantalla distingue `TRABAJANDO`, resultado, advertencia, revisión manual, no disponible y error seguro. [Heurística 1, contracts §Estados]
- [ ] CHK002 La tabla de personas muestra una fila por persona unificada y todas sus procedencias. [Heurística 1/8, contracts §Personas]
- [ ] CHK003 Se muestran recuentos de páginas descartadas y no clasificadas sin volcar texto. [Heurística 1/8, contracts §Estados]
- [ ] CHK004 El vocabulario usa persona, documento, fuente, página y revisión manual; no usa task, worker, hash ni términos técnicos. [Heurística 2, Constitución VIII]

## Control, prevención y eficiencia

- [ ] CHK005 El botón se habilita solo con CLIENTE, MINUTA, BORRADOR, texto y páginas disponibles; el servidor repite la validación. [Heurística 3/5]
- [ ] CHK006 Cada borrador se procesa por separado y existe retorno claro al expediente. [Heurística 3/6]
- [ ] CHK007 Una página antigua sin páginas serializadas pide volver a subir, no inventa una frontera. [Heurística 5, contracts §Estados]
- [ ] CHK008 Un documento cruzado no se presenta como resultado limpio y uno parecido no se aprueba automáticamente. [Heurística 5/9]
- [ ] CHK009 La acción mantiene POST, CSRF, permisos y no acepta personas, fuentes ni umbral desde el navegador. [Heurística 5/VI]

## Consistencia, errores y ayuda

- [ ] CHK010 Personas, Regla y Ortografía conservan grupos y recuentos conocidos por F5. [Heurística 4/8]
- [ ] CHK011 Los mensajes diferencian sin documento, documento sin titular, conflicto de lecturas, página no clasificada y error de extracción. [Heurística 9/10]
- [ ] CHK012 `revision_manual` explica que no es aprobación y orienta a revisar el documento fuente. [Heurística 9]
- [ ] CHK013 El aviso SISGEN solo se muestra con el texto acordado por NC-001; no se oculta una decisión de negocio en la plantilla. [Heurística 10]

## Accesibilidad y privacidad visible

- [ ] CHK014 Tablas tienen encabezados y las acciones tienen texto; estados usan `role`/`aria-live` apropiados. [Accesibilidad]
- [ ] CHK015 Foco visible, teclado y orden de lectura funcionan en `<details>`, tablas, alertas y acción de confrontar. [Accesibilidad]
- [ ] CHK016 El significado de confirmada, sin documento y revisión manual no depende solo del color. [Accesibilidad]
- [ ] CHK017 Solo usuarios autorizados ven nombres, documentos, nombres de archivo y páginas; no se muestra ruta, hash, texto completo ni logs. [Constitución IV/VI]
- [ ] CHK018 No se cargan recursos CDN ni se envía contenido a servicios externos. [Constitución I/VI/VII]
- [ ] CHK019 El nombre de archivo se escapa y se muestra solo como procedencia autorizada, nunca como ruta ejecutable. [Seguridad]

## Decisiones pendientes

- [NEEDS CLARIFICATION] CHK020 Definir presentación del DNI consultado en SISGEN antes de cerrar el recuento de descartes. [NC-001]
- [NEEDS CLARIFICATION] CHK021 Definir si el nombre sin documento es informativo o genera una observación. [NC-003]
- [NEEDS CLARIFICATION] CHK022 Definir si la página no clasificada se lista como revisión manual o solo como recuento. [NC-005]

## Evidencia

Pendiente de implementación. No se declara revisión visual del navegador,
pruebas UI, cobertura ni Quality Gate remoto en esta etapa.
