# Decisión 02. Un json por línea en todos los registros

Fecha: 29 de octubre de 2026.

Se aprueba la decisión propuesta en `docs/specs/02_run_corpus.md`: los dos programas que hablan con el modelo guardan la información del mismo modo, un json por línea. El programa de la especificación 01 ya lo hace con `data/registry.json`, según la decisión 01. El programa que recorre el corpus lo hará igual con sus dos ficheros:

1. `labelled/result_corpus.jsonl`. Una línea por reseña, con su número, su local, las estrellas, los juicios del modelo si la respuesta era válida, si la forma era correcta, los avisos, lo que tardó y el resto de campos que describe la especificación.
2. `labelled/errors_corpus.jsonl`. Solo las reseñas que fallaron, con el mismo contenido.

Motivo: con un json por línea los ficheros se pueden leer igual, cortar por la mitad si se rompe una llamada y retomar sin perder lo anterior. Un registro con sangría obliga a leer el fichero entero para añadir una línea, y en un recorrido largo eso es frágil.

Esta decisión no introduce nada nuevo respecto a la decisión 01: la confirma y la extiende a los dos ficheros nuevos. La especificación 01 no se toca, porque su formato ya quedó decidido así.

El código del programa que recorre el corpus todavía no se ha programado. Michel ha pedido dejar la decisión hecha; la programación se pedirá aparte.
