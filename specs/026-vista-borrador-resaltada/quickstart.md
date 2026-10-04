# Quickstart: validar F32 · Vista del borrador con errores resaltados

## Requisitos

- Entorno de `specs/001-base-devsecops/quickstart.md`. LibreOffice (`soffice`) en `PATH` para los
  tests del adaptador.
- PostgreSQL de pruebas configurado (variables `POSTGRES_*`).
- Solo datos ficticios.

## Pruebas automáticas

```bash
python -m pytest tests/test_ubicacion_pagina.py
python -m pytest tests/test_paginas_adaptador.py
python -m pytest tests/test_vista_borrador.py
python -m ruff check .
python -m ruff format --check .
python -m pytest --cov --cov-report=term
```

Resultado esperado:

- Núcleo: un valor en un segmento, un valor partido en dos segmentos de la misma línea, un valor que
  cruza dos líneas, varias apariciones, un valor que es parte de una palabra (proporción), un valor
  ausente (lista vacía) y la misma entrada dos veces (resultado idéntico).
- Adaptador: un `.docx` ficticio con un DNI ficticio en la página 2 produce un segmento con ese
  texto en la página 2.
- Vistas: 302 sin sesión; 403 sin rol; 404 con otro expediente, otro borrador u otra corrida; JSON
  `LISTA` con la marca de la observación ficticia; PNG con `Cache-Control: no-store`; `FORMATO`
  para un PDF (Tramo A); `SIN_ORIGINAL` tras eliminar el original; la caché de vista desaparece
  tras `suprimir_texto_expediente`.

## Prueba manual (Tramo A)

1. Crear un expediente ficticio con una minuta y un borrador `.docx` ficticios. El borrador lleva
   un DNI que no coincide (alta), un monto distinto (media) y una errata (baja).
2. Confrontar.
3. Comprobar:
   - El panel "Borrador" muestra "Preparando la vista…" y luego la página 1.
   - Los tres recuadros están en rojo, amarillo y neutro, con borde continuo, discontinuo y
     punteado.
   - Al elegir el DNI en la lista, la vista va a su página y lo destaca; al hacer clic en el
     recuadro amarillo, se selecciona el monto.
   - Al filtrar por "Severidad alta", solo queda el recuadro rojo.
   - Con Tab se llega a los recuadros y con Enter se selecciona la observación.
4. Recargar la página: los recuadros salen en las mismas posiciones (SC-004).
5. Borrar el original del expediente ficticio y recargar: aparece el aviso `SIN_ORIGINAL` y la
   lista sigue funcionando.

## Verificación del 2026-10-02 (máquina de desarrollo, datos ficticios)

- **Entorno**: base aparte `confrontador_f32_demo` en el PostgreSQL local, servidor en el puerto
  8032, y carpetas temporales y de originales fuera del repositorio. La vista la convierte el
  worker: `python manage.py procesar_documentos` después de abrir el resultado.
- **Conversión del `.docx`**: 24 s en el worker. Medidas aparte de LibreOffice: de 12 a 42 s con
  un perfil ya creado y más de 120 s con un perfil nuevo. Por eso la conversión no se hace en la
  petición (research R5).
- **Ubicación (SC-001 y SC-002)**: las 5 observaciones ficticias quedaron marcadas en su página y
  sobre sus palabras (1 de identidad, 3 de regla y 1 lingüística, en 2 páginas), sin recuadros
  falsos. Es un conjunto pequeño: el 95 % de SC-001 debe medirse con los expedientes ficticios de
  referencia antes de cerrar F32.
- **Tiempo (SC-003)**: con la vista preparada, unos 0,1 s el JSON y unos 0,1 s cada página PNG.
- **Interacción**:
  - Elegir en la lista lleva a la página 2 y deja el recuadro a la vista.
  - El clic en un recuadro selecciona su observación y muestra su detalle.
  - El filtro de severidad baja deja solo el recuadro neutro.
  - Dos observaciones sobre el mismo DNI alternan con clics sucesivos.
  - «Ampliar» funciona.
  - La consola queda sin errores.
- **Pendiente de probar**: la severidad media (el conjunto ficticio no generó ninguna; su estilo
  se ve en la leyenda) y la revisión completa de las 10 heurísticas con un digitador.

## Tramo B (solo tras aprobar la constitución 1.8.0)

Repetir el paso 3 con un borrador PDF escaneado ficticio. El recuadro debe caer en la línea del
monto, con un margen lateral de pocos milímetros como máximo.
