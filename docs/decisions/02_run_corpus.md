# Decisión 02. Recorrer el corpus entero

Fecha: 1 de noviembre de 2026.

Se aprueba la especificación `docs/specs/02_run_corpus.md` y se implementa en `src/run_corpus.py`, con sus pruebas en `tests/test_run_corpus.py`.

Motivo: Michel pidió implementar la especificación. La propuesta ya describía el programa completo, así que no se añaden reglas nuevas.

Se mantienen las decisiones que ya estaban escritas:

1. Los resultados van a `labelled/result_corpus.jsonl` y los fallos a `labelled/errors_corpus.jsonl`, un json por línea, según la decisión `docs/decisions/02_format_jsonl.md`.
2. Toda la conversación con el modelo la sigue haciendo `src/extract.py`. El programa que recorre el corpus lo importa y no repite la llamada, la limpieza ni la revisión de forma.
3. El fichero se llama `src/run_corpus.py`, en inglés, siguiendo la regla del proyecto. Los comandos de la especificación se actualizan con ese nombre.

Dos detalles que la especificación no fijaba y quedan así:

1. `--reintentos` vale 2 si no se indica otra cosa. Son dos reintentos después del primer intento, tres llamadas como máximo por reseña.
2. El campo con los primeros 2.000 caracteres de la respuesta cruda se llama `respuesta_cruda`, igual que en los resultados anteriores del prototipo.

La comprobación queda en las pruebas: primera pasada, retomar sin repetir, fallo con reintento, reintentos agotados, rango con final excluido y parada sin configuración.
