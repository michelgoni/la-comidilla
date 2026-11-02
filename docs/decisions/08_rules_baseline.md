# Decisión 08. El rival sin modelo

Fecha: 2 de noviembre de 2026.

Se aprueba la especificación `docs/specs/04_rules_baseline.md` y se implementa en `src/rules.py`, con sus pruebas en `tests/test_rules.py`.

Motivo: si unas listas de palabras escritas a mano una vez igualan o superan al modelo, el modelo no aporta nada y el proyecto no sigue. El rival es además la referencia barata: corre en milisegundos y no gasta dinero, así que se puede lanzar cada vez que cambie algo del examen.

## Los cambios sobre el texto de la especificación

1. **El programa es `src/rules.py`, no `src/reglas.py`.** La regla del proyecto dice que los nombres de ficheros van en inglés, igual que ya hizo la decisión 05 con `src/measure.py`. El comando queda `python3 src/rules.py`. El resto del programa (mensajes por pantalla, campos del resultado) sigue en español, como pide la especificación.
2. **El texto se busca sin distinguir mayúsculas de minúsculas.** Las frases empiezan con mayúscula («Rico», «Estaba buen») y las listas del anexo están escritas en minúscula. Si la búsqueda distinguiera el caso, la primera palabra de cada frase se perdería. Se valida abajo con el examen.
3. **La precisión y el recuerdo se suman sobre todas las reseñas** (las parejas de cada reseña se acumulan y se divide al final), no se hace la media de reseña por reseña. Es la misma cuenta del titular de `src/measure.py`, para que los dos programas se puedan comparar sin convertidores.
4. **«Cuando coincide el tema, el tono» se cuenta por tema y en total**: el tono coincide en una reseña y tema concretos cuando, mencionando los dos ese tema, alguno de los tonos con que lo marca cada uno aparece en los dos.

## Resultado de la medida

El programa recalcula `labelled/result_rules.json` cada vez que corre. En la corrida de aprobación salió:

- Parejas tuyas: 56 | parejas del programa: 44 | aciertos: 35
- Precisión: 0,795 | recuerdo: 0,625
- Líneas de juicio del programa: 57

Comprobación contra los números publicados: las 57 filas de `del_modelo` salieron **idénticas, fila por fila**, a las del fichero que produjo la versión anterior del programa con el mismo léxico. La única diferencia del fichero nuevo está en las marcas (`mias`) de 10 reseñas, exactamente las que cambió la revisión de la hoja (decisión 07): el programa anterior se midió contra la hoja vieja. Mostraba al rival peor de lo que es, que es justo lo que la especificación manda corregir.

## Lo que no cambia

- El léxico del anexo. Se escribe una vez y no se ajusta mirando las marcas; si se cambia, se vuelve a medir y se anota aquí.
- La hoja marcada a mano, que no se toca.
- El modelo y su prompt, que no participan en este programa ni en esta medida.
