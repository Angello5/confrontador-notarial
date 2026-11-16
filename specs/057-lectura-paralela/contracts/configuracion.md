# Contrato de configuración · F76

Variables de entorno del proceso de lectura. En el servidor van en `erp.env` (F8).

| Variable | Valores | Por defecto | Efecto |
|---|---|---|---|
| `OCR_MOTOR` | `onnxruntime`, `openvino` | `onnxruntime` | Motor de ejecución de los modelos de OCR. `onnxruntime` es la lectura anterior a F76. |
| `OCR_PROCESOS` | entero ≥ 1 | `1` | Procesos de lectura por worker. Con `1` las páginas se leen en serie. |
| `OCR_HILOS` | entero ≥ 1 | `1` con varios procesos; sin fijar con uno | Hilos del motor en cada proceso de lectura. |

Reglas:

- Un valor que no sea válido detiene el arranque con un mensaje que nombra la variable.
- `OCR_PROCESOS × OCR_HILOS` no debe superar 3 en el servidor de la notaría mientras comparta el equipo con otros sistemas. No lo impone el código: lo fija la medición.
- Sin configurar nada, la lectura es exactamente la anterior a F76.
- Lectura rápida propuesta para el servidor de la notaría, pendiente de su medición y de la decisión sobre el texto: `OCR_MOTOR=openvino`, `OCR_PROCESOS=3`, `OCR_HILOS=1`.
- Se ejecuta un solo worker de lectura por servidor.

Salida de `scripts/medir_lectura_paralela.py`, una línea por configuración:

```text
motor=<m> procesos=<n> hilos=<h> paginas_min=<x> memoria_gb=<y> texto_identico=<a>/<total> avisos_identicos=<b>/<total>
```
