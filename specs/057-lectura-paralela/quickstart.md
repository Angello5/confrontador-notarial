# Quickstart · F76 Lectura rápida de escaneos

Validación de extremo a extremo. Solo documentos ficticios.

## En desarrollo

```bash
python scripts/generar_fixtures.py
python -m pytest tests/test_lectura_paralela.py tests/test_expedientes_worker.py tests/test_procesamiento_concurrente.py
python -m pytest --cov --cov-report=term
```

| # | Escenario | Resultado esperado | Requisito |
|---|---|---|---|
| 1 | PDF escaneado ficticio leído en serie y con 3 procesos | Mismo texto y mismos avisos, páginas en orden | FR-001 a FR-003 |
| 2 | `OCR_MOTOR=onnxruntime`, `OCR_PROCESOS=1` | `version_extractor()` igual que antes de F76 | FR-005, SC-005 |
| 3 | Recaudo encolado antes que borrador y minuta | El worker toma borrador y minuta primero | FR-008 |
| 4 | Documento cuyo avance se renueva pasado el límite | No vuelve a la cola | FR-009 |
| 5 | Documento sin avance pasado el límite | Vuelve a `PENDIENTE` una vez | FR-009 |
| 6 | Una página falla en su proceso de lectura | Documento en «Error», sin texto, temporal borrado | FR-010 |
| 7 | `OCR_MOTOR` con un valor desconocido | El worker no arranca y nombra la variable | [contrato](contracts/configuracion.md) |

## En el servidor de la notaría

```powershell
# Con la cuenta de servicio, el worker detenido y los demás sistemas en uso normal:
python scripts\medir_lectura_paralela.py --paginas 40
```

| # | Comprobación | Criterio |
|---|---|---|
| 8 | Línea base: `onnxruntime`, 1 proceso | Anotar páginas por minuto |
| 9 | `openvino`, 3 procesos × 1 hilo | Al menos el doble que la línea base; texto y avisos idénticos |
| 10 | Memoria máxima de la configuración elegida | Dentro del presupuesto; actualizar `specs/046-despliegue/quickstart.md` |
| 11 | Otras configuraciones (2×1, 2×2, 3×2, 6×1) | Elegir la mejor que no pase de 3 núcleos y anotarla en `docs/mediciones-ocr.md` |
| 12 | Documento de más de 100 páginas | Se lee una sola vez |

Volver a la lectura anterior: `OCR_MOTOR=onnxruntime` y `OCR_PROCESOS=1` en `erp.env`, y reiniciar el worker.
