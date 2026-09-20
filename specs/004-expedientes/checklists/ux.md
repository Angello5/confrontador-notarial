# Checklist Nielsen y accesibilidad: F4 · Expedientes

**Purpose**: revisar si los requisitos de interfaz describen las 10 heurísticas
de Nielsen y los mínimos de accesibilidad; no valida la implementación.
**Created**: 2026-09-20
**Feature**: [contracts/ui.md](../contracts/ui.md) y [spec.md](../spec.md)
**Review Ownership**: dejar todos los ítems sin marcar hasta la revisión del
revisor. `[x]` significa que el requisito está bien definido, no que la pantalla
ya exista.

## Visibilidad del estado y coincidencia con el mundo real

- [ ] CHK001 ¿Cada estado `PENDIENTE`, `PROCESANDO`, `LISTO` y `ERROR` tiene texto, significado y acción siguiente definidos? [Heurística 1, contracts §Estados]
- [ ] CHK002 ¿El expediente resume cuántos documentos faltan sin sugerir un porcentaje que no se puede medir? [Heurística 1, Spec §UX]
- [ ] CHK003 ¿Está definido el estado de una consulta JSON fallida, una recarga y el regreso posterior a la pantalla? [Heurística 1, contracts §Avance]
- [ ] CHK004 ¿El vocabulario visible usa expediente, fuente, borrador y extracción, y evita task, worker, hash y términos técnicos? [Heurística 2, Spec §Requisitos UX]
- [ ] CHK005 ¿La ayuda diferencia minuta/documentos del cliente como `FUENTE` y proyecto de escritura como `BORRADOR` sin introducir reglas de negocio nuevas? [Heurística 2, Spec §Clarifications]

## Control, libertad y prevención de errores

- [ ] CHK006 ¿Cada operación iniciada por el usuario tiene una salida clara, cancelación o regreso, incluyendo validación fallida y reintento? [Heurística 3, Spec §Requisitos UX]
- [ ] CHK007 ¿El requisito de cerrar un expediente está definido antes de presentar una acción de cierre? [Heurística 3, Gap, data-model §Expediente]
- [ ] CHK008 ¿La prevención de duplicados, formato, tamaño y contenido se explica antes de enviar y se valida también en servidor? [Heurística 5, Spec §FR-011]
- [ ] CHK009 ¿La confirmación antes de eliminar un documento está vinculada a una función real o se mantiene como aclaración pendiente? [Heurística 5, Spec §Requisitos UX]
- [ ] CHK010 ¿La interfaz diferencia un expediente cerrado de un fallo técnico y explica qué acción queda disponible? [Heurística 5, contracts §Detalle]

## Consistencia, reconocimiento y eficiencia

- [ ] CHK011 ¿Las pantallas F4 reutilizan la ubicación, estilo y navegación del layout AdminLTE de F2? [Heurística 4, contracts §Mensajes]
- [ ] CHK012 ¿El usuario puede reconocer el expediente actual, sus documentos y sus estados sin memorizar códigos entre pantallas? [Heurística 6, Spec §UX]
- [ ] CHK013 ¿El listado define búsqueda/filtros si el volumen de expedientes lo requiere, o declara por qué no son necesarios en F4? [Heurística 7, Gap]
- [ ] CHK014 ¿El sondeo automático deja de ejecutarse en `LISTO` y ofrece una alternativa clara para actualizar tras un error? [Heurística 7, contracts §Avance]
- [ ] CHK015 ¿El estado vacío, la lista con errores y la lista completamente lista tienen jerarquía visual mínima y no muestran controles irrelevantes? [Heurística 8, Spec §UX]

## Errores, ayuda y accesibilidad

- [ ] CHK016 ¿Cada error dice qué ocurrió y qué puede hacer la persona, sin traceback, rutas, hash, nombres ni texto? [Heurística 9, Spec §Requisitos de seguridad y privacidad]
- [ ] CHK017 ¿La ayuda sobre formatos admitidos, tamaño máximo, roles y reintento está junto al campo o acción correspondiente? [Heurística 10, contracts §Detalle]
- [ ] CHK018 ¿Todos los campos tienen `label` asociado, instrucciones y error accesible por tecnología asistiva? [Accesibilidad, Constitución VIII]
- [ ] CHK019 ¿La navegación por teclado, el foco visible, el orden de tabulación y la operación del menú Alpine están definidos? [Accesibilidad, Constitución VIII]
- [ ] CHK020 ¿El contraste de estados y mensajes no depende solo de color y existe una alternativa textual? [Accesibilidad, Constitución VIII]
- [ ] CHK021 ¿La interfaz evita recursos CDN y mantiene disponibles los assets locales en una instalación sin internet? [Seguridad/Dependencia, Constitución VI/VII]
- [ ] CHK022 ¿La respuesta de estado excluye texto extraído y rutas temporales, y define qué datos mínimos son necesarios para la pantalla? [Privacidad, contracts §Rutas]
