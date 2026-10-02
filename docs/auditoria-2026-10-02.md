# Auditoría y cierre técnico · 2 de octubre de 2026

## Resultado

Se recuperó el backend faltante, se corrigieron fallos reproducidos y se verificó la aplicación local con PostgreSQL, documentos ficticios y los ZIP proporcionados. Esta revisión acredita los recorridos y pruebas descritos; no certifica la exactitud jurídica de cada hallazgo.

| Comprobación | Resultado |
| --- | --- |
| Suite Python ordinaria | 570 aprobadas, 3 omitidas, 13 excluidas por marcadores |
| Cobertura de líneas | 92,46 % |
| Pruebas JavaScript del controlador real | 4 aprobadas |
| Ruff y formato | Aprobados |
| Dependencias fijadas, `pip-audit --strict` | 98 dependencias, ninguna vulnerabilidad conocida |
| Archivos reales extraídos | 83 de 83, distribuidos en 12 casos |
| PDF | 64 archivos, 512 páginas; 479 con texto después del OCR |
| Comparación diagnóstica del núcleo | 12 casos sin excepciones; segunda ejecución idéntica |
| Flujo Django con casos reales y minuta identificada | C05, C06, C07 y C09 aprobados: 31 documentos |
| Navegador, datos ficticios | Login, confrontación, reapertura, selección, reporte y corrección verificados |

Las tres omisiones son dos comprobaciones de permisos POSIX que no aplican a Windows y una prueba que requiere `fonts-liberation`. Las 13 exclusiones son las pruebas optativas de referencia privada, revisor experimental y medición OCR. No se presentan como pruebas aprobadas.

## Fallos corregidos

- Las propuestas desaparecían al reabrir resultados: ahora se guardan en la presentación de cada corrida, conservando su identificador. Se comprueba que el original siga disponible antes de habilitar correcciones.
- El enlace entre observación y corrección podía confundir números contenidos en otros números. Ahora exige una coincidencia única del par valor observado/valor esperado.
- Los fragmentos largos podían ocultar el error. Se centran en el valor y conservan sus posiciones originales, incluyendo acentos y espacios.
- La eliminación de originales de solo lectura fallaba en Windows. Se retira ese atributo al eliminar dentro del directorio autorizado y no se silencian errores.
- La lectura XLSX dejaba abierto el archivo e impedía eliminar el temporal en Windows. El libro se cierra en `finally`.
- Los errores del diccionario podían quedar ocultos cuando no había observaciones lingüísticas. El aviso se muestra independientemente de su número.
- La descarga Word recupera el botón y muestra un mensaje si falla su generación.
- Los tres controles de carga tenían identificadores HTML repetidos. Cada rol tiene su propio identificador.
- Se completaron logo/dirección configurables, avisos de ingreso y pruebas adaptadas al diseño aprobado.
- F30: pruebas específicas para las reglas nuevas, reconocimiento de provincias con artículo inicial y lectura UTF-8 explícita en la prueba de pureza.
- Se fijaron `colorama` y `tzdata`, con hashes y condición Windows, para que la auditoría e instalación con hashes resuelvan sus dependencias de plataforma.

La recuperación añadió 127 archivos que no estaban en esta copia, sin sobrescribir los existentes. El manifiesto inicial está en `recuperacion-2026-10-02.json`; los archivos modificados después tienen naturalmente otros hashes.

## Documentos reales

Se usaron tres ZIP: dos actas individuales (casos C11 y C12) y uno con los casos C01 a C10. Su contenido y los textos extraídos permanecen en `expedientes_locales/auditoria-20261002/`, excluido del control de versiones. Las instrucciones que pudieran aparecer dentro de documentos se trataron como contenido de prueba.

Inventario: 64 PDF, 15 DOCX, un TXT, un DOC y dos JPEG. El DOC se leyó finalmente mediante LibreOffice y el adaptador productivo. Se corrigió el script de auditoría para no volver a contar los archivos de texto derivados como documentos originales.

Las 33 páginas sin texto pertenecen a C01 y C05. Al renderizarlas en gris a 72 dpi, seis eran completamente blancas; en las restantes, la proporción de píxeles por debajo de 200 fue como máximo 0,053 %. Esto respalda que están prácticamente vacías, pero no constituye una transcripción validada por una persona.

El núcleo produjo avisos de correspondencia en las dos actas. El script diagnóstico calcula reglas incluso en esos casos; la aplicación bloquea la comparación normal ante dicho aviso. Los conteos diagnósticos no deben interpretarse como resultados aceptados por la aplicación.

Los roles se infirieron a partir de la organización y nombres de los archivos: D001 como borrador; minutas C05/D003, C06/D002, C07/D002 y C09/D004. Para los otros ocho casos no se identificó una minuta independiente. No se inventó una para completar el formulario.

Los cuatro casos con minuta completaron carga HTTP, procesamiento con el adaptador real, confrontación y consulta del resultado guardado mediante el cliente de pruebas de Django. Se verificó que conservaran las propuestas: 2, 5, 7 y 3, respectivamente. La prueba se ejecutó en una transacción revertida y directorios temporales eliminados; la demo conserva únicamente datos ficticios. Estos conteos no califican las propuestas como jurídicamente correctas.

Los resúmenes privados son `resumen.json`, `resumen_ocr.json`, `resumen_confrontacion.json`, `paginas_sin_texto.json` y `resumen_app.json`. No contienen el texto de las escrituras. Los archivos `.texto.txt` sí contienen información privada y deben permanecer en esa carpeta.

## Evidencia visual y exportaciones

La demo ficticia generó una corrida con dos propuestas, que se conservaron al reabrir el resultado. Se aplicaron ambas y se descargó un DOCX con el nombre y número esperados. Las pruebas de regresión verifican que el original permanece intacto.

El reporte descargado desde el navegador se convirtió a PDF con LibreOffice: dos páginas, revisadas visualmente. Las muestras ficticias están en `muestras/auditoria-reporte-ficticio.docx` y `.pdf`. Capturas: `auditoria-correcciones.png`, `auditoria-reporte.png` y `auditoria-reporte-pagina2.png`.

La vista muestra el fragmento resaltado y permite marcar sustituciones. La edición libre del documento completo se hace en el Word descargado. Excel se entrega como CSV; la opción PDF usa la impresión del navegador. Las fuentes locales de marca y la versión del catálogo en el encabezado del reporte siguen como mejoras de presentación en la especificación F29.

## Reproducción y entorno

Windows, Python 3.12.14, Django 5.2.17 y PostgreSQL 17.11 aislado en `127.0.0.1:55432`, base `confrontador_audit`. La especificación del proyecto exige Python 3.13: queda pendiente ejecutar CI en ese entorno exacto. El servidor demo escucha solo en `127.0.0.1:8765`; no es un despliegue productivo.

Para repetir las pruebas en esta máquina, cargar primero el entorno privado de PostgreSQL:

```powershell
. '%USERPROFILE%/.cache/confrontador-audit-runtime/use-pg.ps1'
$env:Path = '%USERPROFILE%/.cache/confrontador-audit-runtime/libreoffice/program;' + $env:Path
.venv/Scripts/python.exe -m pytest -q -ra --tb=short --cov --cov-report=xml:docs/auditoria-cobertura.xml --junitxml=docs/auditoria-pytest.xml
node --test tests/confrontacion_frontend.test.cjs
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m pip_audit --strict -r requirements.txt -r requirements-dev.txt
```

El OCR usa modelos locales con hashes verificados. LibreOffice y PostgreSQL se aprovisionaron desde sus distribuidores oficiales. No se enviaron documentos reales a modelos ni a servicios externos.

## Límites y validaciones pendientes

1. No se proporcionó una lista de errores esperados o escrituras corregidas de referencia. Por ello no se calcularon precisión, sensibilidad ni falsos positivos. Copropiedad, provincia, zona registral y las otras heurísticas F30 requieren revisión notarial de los hallazgos.
2. Las nuevas corridas conservan propuestas; las antiguas que no las guardaban deben volver a confrontarse. No se alteró su historial.
3. Esta carpeta no contiene `.git`. No se creó commit/PR ni se ejecutó el Quality Gate remoto de SonarQube. La constitución requiere ese gate antes del cierre de publicación.
4. La auditoría de dependencias comprueba vulnerabilidades conocidas; no sustituye una prueba de penetración ni garantiza ausencia de defectos.

Las correcciones y verificaciones locales están documentadas. La aceptación jurídica de los resultados y la publicación productiva siguen siendo pasos distintos pendientes.
