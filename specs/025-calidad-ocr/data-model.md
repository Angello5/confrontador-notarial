# Datos

`TextoExtraido.calidad`: JSON vacío para históricos; en lecturas nuevas contiene versión y páginas. Cada página identifica método, confianza nullable, motivos de revisión, intentos y cajas en el sistema de coordenadas de la imagen analizada con su transformación. Se conserva junto al texto, con su misma vida útil.

`Corrida.presentacion.calidad_lectura`: resumen por documento/página, sin duplicar cajas ni texto; snapshot para reabrir sin recalcular. No altera la huella de hallazgos existente.

Referencia privada: caso/documento/página/campo/sujeto/rol/bien/moneda/concepto/fecha/valor observado/valor esperado/estado de revisión. Ningún valor esperado se rellena a partir de la salida del motor.
