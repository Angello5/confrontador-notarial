# Validación F34

Python 3.13, PostgreSQL de prueba y fixtures ficticios. No usar base de expedientes para demostraciones.
1. pytest tests/test_carga_continua.py tests/test_procesamiento_concurrente.py y suite con cobertura.
2. node --test tests/carga_frontend.test.cjs y demás tests frontend.
3. Ruff check/format, manage.py check y makemigrations --check --dry-run.
4. Servidor aislado: tres roles consecutivos, Confrontar pendiente, cancelar/reintentar y salir/volver. Confirmar reutilización.
5. Marca → propuesta → confirmar → copia DOCX. Hash original intacto. Aviso de calidad independiente.
6. Medición primera carga/reutilización y consumidores 1/2; repetir en servidores en F8.
Integración pendiente de Git, PR, CI y Quality Gate.

## Medición de duraciones (FR-012)
- `Documento.metricas`: `recepcion_servidor_segundos`, `cola_segundos`, `lectura_segundos` y `reutilizada`.
- `Corrida.presentacion["metricas"]`: `analisis_segundos`, `campos_segundos` y `comparacion_segundos`.
- La preparación de la vista DOCX se registra en el log del worker (`vista documento_id=… segundos=…`).
- Solo números y booleanos: ni nombres de archivo, ni rutas, ni texto documental.
- Las cifras de esta máquina de desarrollo no representan al servidor de la notaría; la medición con 1 y 2 consumidores se repite en F8.
