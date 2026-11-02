# Decisión 05. Medir el modelo contra tus marcas

Fecha: 1 de noviembre de 2026.

Se aprueba la especificación `docs/specs/03_measure_against_marks.md` con los cambios señalados abajo y se implementa en `src/measure.py`, con sus pruebas en `tests/test_measure.py`.

Motivo: sin un programa que compare lo que el modelo devuelve con lo que Michel marcó a mano no hay forma de decir si el proyecto funciona. Es el examen: sus números son los que se publican en el README.

## Los dos cambios sobre el texto de la especificación

1. **El programa es `src/measure.py`, no `src/medir.py`.** La regla del proyecto dice que los nombres de ficheros van en inglés, como ya hizo `src/run_corpus.py` en la especificación 02. El comando queda `python3 src/measure.py`.
2. **El resultado se guarda en `labelled/result_marked.jsonl`, no en `labelled/result.jsonl`.** Ese fichero ya existe y quedó contaminado por la trampa que la propia especificación 03 manda corregir: el programa antiguo usaba un prompt y apuntaba otro. Si el retomar saltara reseñas apoyándose en esas líneas, las medidas nuevas heredarían datos del prompt equivocado. Se usa un fichero nuevo, paralelo a `labelled/result_corpus.jsonl`, y el antiguo no se borra.

Además se corrige la trampa en el código: el campo `prompt` de cada línea se rellena con el nombre exacto del fichero de prompt que se ha usado (por defecto `prompt_v4.txt`, o el que diga `COMIDILLA_PROMPT`). Un único punto de configuración para prompt y modelo, heredado de `src/extract.py`, que es el mismo programa que usa la extracción.

## Decisión de la misma fecha

- Los avisos no cambian la comparación: los juicios con tema o polaridad no válida, o con trozo no literal, se conservan y cuentan en aciertos, inventadas y omitidas. El trozo solo genera aviso, tal como pide la especificación.
- La comparación cuenta parejas por número de apariciones: si una reseña lleva dos `comida / negativo` marcadas y el modelo devuelve una, cuenta un acierto y una omitida.
- «Lo que más inventa» y «lo que más se deja» sacan una sola pareja de tema y tono por lado, con su número de veces.

La comprobación queda en las pruebas: el caso sencillo calculable a mano, la respuesta mal formada que no cae, el retomar que no repite reseñas, el trozo inventado que cuenta y avisa, y la hoja sin marcar que para con mensaje claro.
