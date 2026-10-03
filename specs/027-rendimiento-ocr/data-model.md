# Datos

Sin cambios de esquema ni migraciones.

Informe de lectura por página (F31, guardado en `TextoExtraido.calidad`): misma forma. Cambian sus valores en dos casos:

- Hoja totalmente blanca: `texto` vacío, `metodo` `ocr`, `intentos` 0, `cajas` vacías, `motivos` `["pagina_casi_vacia"]`, `requiere_revision` verdadero.
- Página girada leída en un reintento: `intentos` puede ser menor, `lecturas_divergentes` ya no aparece cuando la lectura original estaba vacía o era escasa, y `transformacion.giro` corresponde al giro con líneas horizontales.

`calidad.version` pasa de 2 a 3 en lecturas nuevas.
