# Decisión 03. Reintentar las reseñas que acabaron con error

Fecha: 1 de noviembre de 2026.

Se aprueba la propuesta `docs/proposals/03_retry_failed.md` y se implementa en `src/run_corpus.py` con la opción `--reintentar-fallidas`, con sus pruebas en `tests/test_run_corpus.py`.

Motivo: la primera corrida del corpus dejó 39 reseñas con error 402 (crédito insuficiente). El programa las daba por hechas y no había forma de volver a pasarlas sin borrar líneas a mano.

Queda así:

1. Sin la opción, el programa se comporta como hasta ahora: cualquier reseña con línea en el fichero de resultados cuenta como hecha y se salta.
2. Con la opción, las líneas con error no cuentan como hechas: esas reseñas vuelven a la lista de pendientes, dentro del rango que se pida.
3. Antes del pase, se quitan del fichero de resultados las líneas con error de las reseñas que se repasan. No se pierde nada: el historial de fallos vive en `labelled/errors_corpus.jsonl`, que nunca se borra ni se reescribe, solo se añade.
4. Si una reseña repetida vuelve a fallar, el error nuevo se apunta en los dos ficheros, como siempre.

Decisión de Michel de la misma fecha, apuntada aquí: las 32 reseñas sin error pero con avisos (trozos que no están literales en la reseña) no se repasan. Se quedan como están y contarán como lo que son, `forma_correcta` falso, cuando llegue la medición de la especificación 03.

La especificación `docs/specs/02_run_corpus.md` se actualiza con la opción nueva.

La comprobación queda en las pruebas: repasar solo las fallidas, no repasar nada sin la opción, el fallo repetido deja una sola línea y hace crecer el fichero de errores, y las fallidas fuera del rango se quedan como están.
