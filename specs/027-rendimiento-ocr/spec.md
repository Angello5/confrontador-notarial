# F33 · Rendimiento del OCR

**Feature Branch**: `feature/f33-rendimiento-ocr`

**Created**: 2026-10-03

**Status**: Implementado y verificado localmente; integración por PR, CI y Quality Gate pendientes.

**Input**: «Verificar si se puede mejorar el tiempo del OCR para que no sea tan pesado para el cliente», a partir de las mediciones de `docs/ocr-tiempos-2026-10-02.md`. Mejoras aprobadas: 1, 2, 3 (solo hojas totalmente blancas) y 5.

## Clarifications

### Session 2026-10-03

- Q: ¿Qué umbral define una hoja que no se lee por OCR, si el 0,1 % actual perdería una página con una sola línea (un DNI)? → A: Solo hojas totalmente blancas: píxeles oscuros ≤ 0,001 % de la página.
- Q: ¿Qué pasa con el perfil reutilizado de LibreOffice si una conversión falla? → A: Se descarta ese perfil y la siguiente conversión crea uno nuevo.

## User Scenarios & Testing

### US1 · Los escaneos se leen más rápido con el mismo texto (P1)

El usuario sube documentos escaneados y espera menos a que queden listos. El texto leído de cada página es exactamente el mismo que antes; solo cambia el tiempo.

**Why this priority**: 510 de 512 páginas auditadas eran escaneos; un expediente tarda de 1 a 6,5 minutos solo en lectura.

**Independent Test**: leer las mismas páginas ficticias con el motor anterior y el nuevo; el texto coincide carácter a carácter y el tiempo total baja.

**Acceptance Scenarios**:

1. **Given** un PDF escaneado ficticio, **When** se extrae, **Then** el texto por página es idéntico al de la versión anterior.
2. **Given** la muestra privada de 12 páginas reales, **When** se mide antes y después, **Then** el tiempo total baja y el texto no cambia.

### US2 · Las páginas giradas se leen bien y sin lecturas de más (P1)

Una hoja escaneada al revés se lee con dos lecturas y sin aviso falso. Una hoja escaneada de lado conserva el orden de sus líneas, para que nombre, DNI y monto sigan en la misma línea.

**Why this priority**: hoy la hoja al revés cuesta 4 lecturas (~21 s) y queda marcada como «lecturas divergentes»; la hoja de lado sale con las líneas desordenadas, lo que afecta a la confrontación.

**Independent Test**: páginas ficticias giradas 180° y 90°; se comprueba el número de lecturas, los avisos y el orden de las líneas.

**Acceptance Scenarios**:

1. **Given** una página al revés cuya lectura original no devuelve texto, **When** se reintenta, **Then** se acepta el primer giro legible, se detiene y no se marca «lecturas divergentes».
2. **Given** una página de lado, **When** un giro deja el texto vertical y otro horizontal con puntuación equivalente, **Then** gana el horizontal y las líneas salen en orden.
3. **Given** una página con texto horizontal y números distintos entre dos lecturas extensas, **When** se reintenta, **Then** se mantiene el aviso «lecturas divergentes» (comportamiento de F31).

### US3 · Las hojas totalmente blancas no pasan por el OCR (P2)

Una hoja escaneada sin ninguna marca no se lee; queda señalada para revisión como hoy. Una hoja con cualquier marca visible, aunque sea una sola línea corta, se sigue leyendo.

**Why this priority**: ahorro pequeño (1–2 s por hoja blanca) pero sin riesgo si el umbral solo admite hojas limpias.

**Independent Test**: hoja ficticia en blanco con ruido de escáner y hojas con una sola línea («1», «DNI 90000001»).

**Acceptance Scenarios**:

1. **Given** una hoja escaneada en blanco, **When** se extrae, **Then** no se ejecuta ninguna lectura OCR y la página queda con el motivo `pagina_casi_vacia`.
2. **Given** una hoja con un solo número de folio o un DNI, **When** se extrae, **Then** se lee por OCR como hoy.

### US4 · Los `.doc`, `.rtf` y `.odt` se convierten más rápido (P2)

A partir del segundo documento en formato antiguo dentro del mismo proceso de extracción, la conversión no vuelve a preparar LibreOffice desde cero.

**Why this priority**: 6,7 s por documento hoy, 3,3 s medido con perfil reutilizado.

**Independent Test**: convertir dos documentos ficticios seguidos y comprobar que el segundo reutiliza el perfil y produce el mismo texto.

**Acceptance Scenarios**:

1. **Given** dos documentos antiguos en el mismo proceso, **When** se convierten, **Then** ambos usan el mismo perfil y el texto es igual al de hoy.
2. **Given** dos procesos de extracción simultáneos, **When** convierten a la vez, **Then** cada proceso usa su propio perfil.

### Edge Cases

- Lectura original vacía y ningún giro legible: se conservan los motivos de revisión y el número real de lecturas.
- Página de lado en la que ningún giro produce cajas horizontales: se elige por puntuación, como hoy.
- Hoja en blanco con ruido o motas: solo se salta si los píxeles oscuros no superan el 0,001 % de la página.
- Imagen que no se puede abrir: se mantiene el comportamiento actual (lectura directa del motor, sin giros).
- Perfil de LibreOffice dañado o bloqueado: la conversión falla con el mismo error controlado de hoy, el perfil se descarta y la siguiente conversión crea uno nuevo.
- Caché: las páginas giradas o en blanco pueden producir un resultado distinto al anterior, así que las lecturas guardadas con la versión previa no se reutilizan.

## Requirements

### Functional Requirements

- **FR-001**: El motor OCR DEBE usar reserva de memoria y recibir la página rasterizada en memoria, sin codificarla a PNG, manteniendo 200 dpi y los mismos modelos.
- **FR-002**: Con las mismas páginas, el texto de US1 DEBE ser idéntico al que produce la versión anterior.
- **FR-003**: Si la lectura original no tiene texto o es escasa, una lectura alternativa NO DEBE marcarse como «lecturas divergentes».
- **FR-004**: Los reintentos DEBEN detenerse en el primer giro que no requiera revisión y cuyas líneas sean horizontales; el máximo sigue siendo cuatro lecturas.
- **FR-005**: Ante puntuaciones equivalentes, DEBE preferirse la lectura con líneas horizontales sobre la de texto vertical.
- **FR-006**: Una página con píxeles oscuros que no superan el 0,001 % de su superficie NO DEBE leerse por OCR; DEBE registrarse con cero lecturas y el motivo `pagina_casi_vacia`, que requiere revisión.
- **FR-007**: Cada proceso de extracción DEBE reutilizar un único perfil de LibreOffice, distinto del de otros procesos, y eliminarlo al terminar. Si una conversión falla, el perfil se descarta y la siguiente conversión crea uno nuevo.
- **FR-008**: La identidad del extractor DEBE cambiar para que no se reutilicen lecturas guardadas con la versión anterior.
- **FR-009**: No se añaden dependencias, modelos, servicios externos ni reglas jurídicas; no cambia la resolución.

### Key Entities

- **Informe de lectura por página** (existente, F31): texto, método, confianza, motivos, intentos, cajas y giro aplicado. No cambia de forma; cambian sus valores en páginas giradas o blancas.

## Success Criteria

### Measurable Outcomes

- **SC-001**: En la muestra privada de 12 páginas reales, el tiempo total baja al menos un 10 % con el texto idéntico al de la versión anterior.
- **SC-002**: Una página ficticia al revés se lee con como máximo 2 lecturas y sin aviso de lecturas divergentes.
- **SC-003**: Una página ficticia de lado conserva el orden de sus líneas (similitud con el texto original ≥ 99 %).
- **SC-004**: Una hoja totalmente blanca se resuelve con 0 lecturas; una hoja con una sola línea corta se sigue leyendo.
- **SC-005**: El segundo documento antiguo convertido en el mismo proceso tarda al menos un 30 % menos que hoy.
- **SC-006**: La suite completa, Ruff y el Quality Gate de SonarQube quedan en verde.

## Assumptions

- La exactitud real se sigue midiendo contra la lectura actual, porque no hay etiquetas de la notaría (F31).
- Los tiempos se miden en el equipo de desarrollo; el servidor de la notaría puede dar cifras distintas.
- La reserva de memoria aumenta el consumo de RAM del proceso de extracción; se acepta mientras quepa en el servidor (a medir en F8).
- F32 modifica la misma función de conversión de LibreOffice en un trabajo aún no integrado; el conflicto se resuelve al integrar la segunda de las dos fases.
- Fuera de alcance: procesos en paralelo (requiere decidir el tiempo límite), resolución, OpenVINO, clasificador de orientación y prioridad de la cola.
