# Especificación 03. Medir el modelo contra tus marcas

Estado: aprobada el 1 de noviembre de 2026. La decisión está en `docs/decisions/05_measure_against_marks.md`. Dos cambios sobre el texto original: el programa es `src/measure.py` (nombres de fichero en inglés, como en la especificación 02) y el resultado va a `labelled/result_marked.jsonl`, porque `labelled/result.jsonl` ya existe con datos de la versión antigua contaminada por la trampa que esta especificación corrige.

## Para qué existe

Este programa es el examen. Coge las reseñas que tú has marcado a mano, se las pasa al modelo y compara lo que devuelve el modelo con lo que marcasted tú. Con eso se sabe si el modelo sirve, y se puede comparar un prompt contra otro o un modelo contra otro.

Sin este programa no hay forma de decir si el proyecto funciona. Los números que salen de aquí son los que se publican en el README. Por eso la comparación tiene que ser siempre la misma: mismas reseñas, mismo prompt, misma manera de contar. Si se cambia una de las tres, los números no se pueden comparar con los anteriores.

## Qué recibe

- **La hoja marcada a mano.** `labelled/reviews_to_label.json`. Es una lista de 20 reseñas. Cada una tiene numero, local, estrellas, texto, valoraciones (tu lista de juicios) y marcada (verdadero o falso). Solo se usan las que tienen `marcada` en verdadero. Ahora mismo las 20 lo están, con 44 juicios en total.
- **El mismo prompt y la misma configuración de modelo** que el programa de la especificación 01. Es importante que sea el mismo prompt que el de la extracción. Si no, se está midiendo otra cosa.
- Nada por línea de comandos. Se lanza y ya.

## Qué devuelve

1. **`labelled/result_marked.jsonl`.** Un json por línea, una línea por reseña. Campos: numero, local, estrellas, mias (tus juicios), del_modelo (los del modelo), avisos (problemas de forma), comparacion (aciertos, inventadas, omitidas), respuesta_cruda, milisegundos, modelo, prompt y fecha. Si se corta, al volver a lanzarlo salta las reseñas que ya están en este fichero.
2. **Por pantalla, al final, un resumen:**
   - Reseñas medidas.
   - Juicios tuyos y juicios del modelo.
   - Aciertos, contando tema y tono.
   - Precisión: de lo que saca el modelo, cuánto está bien.
   - Recuerdo: de lo que hay en tus marcas, cuánto encuentra.
   - Avisos de forma.
   - Reseñas que el modelo dejó vacías sin serlo.
   - Lo que más inventa y lo que más se deja, por tema y tono.

## Cómo se compara

La comparación es por pareja de tema y tono. No se compara el trozo. Es decir, si tú marcaste `comida / negativo` y el modelo devuelve `comida / negativo` con otro trozo, cuenta como acierto. El trozo se revisa aparte, como aviso de forma.

El conteo es por número de veces. Si una reseña tiene dos juicios `comida / negativo`, cuenta dos. Se usan dos contadores: uno con tus parejas y otro con las del modelo. Los aciertos son la intersección. Las inventadas son lo que está en el modelo y no en tus marcas. Las omitidas son lo que está en tus marcas y no en el modelo.

La precisión se calcula dividiendo los aciertos entre el total de juicios del modelo. El recuerdo, dividiendo los aciertos entre el total de tus juicios. Si el total es cero, se enseña `no aplica` en vez de dividir por cero.

## Cómo funciona, paso a paso

1. Lee la configuración y el prompt. Si falta algo, para.
2. Carga la hoja. Filtra las reseñas con `marcada` en verdadero. Si no hay ninguna, para y lo dice.
3. Mira si `labelled/result.jsonl` existe. Si existe, apunta los números ya hechos.
4. Para cada reseña pendiente: prepara el mensaje, llama al modelo, limpia la respuesta, intenta leerla como lista. Si no se puede, guarda la lista vacía y un aviso. Si se puede, revisa cada juicio: tema válido, polaridad válida y trozo presente en la reseña. Los problemas se guardan como avisos, pero los juicios se conservan para comparar.
5. Compara tus juicios con los del modelo y guarda la línea.
6. Al final, recorre todas las líneas de las reseñas pedidas y suma los totales. Enseña el resumen.

## Línea de comandos

```
python3 src/measure.py
```

No tiene opciones. Siempre mide la hoja entera.

## Lo que no hace

- No cambia el prompt ni el modelo. Usa el que le digan.
- No corrige la hoja marcada a mano. Solo la lee.
- No compara trozos. Compara tema y tono. El trozo solo genera avisos.
- No borra resultados anteriores. Si una reseña ya está medida, la salta.
- No decide si el proyecto vale. Da números. La decisión es tuya.

## Cómo se comprueba que funciona

Con un servidor falso y una hoja de prueba de tres reseñas.

1. **Caso sencillo.** Una reseña con dos juicios tuyos. El modelo devuelve uno que coincide y otro que no. La línea guarda un acierto, una inventada y una omitida. La precisión y el recuerdo se pueden calcular a mano y tienen que coincidir.
2. **Respuesta mal formada.** El modelo devuelve texto que no es una lista. La línea guarda `del_modelo` vacío y un aviso. No se cae.
3. **Retomar.** Se lanza, se corta, se vuelve a lanzar. No repite las reseñas que ya están en el fichero.
4. **Trozo inventado.** El modelo devuelve un juicio con un trozo que no está en la reseña. El juicio cuenta para la comparación, pero se apunta el aviso.
5. **Hoja sin marcar.** Ninguna reseña con `marcada` en verdadero. El programa para con un mensaje claro.

## Dependencias

Solo la librería estándar de Python. Importa el programa de la especificación 01. Nada que instalar.

## Trampa de la versión antigua que hay que corregir

El programa antiguo leía el prompt uno, pero apuntaba en el resultado el nombre del prompt tres. Es decir, el fichero de resultados decía que se había usado un prompt que no era el que se usó. Eso hace que los números no se puedan reproducir con confianza. La versión nueva tiene que usar una única ruta de prompt y apuntar exactamente la que usó. Si no se corrige, cualquier comparación futura arrastra el error.

## Cómo se trabaja esta especificación

- El trabajo va en la rama `spec-03-measure-against-marks`, nunca directamente sobre `main`.
- Se abre una pull request contra `main` cuando la rama está lista.
- GitHub ejecuta las pruebas solo, en cada pull request. Si alguna falla, no se fusiona.
- Solo se fusiona con las pruebas en verde y con el visto bueno de Michel.
- El método completo, con los comandos, está en `docs/working-method.md`.
