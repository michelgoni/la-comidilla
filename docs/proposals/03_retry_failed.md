# Propuesta 03. Reintentar en `src/run_corpus.py` las reseñas que acabaron con error

Fecha: 1 de noviembre de 2026.

## Qué quiero hacer

Añadir al programa una opción nueva: `--reintentar-fallidas`. Con esa opción puesta, las reseñas cuya línea en `labelled/result_corpus.jsonl` lleva error vuelven a quedar pendientes y se vuelven a pasar. Sin la opción, el programa se comporta como ahora: las salta.

Hoy son 39 reseñas, todas con el error 402 de crédito insuficiente. Si el error fuera otro, la opción funcionaría igual.

## Por qué hace falta

La especificación 02 dice que `labelled/errors_corpus.jsonl` "sirve para volver a pasarlas sin buscar entre todas". Pero el programa no tiene ninguna forma de hacerlo: la memoria de reanudación da por hecha cualquier reseña que tenga línea en el fichero de resultados, tenga error o no. La única salida actual es borrar líneas a mano del fichero, buscando los números en el fichero de errores.

## Cómo funciona, paso a paso, con la opción puesta

1. Al leer el fichero de resultados, solo cuentan como hechas las líneas sin error. Las 39 con error vuelven a la lista de pendientes (dentro del rango `--desde`/`--hasta` que se pida, como siempre).
2. Antes de llamar al modelo, se reescribe `result_corpus.jsonl` quitando las líneas con error de las reseñas que entran en este pase. No se pierde nada: esas líneas ya están copiadas en `errors_corpus.jsonl`.
3. El resto del pase es el de siempre: llamar al modelo con reintentos, revisar la forma y añadir una línea por reseña.
4. Si una reseña vuelve a fallar, el error nuevo se apunta en los dos ficheros, como ahora.

`errors_corpus.jsonl` no se toca nunca: solo se añade. Es el historial de fallos.

## Qué toco

- `src/run_corpus.py`: la memoria de reanudación, una función nueva que quita las líneas con error antes del pase y la opción de línea de comandos.
- `tests/test_run_corpus.py`: pruebas nuevas con el servidor falso.
- `docs/specs/02_run_corpus.md`: añadir la opción a la lista de opciones y al paso a paso.
- El trabajo va en la rama `spec-02-retry-failed` y se fusiona con una pull request contra `main`, como manda `docs/working-method.md`.

## Qué no toco

- El prompt, el modelo, el corpus y la hoja marcada a mano.
- Las 32 reseñas sin error pero con avisos (trozos que no están literales en la reseña). Decisión de Michel del 1 de noviembre: se quedan como están y contarán como lo que son, `forma_correcta` falso, cuando llegue la medición. Esa decisión queda apuntada junto con esta.
- `errors_corpus.jsonl`: nunca se borra ni se reescribe.

## Coste

Cada reseña repuesta gasta una llamada al modelo, más sus reintentos si falla. La opción va apagada por defecto: sin ponerla, el programa no gasta nada nuevo.

## Cómo se comprueba que funciona

Con el servidor falso y un fichero de resultados preparado:

1. Tres líneas: dos sin error y una con error. Con la opción, solo repasa la del error; las otras dos no se repiten.
2. Tras el repase, el fichero tiene una línea por reseña, sin números repetidos.
3. Sin la opción, la línea con error cuenta como hecha y no se repasa nada.
4. Si la reseña repuesta vuelve a fallar, la línea nueva lleva el error y queda apuntada en los dos ficheros.
5. Con `--desde` y `--hasta`, solo se repasan las reseñas con error que caen dentro del rango, y las líneas con error fuera del rango se quedan en el fichero.

## Decisión propuesta, cámbiala si no te vale

Propongo quitar del fichero de resultados las líneas con error cuando se repasan, porque su historial ya vive en `errors_corpus.jsonl`. La alternativa es no quitar nada y dejar números repetidos donde manda la última línea; no la recomiendo porque obliga al programa de medición a desempatar y confunde cuando se lee el fichero a mano.

## Qué necesito de ti

Revisa la propuesta y dime si la apruebas. Si la apruebas, escribo la decisión en `docs/decisions/03_retry_failed.md` (con tu decisión de hoy sobre las 32 reseñas con avisos), actualizo la especificación 02 y hago el cambio en la rama.
