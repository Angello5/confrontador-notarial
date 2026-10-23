# Quickstart · F61 Capa de sentido

Guía técnica de instalación y operación, y guía de uso para el personal de la notaría. Es el componente del manual técnico y del manual de usuario del numeral 3.9 de la Adenda N.° 01.

## 1. Requisitos del servidor

| Parámetro | Valor |
|---|---|
| Servidor | SQLSERVER (Windows Server 2019, 64 GB). No usar NREAESGA: Windows Server 2012 R2 sin soporte. |
| Memoria de la capa | Unos 2,2 GB. Fijar el **tope de memoria de SQL Server** antes de activarla (lo hace el administrador de la notaría). |
| Hilos | `SENTIDO_HILOS=3` (de 6). SQL Server conserva la mitad. |
| Disco | Unos 2,1 GB de modelos ONNX y tokenizadores, y 0,1 GB de spaCy. |
| Red | Ninguna en ejecución (P-09). |

## 2. Instalar las dependencias opcionales

Desde la raíz del ERP, con el entorno del ERP activo:

```bash
python -m pip install --require-hashes --only-binary :all: -r requirements-sentido.txt
python -m pip install --require-hashes --no-deps -r requirements-sentido-modelo.txt
```

`es_core_news_md` tiene licencia GPL-3.0. Requiere revisión legal antes de activar la capa en producción.

## 3. Aprovisionar los modelos

Copiar a la carpeta de modelos (por defecto `~/notaria-modelos/sentido`, o la que indique `SENTIDO_MODELOS_DIR`) los seis archivos del manifiesto `adaptadores/modelos_sentido.toml`:

```text
e5.onnx            e5.tokenizer.json
mdeberta.onnx      mdeberta.tokenizer.json
minilm.onnx        minilm.tokenizer.json
```

Se entregan en el paquete de instalación. Para reproducir la exportación, en un equipo de desarrollo con red y PyTorch: `scripts/exportar_modelos_sentido.py`. Si se vuelven a exportar, las huellas pueden cambiar; entonces se actualiza el manifiesto y se repite la medición de la sección 6.

Verificar las huellas:

```bash
python manage.py verificar_modelos_sentido
```

Un archivo que falta o con otra huella detiene el comando con error, y la capa no lo carga.

## 4. Activar y apagar

En el `.env` del servidor:

```bash
SENTIDO_ACTIVO=1
SENTIDO_MODELOS_DIR=C:\notaria-modelos\sentido
SENTIDO_HILOS=3
```

Aplicar la migración (`python manage.py migrate`) y reiniciar el servidor web y el worker. Conviene el worker continuo, que carga los modelos una sola vez, con prioridad por debajo de lo normal:

```bat
start "worker" /belownormal python manage.py procesar_documentos --continuo
```

**Apagar** (plan de reversión): `SENTIDO_ACTIVO=0` y reiniciar. El ERP vuelve a funcionar exactamente como antes; no hace falta desinstalar nada. Los análisis ya guardados no se borran y vuelven a mostrarse si se reactiva.

## 5. Cómo funciona en el worker

1. El worker extrae los documentos y confronta por reglas, como siempre.
2. Al final de cada vuelta analiza **una** corrida pendiente: la última con resultado de cada borrador de kardex. Las transferencias vehiculares no se analizan.
3. Guarda el resultado en `AnalisisSentido`: anotaciones, versión de los modelos, tiempo y huella. La corrida no cambia.
4. Si faltan modelos, no guarda nada y lo vuelve a intentar en la vuelta siguiente; el log dice qué archivo falta. Si el análisis falla, lo guarda como error; el log no lleva texto de los documentos.

**Supresión (Ley 29733):** `python manage.py suprimir_texto_expediente <código>` también borra las oraciones de las anotaciones de sentido. La huella se conserva.

## 6. Mediciones en la instalación (26/10/2026)

1. **Tiempo:** el tiempo de cada expediente queda en `AnalisisSentido.segundos`. Medir el conjunto de prueba y fijar por escrito el tiempo máximo por expediente (numeral 5.2 b; propuesta: 3 minutos).
2. **Efecto sobre SQL Server:** con el Monitor de recursos, comparar la CPU y el tiempo de respuesta de una consulta habitual con la capa activa y apagada.
3. **P-09:** con el Monitor de recursos (pestaña Red) o `netstat -b`, verificar que el proceso del worker no abre conexiones salientes mientras analiza.
4. **P-01:** procesar dos veces el mismo expediente (borrar su `AnalisisSentido` entre una y otra) y comparar la `huella`.

Referencia en el equipo de desarrollo (Apple M1, 3 hilos): 14 s por proyecto de promedio, 67 s el más largo, y 7 s de carga de los modelos.

## 7. Guía de uso (personal de la notaría)

En la pantalla de confrontación, debajo de las observaciones, aparece la sección **«Sentido frente a la minuta»**.

- **Qué hace:** compara el sentido de cada cláusula del proyecto con la minuta. Avisa cuando el proyecto:
  - dice lo contrario (un «no» que la minuta no tiene);
  - cambia la parte que se obliga;
  - quita o agrega una condición;
  - cambia el tiempo del verbo;
  - trae una cláusula que no está en la minuta;
  - tiene un error de concordancia («los inmuebles descrito»).
- **Cómo leerla:** cada nota muestra lo que **dice la minuta** y lo que **dice el proyecto**, uno junto al otro.
  - **Observación:** los dos modelos ven el cambio. Revise la cláusula antes de la firma.
  - **Para revisar:** lo ve uno solo; es una alerta más débil. Déle una mirada rápida.
- **Qué no hace:** no cambia el documento ni las observaciones de reglas. Los DNI, montos, nombres y la ortografía los siguen revisando las reglas. Es un apoyo, no un reemplazo de la lectura del abogado: el cambio de tiempo verbal es su punto débil (detecta unos 4 de cada 10).
- **Mientras se analiza:** la sección dice «Analizando…» y se actualiza sola. Puede seguir revisando las demás observaciones.
- **Si dice que no está disponible:** avise al administrador del sistema (faltan los modelos en el servidor).
- **En el informe:** al descargar el informe en Word, PDF o Excel, marque o desmarque «Sentido frente a la minuta».
