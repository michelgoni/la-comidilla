# Propuesta 05. Integridad de los resultados y medida limpia

Estado: aprobada el 2 de noviembre de 2026. La decisión está en `docs/decisions/09_results_integrity.md`. Fecha de la propuesta: 2 de noviembre de 2026.

## Para qué existe

El análisis del 2 de noviembre recontó los números publicados en el README y en la decisión 08. **Los números son correctos**, pero el análisis encontró tres problemas que no son de cálculo: el fichero de resultados se reescribió, el examen se corrigió mirando al modelo y la cuenta publicada no es la única posible. Esta propuesta arregla el papeleo y define la medida limpia que falta.

## Lo que se ha verificado

- `labelled/result_marked.jsonl` tiene 20 entradas, una por reseña marcada, con las 56 marcas actuales.
- Los totales salen: modelo 49 aciertos, 52 parejas, precisión 0,942, recuerdo 0,875, 3 inventadas, 7 omitidas, 106 filas, 2,04 por pareja, tono 43 de 45.
- Los del rival: 35 aciertos, 44 parejas, 0,795, 0,625, 9 inventadas, 21 omitidas, 57 filas, 1,30 por pareja, tono 31 de 34.
- Los 106 trozos del modelo y los 57 del rival son literales.
- Las 68 pruebas pasan.

## Problema 1. El fichero de resultados se reescribió

La fecha de las 20 entradas es del 1 de noviembre a las 19:31, antes de la revisión de la hoja. El backup `result_marked.backup-2026-11-01.jsonl` tiene 44 marcas; el fichero actual tiene 56, y las 10 reseñas que difieren son exactamente las de la decisión 07. Además, ninguna entrada guarda `comparacion_parejas`, campo que escribe `measure.py:180` y que exige la decisión 06.

Efecto: los números se pueden recalcular (yo lo he hecho), pero el fichero ya no prueba qué se midió, y `measure.py:361` saltará esas 20 reseñas para siempre.

## Problema 2. El examen se corrigió mirando al modelo

De las 16 parejas que el modelo dijo y no estaban en la hoja, se aceptaron 13 (12 nuevas y 1 corrección). Salieron del modelo, así que el modelo las acierta por construcción: 13 de 13, frente a 6 de 13 del rival.

Efecto medido, sobre la hoja anterior del backup: modelo 69,2% de precisión y 81,8% de recuerdo; rival 68,2% y 68,2%. Sobre la hoja revisada: 94,2% y 87,5% frente a 79,5% y 62,5%. La ventaja de precisión pasa de 1,0 puntos a 14,7.

## Problema 3. La cuenta publicada no es la única

Por pareja, F1 90,7% frente a 70,0%. Por fila, F1 60,5% frente a 61,9%: gana el rival. La cuenta por pareja le quita al modelo el 51% de sus filas y al rival el 23%, así que premia al programa verboso. Es defendible (la hoja está marcada por pareja), pero hay que publicarla como una elección, no como el único número.

## Cambios que se proponen

### 1. README, ya corregido en la rama `spec-04-rules-baseline`

Cuatro afirmaciones que no se seguían de los números: la fecha de la medida, "encuentra 14 parejas más", "el tono lo aciertan casi igual" y el "ruido". Se añade la comparación con la hoja anterior y la nota de que las dos columnas de la tabla por tema no comparten base. Números sin tocar.

### 2. Un programa que recalcule la tabla: `src/recount.py`

Hoy la tabla se calcula a mano. La columna por tema del modelo no la imprime ningún programa del repo (`rules.py:195` solo la calcula para el rival). Se propone un programa que lea la hoja y los dos ficheros de resultados y saque, sin llamar al modelo y sin escribir nada:

- la cuenta por pareja y la cuenta por fila, con aciertos, inventadas y omitidas;
- el F1 por reseña y la media;
- la tabla por tema contada por pareja, con las marcas como denominador;
- la versión de la hoja que se ha usado (hash).

Criterio de aceptación: reproduce exactamente los números publicados hoy. Si no los reproduce, el programa está mal.

### 3. La hoja viaja con el resultado

`measure.py` guardará en cada línea el hash del fichero de la hoja. Regla nueva: **un fichero medido no se parchea nunca**. Si cambia la hoja, se escribe otro fichero y el anterior se queda como histórico. El fichero actual no se toca; queda documentado como anterior al contador por parejas.

### 4. Definición de mixto, para la rúbrica

Texto propuesto: *mixto solo cuando la misma frase lleva las dos caras del mismo tema y no se pueden separar sin partir la frase. Si las dos caras están en frases distintas, son dos marcas, una positiva y una negativa.*

Regla añadida: **dos marcas no pueden solaparse en el mismo tema**. La reseña 116 tiene la misma frase marcada como positivo y como mixto: hay que quedarse con una.

Efecto en la métrica, tres opciones:

- **a)** Canonizar mixto como positivo más negativo. Modelo 98,2% y 93,1%; rival 84,1% y 63,8%.
- **b)** Publicar las dos cuentas, con y sin canonizar. Es lo que recomiendo: no esconde la decisión y no obliga a elegir ahora.
- **c)** Dejarlo como está y declarar que mixto es una etiqueta aparte.

### 5. La medida limpia

- **Muestra:** 30 a 40 reseñas del corpus que no estén entre las 20 actuales. Se eligen al azar con una semilla escrita en la decisión.
- **A ciegas:** la hoja se marca y se cierra antes de ejecutar nada. Michel no ve la respuesta del modelo hasta que la hoja está cerrada.
- **Congelado:** prompt `prompt_v4.txt`, modelo `claude-haiku-5-5`, léxico del anexo de la especificación 04. No se toca nada de eso entre la medida del modelo y la del rival.
- **Una pasada por programa.** Del modelo se guarda la respuesta cruda entera, sin el tope de 2000 caracteres.
- **Se publica:** cuenta por pareja, cuenta por fila, F1 por reseña, intervalo por bootstrap de reseñas, tabla por tema con denominador común, y el acuerdo entre anotadores (kappa) en 10 de las reseñas.
- **Las 20 actuales no se tiran:** quedan como medida histórica, con su fecha.

## Lo que no se toca

El corpus, el léxico, el prompt, el modelo, las 20 reseñas marcadas y los ficheros ya medidos.

## Qué decide Michel

1. Aprueba o corrige la definición de mixto y la regla de no solapar trozos.
2. Elige la opción de métrica (a, b o c). Recomiendo b.
3. Fija el tamaño de la muestra nueva y si quiere segundo anotador.

Decidido el 2 de noviembre de 2026: la regla de mixto, tal como está escrita; la opción b para la métrica; 30 reseñas nuevas, sin segundo anotador por ahora. El detalle está en `docs/decisions/09_results_integrity.md`.

Con eso queda escrito. La medida limpia arranca cuando la hoja nueva esté marcada y cerrada.
