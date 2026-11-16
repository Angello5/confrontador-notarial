# F76 · Lectura rápida de escaneos en el servidor

**Feature Branch**: `feat/f76-lectura-paralela`

**Created**: 2026-11-16

**Status**: Draft

**Input**: el usuario pidió sacar la máxima velocidad a la lectura de documentos sin perder calidad, con el OCR en el servidor de la notaría y dimensionado para ese servidor, no para el equipo de desarrollo.

## Origen

- Casi todo lo que se sube son escaneos: en la muestra privada de 70 PDF, 544 de 546 páginas no traen texto digital. Los PDF digitales ya se leen en milisegundos; la espera está en los escaneos.
- Hoy un solo proceso lee los documentos de uno en uno y sus páginas en serie. Un kardex de 14 a 86 páginas espera entre 1 y 6,5 minutos antes de poder confrontarse (`docs/ocr-tiempos-2026-10-02.md`).
- Se midieron cuatro vías el 2026-11-16 (`docs/mediciones-ocr.md`, sección «Vías de velocidad»). Dos rinden y dos se descartan.

## Servidor de destino

Las decisiones de esta fase se toman para este equipo, no para el de desarrollo:

| | |
|---|---|
| Equipo | HPE ProLiant ML110 Gen10 |
| Procesador | Intel Xeon Bronze 3204, 1,90 GHz, 6 núcleos y 6 hilos (sin Turbo Boost ni Hyper-Threading) |
| Memoria | 64 GB |
| Sistema | Windows Server 2019 Standard |
| Carga compartida | PostgreSQL del ERP, la web, la capa de sentido si se activa (3 núcleos) y los otros sistemas de la notaría |

Consecuencia: no hay hilos lógicos de sobra. Cada proceso de lectura ocupa núcleos reales que se quitan a los demás sistemas, así que el reparto se fija por configuración y se valida midiendo en el propio servidor.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Los escaneos se leen varias veces más rápido (Priority: P1)

Una digitadora sube los recaudos escaneados de un kardex. El sistema lee varias páginas a la vez y termina en una fracción del tiempo actual, con el mismo texto y los mismos avisos de lectura que hoy.

**Why this priority**: es la espera que hoy frena a las usuarias y la mejora medida más grande.

**Independent Test**: subir un PDF escaneado ficticio de 20 páginas con la lectura rápida apagada y encendida, y comparar el texto, los avisos de calidad y el tiempo.

**Acceptance Scenarios**:

1. **Given** un PDF escaneado de varias páginas, **When** se lee con la lectura rápida, **Then** el texto guardado es idéntico, carácter a carácter y en el mismo orden de páginas, al de la lectura actual.
2. **Given** el mismo PDF, **When** se lee con la lectura rápida, **Then** cada página conserva los mismos avisos de calidad (lectura dudosa, motivos, relecturas) que con la lectura actual.
3. **Given** una página girada o con marca de agua, **When** se lee, **Then** recibe las mismas relecturas que hoy y el resultado elegido es el mismo.
4. **Given** un PDF digital o un `.docx`, **When** se sube, **Then** se lee como hoy, sin pasar por los procesos de lectura.

---

### User Story 2 - La confrontación empieza antes (Priority: P2)

La digitadora sube el borrador, la minuta y los recaudos de un kardex. El sistema lee primero el borrador y la minuta, que son cortos, y después los recaudos.

**Why this priority**: no acelera la lectura total, pero deja listos antes los dos documentos que la usuaria revisa primero y adelanta el resultado cuando los recaudos ya estaban leídos.

**Independent Test**: encolar recaudos y después un borrador y una minuta del mismo kardex, y comprobar el orden en que el sistema los toma.

**Acceptance Scenarios**:

1. **Given** documentos pendientes de varios roles, **When** el sistema toma el siguiente, **Then** elige primero borradores y minutas, y entre iguales el más antiguo.
2. **Given** dos kardex con documentos pendientes, **When** uno solo tiene recaudos, **Then** sus recaudos no esperan indefinidamente: se leen en cuanto no quedan borradores ni minutas pendientes.

---

### User Story 3 - Un documento largo no se repite ni se pierde (Priority: P2)

Un PDF de 150 páginas tarda más que el tiempo límite de un documento. Mientras el proceso que lo lee siga vivo, el sistema no lo devuelve a la cola ni lo lee dos veces.

**Why this priority**: con documentos largos, repetir la lectura anularía la mejora.

**Estado**: ya resuelto antes de esta fase. El riesgo descrito en `docs/ocr-tiempos-2026-10-02.md` (hallazgo 5) se cerró en F34: el proceso mantiene un bloqueo sobre el documento y la recuperación por tiempo límite lo respeta (`tests/test_procesamiento_concurrente.py`). F76 no añade ningún mecanismo: lo comprueba al revisar el código y lo conserva.

**Independent Test**: la prueba existente de F34; y un fallo de lectura deja el documento en «Error».

**Acceptance Scenarios**:

1. **Given** un documento en lectura con su proceso vivo, **When** pasa el tiempo límite, **Then** no vuelve a la cola.
2. **Given** un documento cuyo proceso murió, **When** pasa el tiempo límite, **Then** vuelve a la cola una sola vez y se lee de nuevo.
3. **Given** un proceso de lectura que falla en una página, **When** termina el documento, **Then** queda en «Error» con el mensaje actual y no se guarda texto parcial.

---

### User Story 4 - El administrador del servidor controla cuánto consume (Priority: P3)

Quien opera el servidor fija cuántos procesos de lectura corren y puede volver a la lectura actual con un cambio de configuración, sin tocar el código.

**Why this priority**: el servidor es compartido; sin este control la mejora no se puede desplegar con seguridad.

**Independent Test**: cambiar la configuración a un proceso y al motor actual y comprobar que el sistema se comporta exactamente como antes de esta fase.

**Acceptance Scenarios**:

1. **Given** la configuración por defecto del servidor, **When** se leen escaneos, **Then** se usan como máximo 3 de los 6 núcleos.
2. **Given** la lectura rápida apagada, **When** se lee cualquier documento, **Then** el texto, los avisos y la identidad de la lectura son los de antes de esta fase.
3. **Given** un motor configurado que no está disponible en el servidor, **When** arranca el proceso de lectura, **Then** se detiene con un mensaje claro antes de tomar ningún documento. La verificación periódica de F8 (`verificar.ps1`, aún sin implementar) recogerá este aviso.

### Edge Cases

- PDF con páginas mezcladas, unas digitales y otras escaneadas: solo las escaneadas van a los procesos de lectura; el orden final es el del documento.
- Documento de una sola página o imagen suelta: lo lee un único proceso de lectura, para no cargar otra copia de los modelos.
- Dos documentos grandes a la vez: el total de procesos de lectura no supera el configurado.
- La capa de sentido está activa: lectura y sentido no usan más núcleos de los que cada una tiene asignados.
- El servidor se reinicia a mitad de un documento: se recupera como hoy, por tiempo límite sin avance.
- Hoja en blanco: se sigue saltando sin lectura (F33).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Las páginas escaneadas de un mismo documento DEBEN poder leerse a la vez, y el texto final DEBE conservar el orden de las páginas.
- **FR-002**: El texto de cada página DEBE ser idéntico, carácter a carácter, al de la lectura actual. Un cambio de texto es un defecto (principio I).
- **FR-003**: Los avisos de calidad de cada página (confianza, motivos, relecturas, giro elegido) DEBEN ser los mismos que con la lectura actual. Si el motor nuevo altera una confianza lo bastante para cambiar un aviso, la fase no se integra hasta resolverlo.
- **FR-004**: La lectura DEBE usar el motor de ejecución que mejor rinde en el procesador del servidor, con los mismos modelos de OCR, la misma resolución y las mismas reglas de relectura. No cambian los modelos ni sus SHA-256.
- **FR-005**: El motor de ejecución y el número de procesos DEBEN formar parte de la identidad de la lectura solo en lo que pueda cambiar el texto: el motor entra en la llave; el número de procesos no (principio IV, caché de texto).
- **FR-006**: El número de procesos de lectura y los hilos de cada uno DEBEN ser configurables en el servidor. Valores por defecto, pensados para el Xeon de 6 núcleos: 3 procesos de 1 hilo. Con 1 proceso las páginas se leen en serie y los hilos quedan como los fija el motor, igual que hoy.
- **FR-007**: DEBE existir un interruptor para volver al motor actual sin desinstalar nada.
- **FR-008**: La cola DEBE tomar primero los borradores y las minutas y después los recaudos; entre documentos del mismo grupo, el más antiguo.
- **FR-009**: Un documento en lectura NO DEBE volver a la cola por tiempo límite mientras el proceso que lo lee siga vivo; si ese proceso muere, vuelve a la cola una vez. Ya se cumple desde F34 (el proceso mantiene un bloqueo sobre el documento): F76 no lo cambia y lo conserva.
- **FR-010**: Si falla la lectura de una página, el documento DEBE terminar en «Error», sin texto parcial, y su archivo temporal DEBE borrarse como hoy.
- **FR-011**: Los límites de recursos del ERP en el servidor (`specs/046-despliegue/quickstart.md`, FR-013 de F8) DEBEN actualizarse con la memoria y los núcleos medidos de la lectura.
- **FR-012**: DEBE existir una medición reproducible, con documentos ficticios, que se ejecute en el servidor y dé páginas por minuto, memoria máxima y la comprobación de texto y avisos idénticos para cada configuración.
- **FR-013**: La dependencia nueva del motor DEBE fijarse con versión y hashes y pasar la auditoría de dependencias. No se añade ninguna otra.

### Fuera de alcance

- **Caché por página**: en la muestra, 14 de 544 páginas se repiten (2,6 %) y ninguna entre expedientes. No compensa.
- **Clasificador de orientación**: 1 de 80 páginas venía girada; ahorraría cerca del 5 % y exige aprovisionar otro modelo.
- Cambiar modelos de OCR, resolución o reglas de relectura.
- OCR fuera del servidor de la notaría (constitución, principio VI).
- Sellos y número CAL: fase posterior.
- Avance visible por página en la pantalla: fase de interfaz posterior.

## Seguridad

- No cambian permisos, roles ni datos persistidos. Los procesos de lectura corren con la misma cuenta de servicio sin privilegios.
- Las páginas se pasan a los procesos de lectura dentro del servidor; no se escriben copias nuevas en disco fuera del directorio temporal, que se borra como hoy.
- Los registros siguen sin incluir texto de documentos, nombres ni DNI: solo identificadores, recuentos y tiempos.
- La medición del repositorio usa solo documentos ficticios. La muestra privada se mide fuera del repositorio y solo deja recuentos.

## UX

Sin pantallas nuevas. Los estados visibles (pendiente, procesando, listo, error) y sus mensajes no cambian (principio VIII.1). La usuaria solo nota que termina antes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En el servidor de la notaría, con la configuración por defecto, los escaneos se leen al menos 2 veces más rápido (páginas por minuto) que con la lectura actual medida en ese mismo servidor.
- **SC-002**: Sobre la muestra de referencia, 100 % de las páginas con texto idéntico y con los mismos avisos de calidad que la lectura actual.
- **SC-003**: Con la configuración por defecto, la lectura no ocupa más de 3 de los 6 núcleos ni más de la memoria que se documente tras medir (presupuesto inicial: 6 GB).
- **SC-004**: Ningún documento se lee dos veces por tiempo límite en una carga de prueba con un documento de más de 100 páginas.
- **SC-005**: Con la lectura rápida apagada, todas las pruebas existentes pasan sin cambios.

## Assumptions

- Las cifras del 2026-11-16 salen de un portátil con núcleos mezclados y son indicativas: 58 a 69 páginas por minuto con el motor nuevo y varios procesos, frente a 8 a 33 con el actual, con texto idéntico en 18 páginas (28 902 caracteres). El criterio de aceptación es la medición en el servidor, no estas cifras.
- En esa medición se comparó el texto, no las confianzas. FR-003 exige comprobarlas antes de integrar.
- El Xeon Bronze 3204 tiene 6 núcleos iguales, sin hilos lógicos: 3 procesos de 1 hilo dejan la mitad del procesador a los demás sistemas. La medición en el servidor puede cambiar ese valor por configuración, sin tocar el código.
- Cada proceso de lectura llegó a 1,7 GB con el motor actual (F33). La memoria con el motor nuevo no está medida.
- Cambiar el motor cambia la llave de la caché de texto: los recaudos y minutas ya leídos se vuelven a subir si se reabren, y los borradores `.docx` se releen solos (F50).
- El despliegue (F8) sigue en curso; esta fase no lo bloquea y sus valores entran en la plantilla de configuración del servidor.
