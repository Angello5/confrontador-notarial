# Calidad OCR · F31 · 2 de octubre de 2026

## Cambios implementados

- Agrupación de líneas según la inclinación dominante, respaldada por al menos tres cajas. Se mantienen el filtro de marcas diagonales y sus coordenadas para auditoría.
- Hasta cuatro lecturas por página cuando el texto es escaso o la confianza global es baja. Una caja dudosa aislada conserva el aviso, sin girar toda una página que ya se lee bien.
- Las capas PDF con caracteres inválidos activan OCR. Una alternativa parcial no reemplaza una capa más completa; se conserva el texto y se pide revisión.
- Metadatos por página: método, confianza disponible, cajas, inclinación, giro aplicado, intentos y razones de revisión. Las coordenadas corresponden a la imagen analizada.
- Avisos persistentes en resultados, impresión y Word. Los resultados históricos sin metadatos aparecen como lectura sin medición. La ausencia de observaciones no se presenta como garantía de coincidencia.
- Cachés vinculadas a la versión del algoritmo, modelos y resolución. La supresión del texto también borra los metadatos con contenido OCR.

No se añadieron dependencias, servicios externos ni reglas jurídicas. Se mantienen los modelos locales y 200 dpi.

## Medición y límites

La batería sintética usa siete imágenes ficticias y tres campos exactos por imagen: DNI, nombre e importe. Incluye página horizontal, inclinación de 7° y 10°, giros de 90° y 180°, bajo contraste y marcas diagonales. Se comprobaron los hashes: ambas versiones usan exactamente las mismas imágenes.

| Medida | Línea base | Candidato final |
|---|---:|---:|
| Campos exactos | 9/21 (42,9%) | 21/21 (100%) |
| Mediana por imagen | 2.602 ms | 5.298 ms |
| Tiempo total | 20,76 s | 32,90 s |

Artefactos: `ocr-baseline.json` y `ocr-candidato.json`. Son solo siete imágenes; ese 100% no estima la precisión sobre escrituras reales. Los tiempos son observados en esta máquina, con otras pruebas activas durante el candidato; no constituyen un ensayo de rendimiento aislado. Los giros pueden añadir trabajo hasta el límite de cuatro lecturas.

La muestra privada selecciona la primera y última página PDF no vacía de cada uno de los doce casos: 24 páginas. Compara conjuntos de campos detectados antes/después; un campo nuevo no es por sí solo un acierto y un campo ausente no es por sí solo un error confirmado. No hay etiquetas jurídicas validadas para medir sensibilidad o falsos positivos.

Resultado final de esa muestra: 17 DNI, 16 nombres, 4 partidas y 26 importes conservados (63 campos); cero campos nuevos o ausentes en esos cuatro grupos. Once páginas tienen texto idéntico y siete quedan señaladas para revisión. El resto puede diferir en espaciado o texto fuera de los campos contabilizados. La ejecución tardó 419,46 segundos con otras pruebas en paralelo; no es una comparación de rendimiento controlada.

La primera versión candidata perdió un DNI y cinco importes que la línea base reconocía. Se rechazó esa selección: el origen eran giros innecesarios activados por una caja de baja confianza en páginas con buena confianza global. Una regresión ficticia reproduce el fallo y protege la corrección. También se reprodujo y corrigió la sustitución de una capa PDF legible por un OCR parcial, y la de una capa corta (menos de 50 caracteres) por un OCR dudoso que no recupera más texto; ninguna de las 512 páginas PDF del corpus privado tiene una capa así, por lo que las cifras anteriores no cambian.

La confianza del OCR puede ser alta incluso cuando un dígito es incorrecto. Las señales de lectura no garantizan exactitud. La detección de capas corruptas cubre caracteres inválidos y de control; no identifica todas las capas erróneas compuestas por caracteres válidos.

## Variables para revisar nuevos errores

La referencia privada `expedientes_locales/auditoria-20261002/mejora_ocr/referencia_pendiente.json` contiene 83 documentos pendientes de revisión. No se sobrescribe al repetir la medición.

Para cada discrepancia confirmada, registrar:

1. Documento fuente y página; valor observado y esperado.
2. Persona y rol: distinguir comprador, vendedor, representante u otro interviniente.
3. Bien o partida a la que pertenece el dato.
4. Moneda y concepto del importe: precio, cuota, impuesto u otro concepto.
5. Fecha del documento fuente y tipo de error.
6. Confirmación del revisor.

Estas variables permiten separar errores de OCR, asociación de datos y reglas de confrontación. No se activaron nuevas obligaciones jurídicas sin esa validación. Para estimar efectividad real, revisar tanto observaciones emitidas como errores conocidos que el sistema no señaló, reservando casos distintos para validar futuros ajustes.

## Reproducción

```powershell
.venv/Scripts/python.exe scripts/medir_ocr_sintetico.py --actual --salida .venv/ocr-medicion/candidato-final.json
.venv/Scripts/python.exe scripts/evaluar_ocr_casos.py
```

El segundo comando requiere el corpus privado existente; sus textos quedan bajo `expedientes_locales`. Los artefactos compartibles contienen solo métricas y datos ficticios.

## Alcance de la entrega

Verificación final: 590 pruebas Python aprobadas, 3 omitidas por el entorno (dos de permisos POSIX y una de tipografía disponible en CI), 13 excluidas por los marcadores ordinarios. Cobertura: 92,53% (3.111/3.362 líneas), con el control de inventario de archivos aprobado. Cinco pruebas Node aprobadas. Ruff (análisis y formato), `manage.py check` y `makemigrations --check --dry-run` sin errores. Evidencia: `ocr-pytest.xml` y `ocr-cobertura.xml`.

La auditoría inicial de dependencias registrada en `auditoria-2026-10-02.md` revisó 98 paquetes sin vulnerabilidades conocidas; F31 no cambió dependencias. El análisis independiente detectó los tres problemas de selección/trazabilidad corregidos y documentados arriba.

La verificación local utiliza Windows y Python 3.12.14. Quedan pendientes la ejecución de CI con Python 3.13 y el Quality Gate de SonarQube exigidos para integrar/publicar. Esta carpeta carece de metadatos Git; no se creó un PR ni se desplegó en producción.

## Revisión de coherencia

FR-001/002/003/006 se cubren con regresiones del adaptador; FR-004/005 con persistencia, reapertura de corridas, supresión y exportación; FR-007/008 con las dos mediciones y la referencia privada. No hay reglas jurídicas nuevas ni tareas sin requisito asociado. Se verificó el aviso histórico en navegador; evidencia visual: `ocr-aviso-lectura.png`.
