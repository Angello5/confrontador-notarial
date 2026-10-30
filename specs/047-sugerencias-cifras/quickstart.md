# Quickstart · F64 Sugerencias en cifras y cuotas

## Pruebas

```bash
python -m pytest tests/test_sugerencias_cifras.py tests/test_errores_borrador.py tests/test_reglas_f30.py
python -m pytest --cov --cov-report=term
python -m ruff check . && python -m ruff format --check .
```

Esperado: las historias 1 a 3 de la spec en verde con frases ficticias, y la ida y vuelta de `letras_de` en todo el rango.

## Ver el aviso en pantalla

1. Crear un kardex ficticio con una minuta que diga «LUIS SOTO EL 60 %» y un proyecto con «TREINTA Y SEI POR CIENTO (36%)», «TREINTA Y CINCO POR CIENTO (36%)» y un reparto 20-20-50.
2. Confrontar.
3. En la lista de observaciones deben verse los avisos del [contrato](contracts/observaciones.md), con su línea «Se sugiere».
4. Una confrontación anterior a F64 se ve como antes.

## Medición privada (kardex locales, nunca en CI)

Con el entorno local y la base `confrontador_audit`, correr el script de medición fuera del repositorio y anotar en la spec solo los conteos descritos en el [plan](plan.md#medición-en-los-kardex-locales-autorizada-por-el-usuario-el-2026-10-30).
