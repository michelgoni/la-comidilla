# Decisión 06. Contar por pareja en el titular

Fecha: 1 de noviembre de 2026.

Se cambia la forma de contar de la especificación 03 y de `src/measure.py`. La cuenta por pareja pasa a ser el titular. La cuenta por veces se queda, pero aparte, como medida del ruido. Esta decisión sustituye el segundo punto de «Decisión de la misma fecha» de `docs/decisions/05_measure_against_marks.md`.

Motivo: la primera medida con el programa nuevo dio una precisión de 0,340, cuando la medida anterior, con otro modelo y otro prompt, había dado 0,73. Al mirar el detalle, el modelo había devuelto 106 filas para 44 juicios marcados, y muchas eran la misma pareja repetida con trozos distintos: las 106 filas contenían solo 52 parejas. Contando por veces, cada repetición de una pareja correcta se cuenta como inventada. El número medía la verbosidad del modelo, no su acierto, y no se podía comparar con las medidas de octubre, que se calcularon por parejas.

## Lo que cambia

1. `pair_set` y `compare_pairs` cuentan cada pareja una vez por reseña. `compare` sigue igual, por filas.
2. El resumen enseña dos bloques: «Por pareja (lo que decide)» y «Por veces (ruido)», con la repetición al final del segundo, en filas por pareja.
3. «Lo que más inventa» y «lo que más se deja» se cuentan también por pareja, para que coincidan con el titular.
4. Cada línea del resultado guarda los dos números: `comparacion` y `comparacion_parejas`.

## Lo que no cambia

- La hoja marcada a mano, que sigue con 44 juicios y no se toca.
- El prompt. El modelo sigue devolviendo una fila por juicio, como pide el prompt cuatro.
- La comparación no mira el trozo, solo el tema y la polaridad.

## Por qué no las otras dos salidas

- **Re-marcar la hoja** para permitir varias marcas iguales por reseña cuesta horas y hace la medida frágil: exigiría acertar el número exacto de repeticiones, y dos personas no coinciden en cuántas veces se queja una reseña.
- **Pedir al prompt que agrupe** las repeticiones es buena idea más adelante, cuando el producto enseñe la lista al usuario, pero cambia el prompt y obliga a re-medir. No hace falta para arreglar la comparación.

## Comprobado el 1 de noviembre de 2026

Las 53 pruebas pasan. Con el fichero de la medida de ese día, el mismo resultado da 0,340 de precisión por veces y 0,692 por parejas, con un recuerdo de 0,818 en los dos casos.
