# La Comidilla

Coge la reseña de un restaurante y devuelve la lista de juicios que hay dentro: de qué habla (comida, servicio, precio, ambiente, espera), si lo valora bien o mal, y el trozo exacto de la reseña que lo demuestra.

Es una pieza de portafolio de ingeniería de inteligencia artificial aplicada, no un producto. Lo que quiere demostrar, con números, es una cosa concreta: que un modelo bien dirigido saca de las reseñas juicios que una lista de palabras clave no alcanza.

## Qué devuelve

Ejemplo inventado, para no publicar reseñas de terceros:

```json
[
  {"tema": "ambiente", "polaridad": "positivo", "trozo": "El local es precioso y súper tranquilo"},
  {"tema": "comida", "polaridad": "mixto", "trozo": "la tarta de queso, que estaba seca, aunque el café riquísimo"},
  {"tema": "espera", "polaridad": "negativo", "trozo": "Tardaron 40 minutos en tomarnos nota"}
]
```

Tres campos y nada más: el tema, la polaridad y el trozo. El trozo va literal, copiado tal cual, con las faltas si las hay. Eso es lo que permite distinguir «el modelo se equivocó de tema» de «el modelo se lo inventó».

## Estado

- **Terminado:** el extractor (`src/extract.py`), el programa que recorre el corpus (`src/run_corpus.py`), el examen que mide contra las reseñas marcadas a mano (`src/measure.py`), el rival de reglas (`src/rules.py`) y el programa que recalcula la tabla desde los resultados guardados (`src/recount.py`). Todos con sus pruebas, y GitHub las ejecuta en cada cambio.
- **Hecho:** la medida limpia del 2 de noviembre de 2026, sobre 30 reseñas marcadas a ciegas antes de ver ninguna respuesta del modelo.

## Cómo se trabaja aquí

Cada pieza sigue el mismo camino: se escribe la especificación, se propone, se decide y se deja la decisión por escrito, y solo entonces se programa. Cada especificación tiene su rama, cada cambio su pull request, y las pruebas se ejecutan solas antes de fusionar. El detalle está en `docs/working-method.md`.

## Cómo se ejecuta

```
python3 src/extract.py --index 3                  (analiza la reseña número 3)
python3 src/run_corpus.py                         (recorre el corpus entero)
python3 src/rules.py                              (el rival de reglas, sin gastar llamadas)
python3 src/recount.py                            (recalcula la tabla desde los resultados guardados)
python3 -m unittest discover -s tests             (las pruebas, sin gastar llamadas)
```

Solo necesita la librería estándar de Python, nada que instalar. Para llamar de verdad al modelo hacen falta tres datos en el entorno: la dirección, el nombre del modelo y la clave.

## Lo que no está en este repositorio, a propósito

El corpus y la hoja de reseñas marcadas a mano no se publican. Son textos de terceros y una hoja de trabajo personal, así que quedan fuera con el `.gitignore`. Para ejecutar el programa hace falta un corpus propio con esta forma: `[local, estrellas, texto]`.

## Resultados

Medida principal: 30 reseñas marcadas a mano **antes** de ver ninguna respuesta del modelo, con 87 juicios. El modelo es Claude Haiku 5.5 con el prompt `prompt_v4.txt`; el rival de reglas usa el léxico fijo del anexo de la especificación 04. Una sola pasada de cada programa el 2 de noviembre de 2026, sin volver a llamar a nadie. La tabla se recalcula con `python3 src/recount.py`.

| Medida | Modelo | Rival de reglas |
| --- | ---: | ---: |
| Precisión por pareja | 79,8% | 66,7% |
| Recuerdo por pareja | 86,2% | 41,4% |
| F1 por pareja | 82,9% | 51,1% |
| Parejas inventadas | 19 de 94 | 18 de 54 |
| Parejas omitidas | 12 de 87 | 51 de 87 |
| Filas de juicio | 152 | 63 |
| Filas por pareja | 1,62 | 1,17 |
| F1 medio por reseña | 83,1% | 50,8% |
| Precisión por fila | 49,3% | 57,1% |

El modelo encuentra casi el doble de juicios: 75 de 87 frente a 36 de 87. La ventaja de recuerdo es sólida: el intervalo por bootstrap de reseñas va de 34,5 a 54,3 puntos. La de precisión es real pero pequeña, 13,1 puntos, con un intervalo que casi toca el cero (0,1 a 25,7). Contando por fila, el modelo gana en la nota que combina precisión y recuerdo (62,8% frente a 48,0%) y pierde en precisión sola (49,3% frente a 57,1%), porque escribe 152 filas para 94 parejas.

Por tema, contado por pareja y con las marcas como denominador:

| Tema | Modelo | Rival de reglas |
| --- | ---: | ---: |
| Ambiente | 18 de 26 | 7 de 26 |
| Comida | 25 de 25 | 14 de 25 |
| Espera | 5 de 6 | 2 de 6 |
| Precio | 9 de 10 | 4 de 10 |
| Servicio | 18 de 20 | 9 de 20 |

Los fallos del modelo no son invenciones: son discusiones de etiqueta. De sus 19 parejas inventadas, 13 son tres desacuerdos que se repiten: dónde va un juicio cuando el tiempo y el trato se mezclan (4), si un error en la cuenta o una ración pequeña es precio (4), y si una frase con elogio y pega es mixta o son dos marcas (5). La mitad de sus omisiones, 6 de 12, son elogios generales («gran sitio», «muy recomendable») que la hoja cuenta como ambiente y el modelo no se atreve a marcar.

La medida anterior, con 20 reseñas, dio 94,2% de precisión y 87,5% de recuerdo. Esa hoja se revisó después de ver la respuesta del modelo (decisión 07), así que su precisión está inflada: con la hoja de antes de la revisión el modelo sacaba 69,2% y el rival 68,2%. Se queda como medida histórica y no es la que cuenta.

## Esto es AI Engineering, no ML Engineering

Cuatro líneas, para que no haya duda de dónde cae el trabajo:

1. No entrené ningún modelo: usé uno ya entrenado y lo adapté cambiando el prompt cuatro veces; la cuarta es la que aguanta la medida.
2. Construí solo la capa de arriba: los programas que dirigen al modelo y comparan su salida con las marcas, sin sistema propio de entrenamiento ni de servicio.
3. Ese formato no evita el error, lo hace contable: de los 94 juicios que dio, 19 no están en mi hoja, y ninguno es texto inventado, son desacuerdos de etiqueta.
4. Escribí un rival de reglas, sin modelo. Recuerdo es cuántos de mis 87 juicios encuentra: 75 el modelo (86,2%) y 36 el rival (41,4%). Precisión es cuántos de los que escribe están en mi hoja: 79,8% el modelo y 66,7% el rival, 13 puntos de diferencia.

## Dónde está cada cosa

| Carpeta | Qué guarda |
| --- | --- |
| `docs/specs/` | Lo que cada programa tiene que hacer. |
| `docs/proposals/` | Las propuestas, antes de programar. |
| `docs/decisions/` | Las decisiones tomadas, con fecha y motivo. |
| `docs/working-method.md` | La norma de trabajo: ramas, pull requests y pruebas. |
| `src/` | Los programas: extracción, corpus, examen y rival de reglas. |
| `tests/` | Las pruebas. |
| `prompts/` | Las versiones del texto que se manda al modelo. |
| `AGENTS.md` | El contrato de trabajo con cualquier asistente que toque este repositorio. |

## De dónde sale el método

De dos sitios. Del libro *AI Engineering*, de Chip Huyen: la división en tres capas del stack (capítulo 1, «The AI Engineering Stack», p. 59) y la idea de definir la evaluación antes de construir (capítulo 4, *evaluation-driven development*, p. 160). Y de la rúbrica de etiquetado del propio proyecto, que vive fuera del repositorio y es la que fija qué es un juicio y qué no.
