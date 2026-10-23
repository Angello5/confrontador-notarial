# F61 · Capa de sentido: «Sentido frente a la minuta»

**Fecha**: 2026-10-22  
**Estado**: implementado con el interruptor apagado por defecto. Se activa después de la demostración funcional y de la revisión legal de la licencia de spaCy.  
**Base contractual**: Adenda N.° 01 (CR-01), numerales 3.3 (Alternativa B), 3.6 (selección), 3.8 (regla de arquitectura del A.1) y 3.9 (entregables).  
**Sustento**: Informe de Evaluación del CR-01, versión 1.1 (22/10/2026), secciones 3.3, 3.6, 3.7 y 7 a 10.

## Origen

La notaría eligió la Alternativa B del CR-01: un verificador semántico local. Hasta ahora el confrontador revisa, sin modelos, que los DNI, RUC, montos, nombres y direcciones coincidan con las fuentes, y la ortografía. No ve si una cláusula del proyecto **cambió de sentido** aunque esté bien escrita: un «NO» que la minuta no tiene, otra parte que se obliga, una condición quitada o agregada, otro tiempo verbal.

El 2026-10-22 el usuario pidió: «arranca con la implementación de la B, completa». También pidió que la concordancia de género y número la haga spaCy con análisis gramatical, y que el NLI sea un modelo que funcione bien en el servidor.

## Comportamiento

### Qué compara

- Compara el **cuerpo de cláusulas** del proyecto, desde «PRIMERA» hasta «AGREGUE USTED» o la conclusión. La comparecencia y los datos de RENIEC los siguen revisando las reglas.
- **Respaldo:** para decidir si una oración del proyecto tiene respaldo, se busca en la **minuta completa**, incluida su introducción.
- **Emparejamiento:**
  - una oración copiada tal cual se empareja sin modelos;
  - las demás se emparejan con la oración más parecida, según e5-small. La pareja se acepta si el coseno es 0,9 o más, o si comparten al menos el 70 % de las palabras.
- **No se anota** un par que solo difiere por:
  - letras mal leídas por el OCR («EI»/«EL»);
  - un corte de oración distinto;
  - la numeración de cláusulas o incisos («PRIMERA.-», «a)», «1.», «-»);
  - las cifras en letras que la notaría agrega junto al número («(CIEN MIL CON 00/100 SOLES)»);
  - el membrete repetido en tres páginas o más de la minuta escaneada.

  Las cifras, en números o en letras, las juzgan las reglas: a los modelos les llegan neutras.
- **Clasificación:** cada par distinto lo clasifican dos modelos de inferencia de lenguaje natural (NLI), en las dos direcciones (minuta ⇒ proyecto y proyecto ⇒ minuta). Uno es mDeBERTa-v3-base-xnli y el otro MiniLMv2-L6-xnli.
- **Texto sin respaldo:** las oraciones seguidas del proyecto que no están en ninguna parte de la minuta se anotan en un solo bloque.
- **Concordancia:** el análisis gramatical de spaCy (`es_core_news_md`) busca errores de concordancia de género y número:
  - **nominal:** determinante o adjetivo a dos palabras o menos del sustantivo;
  - **sujeto y verbo:** a tres palabras o menos.

  Si el mismo error ya viene escrito en la minuta, no se anota, porque lo trae el cliente.

### Niveles y tipos

| Nivel | Cuándo |
|---|---|
| **Observación** | Los dos modelos ven el cambio con seguridad de 0,60 o más. |
| **Para revisar** | Lo ve uno solo. También el texto sin respaldo y la concordancia. |

| Tipo | En pantalla |
|---|---|
| CONTRADICE | Contradice la minuta |
| OMITE | Omite algo de la minuta |
| AGREGA | Agrega algo que la minuta no dice |
| CAMBIO | Cambia el sentido |
| SIN_RESPALDO | Sin respaldo en la minuta |
| CONCORDANCIA | Concordancia |

Si un solo modelo ve la contradicción, el tipo es el de mDeBERTa. Si la ven los dos, manda la contradicción de mDeBERTa; si no, el tipo de MiniLM, que casi no da falsas alarmas.

### Cuándo y dónde corre

- **Proceso:** corre en el worker (`procesar_documentos`), **después** de la confrontación por reglas y en un registro aparte (`AnalisisSentido`). Analiza la última corrida con resultado de cada borrador de kardex, una por vuelta, para no frenar la lectura de documentos.
- **Transferencias vehiculares:** no se analizan, porque no tienen minuta.
- **Pantalla:** la confrontación muestra la sección **«Sentido frente a la minuta»** debajo de las observaciones, con «Dice minuta» y «Dice proyecto» uno junto al otro. Mientras el análisis está en curso, la sección lo dice y se actualiza sola cada 5 segundos.
- **Informe:** el informe en Word, PDF o Excel incluye la sección si el usuario la marca. Viene marcada.

### Interruptor

- `SENTIDO_ACTIVO` está apagado por defecto. Apagado, el worker no analiza, la pantalla no muestra la sección y el ERP queda exactamente como antes.
- Si se apaga después de haber analizado, las anotaciones ya guardadas dejan de mostrarse. Si se vuelve a encender, aparecen otra vez.

## Requisitos

- **FR-001**: la capa no decide datos del A.3 ni cambia la corrida: con la capa activa o apagada, `Corrida.hallazgos` y `Corrida.huella` son idénticos (numeral 3.8).
- **FR-002**: la misma entrada da las mismas anotaciones y la misma huella (P-01), con hilos fijos (`SENTIDO_HILOS`, 3 por defecto) y sin muestreo.
- **FR-003**: cada análisis registra la versión del manifiesto de modelos (fecha y huella de los SHA-256), el tiempo y la huella de las anotaciones (P-06, P-08).
- **FR-004**: un archivo de modelo que falta o cuya huella no coincide no se carga.
  - El worker no registra nada y lo reintenta cuando el modelo esté.
  - La pantalla dice que el análisis no está disponible y que se avise al administrador.
- **FR-005**: si el análisis falla, queda registrado como error, sin texto de los documentos en el log, y la pantalla lo dice. Las observaciones no cambian.
- **FR-006**: sin red. Los modelos se cargan de una carpeta local (`SENTIDO_MODELOS_DIR`) y spaCy, del paquete instalado (P-09).
- **FR-007**: la supresión a solicitud (`suprimir_texto_expediente`) borra las oraciones guardadas en las anotaciones y conserva la huella (Ley 29733).
  - Alcanza a toda corrida que usó esos textos, según las entradas que registra, aunque sea de otro expediente o su documento ya no exista.
  - Si la supresión ocurre mientras se analiza, el análisis no guarda oraciones: al guardar, bloquea los textos, comprueba que siguen siendo los analizados y, si no, queda como suprimido.
- **FR-008**: la sección no aparece en transferencias vehiculares, ni con un resultado que no sea «RESULTADO» (advertencia de correspondencia, no disponible o error).
- **FR-009**: el comando `verificar_modelos_sentido` compara cada archivo con su huella. Dice si la capa está activa o apagada y termina con error si algo no coincide.

## Seguridad

- **Quién:** la sección y su endpoint de estado exigen sesión y los mismos permisos que la pantalla de confrontación (`_requiere_rol` y expediente visible). El endpoint responde con `Cache-Control: no-store`.
- **Qué datos:** el análisis lee los textos ya extraídos que registra la corrida. Guarda en `AnalisisSentido` las oraciones anotadas: son resultados, como los fragmentos de las observaciones. Nada sale del servidor. Los logs solo llevan el número de corrida y el tipo de error.
- **Qué se valida:**
  - el SHA-256 de cada modelo antes de cargarlo;
  - la versión del paquete de spaCy;
  - que la corrida pertenezca al borrador y al expediente consultados (`_borrador_y_corrida`).
- **Dependencias:** van aparte en `requirements-sentido.txt` (spaCy, tokenizers y el modelo de español), con hashes, y solo se instalan donde la capa se activa. El modelo `es_core_news_md` es GPL-3.0: requiere revisión legal antes de activarlo en producción.

## UX (principio VIII)

- **Visibilidad del estado (1):** la sección dice «Analizando…» y se actualiza sola. Tras 10 minutos sugiere actualizar la página.
- **Lenguaje de la notaría (2):** usa «Dice minuta», «Dice proyecto», «Observación», «Para revisar» y «Sin respaldo en la minuta». No muestra nombres de modelos ni cifras de seguridad.
- **Consistencia (4):** usa el mismo panel, los mismos chips de severidad (media para observación, baja para revisar) y los mismos avisos del resto de la confrontación.
- **Minimalismo (8):** las anotaciones van aparte de las observaciones de reglas y se ordenan como se leen en el proyecto. Una línea explica los dos niveles.
- **Recuperarse de errores (9):** si falla o faltan los modelos, la sección lo dice en lenguaje claro y aclara que las demás observaciones no cambian.
- **Ayuda (10):** el texto de la sección aclara qué hace y que la revisión del abogado decide.

## Medición (kardex locales, fuera del repositorio)

Medido el 22/10/2026 en el equipo de desarrollo (Apple M1, CPU, 3 hilos, ONNX Runtime 1.30) con los 12 proyectos y la copia sembrada del kardex de la demostración.

| Medida | Resultado |
|---|---|
| Demostración: errores sembrados detectados | 5 de 5 (negación, cambio de parte, tiempo verbal, condición quitada y agregada) |
| Falsas alarmas en la demostración | 0 |
| Anotaciones en los 12 proyectos | 82 (69 de sentido y 13 de concordancia). El informe v1.1 midió 85 de sentido sin los filtros de F61 |
| Tres corridas seguidas | Huellas idénticas en los 13 casos |
| Tiempo por proyecto | 14 s de promedio y 67 s el más largo, en el M1. En SQLSERVER (x86) se mide en la instalación |
| Carga de los modelos | 7 s, una vez por proceso |

El M1 no es representativo de la velocidad de ONNX Runtime en x86. El tiempo máximo por expediente se fija por escrito tras medir en el servidor (numeral 5.2 b).
