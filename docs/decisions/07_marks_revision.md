# Decisión 07. Revisión de las marcas tras la primera medida

Fecha: 1 de noviembre de 2026.

Se revisan las 16 parejas que el modelo devolvió y que no estaban en la hoja marcada a mano. Trece son juicios de verdad: doce se añaden como marcas nuevas y una corrige una marca existente. Las otras tres se rechazan.

Motivo: la primera medida con el contador por pareja daba 16 parejas «inventadas». Al leerlas una a una, la mayoría eran juicios reales que Michel no había marcado, no invenciones del modelo. La hoja, no el modelo, estaba incompleta. Antes de corregir nada se comprobó que los trozos del modelo son literales, y por eso se pueden usar como texto de la marca.

## Lo que cambia

- Doce marcas nuevas: reseña 65 (servicio positivo, comida positivo, precio negativo), 68 (espera positivo), 72 (precio positivo), 81 (ambiente positivo y ambiente negativo), 88 (servicio positivo), 116 (ambiente mixto), 164 (comida positivo), 166 (servicio negativo) y 170 (comida positivo).
- Una corrección en la reseña 147: la marca de servicio pasa de positivo a mixto, con el trozo que lleva las dos caras.
- La hoja pasa de 44 a 56 juicios.
- En la reseña 65 se aceptan dos juicios que Michel había puesto en duda al principio y luego reconoció: «al menos eran muy majos» es servicio positivo, y «una gilda que estaba buena» es comida positivo. La rúbrica manda juzgar cada valoración por separado y no el ánimo general de la reseña.

## Efecto en la medida

Con las mismas respuestas del modelo, sin volver a llamarlo:

- Precisión por pareja: 0,692 pasa a 0,942.
- Recuerdo: 0,818 pasa a 0,875.
- Parejas inventadas: 16 pasan a 3.
- Parejas omitidas: 8 pasan a 7.

## Límite de esta revisión

Las 16 parejas se revisaron viendo la respuesta del modelo, no a ciegas. Eso puede ajustar la hoja hacia el modelo y subir la nota. Para una medida limpia hace falta marcar reseñas nuevas sin ver al modelo. Queda pendiente y se dirá así en el README.

## Comprobado el 1 de noviembre de 2026

Los 56 trozos de la hoja aparecen literalmente en su reseña, incluidos los que unen dos fragmentos con « ... ». Las pruebas del proyecto siguen en verde.

Se guardan copias de la hoja y del resultado anteriores a esta revisión en `labelled/`, con la fecha en el nombre. Esos ficheros no están en el repositorio.
