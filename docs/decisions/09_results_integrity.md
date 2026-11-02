# Decisión 09. Regla de mixto, integridad de los resultados y arranque de la medida limpia

Fecha: 2 de noviembre de 2026.

Sale de la propuesta `docs/proposals/05_results_integrity.md` y de las decisiones que Michel tomó en conversación el mismo día.

## 1. Regla de mixto (la decide Michel)

Texto, con sus palabras: **mixto solo si las dos caras están en la misma frase.**

Consecuencias:

- Si las dos caras están en frases distintas, son dos marcas, una positiva y una negativa.
- Dos marcas no pueden solaparse en el mismo tema. Si la misma frase aparece marcada dos veces, se queda una.
- Un gusto personal no es una queja del local. «Me hubiera gustado que fueran más picantes» habla del paladar de quien escribe, no del producto, y no cambia la polaridad.
- Un error en la cuenta no es un juicio de precio. Cobrar de más o no saber explicar el ticket es servicio: el precio solo se marca cuando el autor dice que el sitio es caro o barato.

Se aplica a la hoja nueva, la de la medida limpia. La hoja actual no se toca, por el motivo del punto 2.

## 2. La hoja actual no se revisa otra vez

Motivo: aplicar la regla a las reseñas 116 y 164 cambiaría dos marcas después de ver las respuestas del modelo, otra vez a favor del modelo. Ya pasó una vez (decisión 07) y no se repite.

Queda documentado el efecto que habría tenido, para que conste: la hoja pasaría de 56 a 55 marcas; el modelo daría 96,2% de precisión y 90,9% de recuerdo (hoy 94,2% y 87,5%), y el rival 75,0% y 60,0% (hoy 79,5% y 62,5%).

Las 20 reseñas actuales se quedan como están y se publican como medida histórica, con su fecha y su revisión.

## 3. Se publican las dos cuentas y las dos lecturas de mixto

- Cuenta por pareja, que es el titular, y cuenta por fila, que mide la repetición.
- Con mixto estricto (mixto solo casa con mixto) y con mixto canónico (mixto cuenta como positivo y negativo a la vez).

Números actuales, mixto estricto: 94,2% y 87,5% el modelo, 79,5% y 62,5% el rival. Con mixto canónico: 98,2% y 93,1% el modelo, 84,1% y 63,8% el rival.

Motivo: la cuenta por pareja premia al programa que repite, y la estricta castiga el empaquetado de la polaridad. Publicar las dos no esconde ninguna de las dos cosas.

Se cambia además la etiqueta «por veces (ruido)» por «por veces (repetición)» en `src/measure.py` y en el README: las filas repetidas no son copias, cada una cita un trozo distinto de la reseña.

## 4. Un fichero medido no se parchea

`src/measure.py` guarda en cada línea del resultado el campo `sheet_version`, el sha256 del fichero de la hoja que se usó. Así cada resultado dice contra qué examen se midió.

Regla: si la hoja cambia, se escribe un fichero de resultados nuevo. El anterior no se reescribe ni se completa a mano.

El fichero actual se queda como está, con su `fecha` del 1 de noviembre y sin `comparacion_parejas`. Está documentado en el README.

## 5. `src/recount.py`, el programa que recalcula la tabla

Hoy la tabla del README se calcula a mano, y la columna por tema del modelo no la imprime ningún programa. `src/recount.py` lee la hoja y los dos ficheros de resultados guardados y saca:

- la cuenta por pareja y la cuenta por fila, con aciertos, inventadas y omitidas;
- el F1 por reseña y la media;
- la tabla por tema contada por pareja, con las marcas como denominador;
- el sha256 de la hoja usada;
- un aviso cuando las marcas guardadas en un resultado no coinciden con la hoja.

No llama a ningún modelo y no escribe ningún fichero.

Criterio de aceptación: reproduce los números publicados (49/52/56, 3 inventadas y 7 omitidas en el modelo; 35/44/56, 9 y 21 en el rival) y coincide con los totales de `measure.py`.

## 6. Medida limpia: 30 reseñas nuevas, a ciegas

- **Muestra:** 30 reseñas de `corpus_reviews.json` que no estén entre las 20 actuales, con 150 caracteres o más. Cuotas por estrellas: 13 de 5, 6 de 4, 4 de 3, 3 de 2 y 4 de 1. Semilla 20261102. La lista está en `labelled/reviews_blind.json`, con las valoraciones vacías.
- **A ciegas:** Michel marca la hoja y la cierra antes de ejecutar nada. No ve la respuesta del modelo hasta que esté cerrada.
- **Congelado:** prompt `prompt_v4.txt`, modelo `claude-haiku-5-5`, léxico del anexo de la especificación 04. No se toca nada de eso entre las dos medidas.
- **Una pasada por programa.** La respuesta cruda se guarda entera.
- **La hoja se elige por entorno, no tocando código.** `measure.py`, `rules.py` y `recount.py` leen `COMIDILLA_SHEET` para la hoja, `COMIDILLA_RESULT` para el resultado del modelo y `COMIDILLA_RULES` para el del rival. Sin esas variables usan los ficheros de siempre, así que la medida histórica no se toca.
- **Se publica:** cuenta por pareja, cuenta por fila, F1 por reseña, intervalo por bootstrap de reseñas (no de parejas), tabla por tema por pareja, y las dos lecturas de mixto.
- Si Michel prefiere 40 reseñas, se añaden 10 antes de empezar a marcar. A partir de ahí, la hoja no se toca.

## Lo que no cambia

El corpus, el léxico, el prompt, el modelo, las 20 reseñas marcadas y los ficheros ya medidos.

## Comprobado el 2 de noviembre de 2026

Las 68 pruebas pasan, 15 de ellas nuevas en `tests/test_recount.py`. El programa reproduce los números publicados y coincide con los totales de `measure.py`.
