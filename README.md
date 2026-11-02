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

- **Terminado:** el extractor (`src/extract.py`), el programa que recorre el corpus (`src/run_corpus.py`), el examen que mide contra las reseñas marcadas a mano (`src/measure.py`) y el rival de reglas (`src/rules.py`). Todos con sus pruebas, y GitHub las ejecuta en cada cambio.
- **Pendiente:** una medida limpia sobre reseñas nuevas marcadas a ciegas. La hoja actual se revisó después de ver la primera respuesta del modelo.

## Cómo se trabaja aquí

Cada pieza sigue el mismo camino: se escribe la especificación, se propone, se decide y se deja la decisión por escrito, y solo entonces se programa. Cada especificación tiene su rama, cada cambio su pull request, y las pruebas se ejecutan solas antes de fusionar. El detalle está en `docs/working-method.md`.

## Cómo se ejecuta

```
python3 src/extract.py --index 3                  (analiza la reseña número 3)
python3 src/run_corpus.py                         (recorre el corpus entero)
python3 src/rules.py                              (el rival de reglas, sin gastar llamadas)
python3 -m unittest discover -s tests             (las pruebas, sin gastar llamadas)
```

Solo necesita la librería estándar de Python, nada que instalar. Para llamar de verdad al modelo hacen falta tres datos en el entorno: la dirección, el nombre del modelo y la clave.

## Lo que no está en este repositorio, a propósito

El corpus y la hoja de reseñas marcadas a mano no se publican. Son textos de terceros y una hoja de trabajo personal, así que quedan fuera con el `.gitignore`. Para ejecutar el programa hace falta un corpus propio con esta forma: `[local, estrellas, texto]`.

## Resultados

Medido el 2 de noviembre de 2026 sobre las 20 reseñas marcadas a mano, que suman 56 juicios. El modelo es Claude Haiku 5.5 con el prompt `prompt_v4.txt`; el rival de reglas usa el léxico fijo del anexo de la especificación 04. La comparación sale de los resultados ya guardados: no se ha vuelto a llamar al modelo.

| Medida | Modelo | Rival de reglas |
| --- | ---: | ---: |
| Precisión por pareja | 94,2% | 79,5% |
| Recuerdo por pareja | 87,5% | 62,5% |
| Parejas inventadas | 3 de 52 | 9 de 44 |
| Parejas omitidas | 7 de 56 | 21 de 56 |
| Filas de juicio | 106 | 57 |
| Filas por pareja | 2,04 | 1,30 |

El modelo gana: encuentra 14 parejas más y falla menos. El rival es más silencioso (44 parejas frente a 52), pero de las suyas falla más: 9 inventadas frente a 3, y se deja 21 frente a 7. Cuando los dos pillan el tema, el tono lo aciertan casi igual: 43 de 45 veces el modelo (96%) y 31 de 34 el rival (91%). La diferencia está en detectar el tema, no en juzgarlo.

Por tema (coincide el tema, de las reseñas en que alguno de los dos lo menciona):

| Tema | Modelo | Rival de reglas |
| --- | ---: | ---: |
| Ambiente | 11 de 13 | 10 de 13 |
| Comida | 14 de 14 | 9 de 15 |
| Espera | 4 de 4 | 3 de 5 |
| Precio | 5 de 5 | 4 de 7 |
| Servicio | 11 de 12 | 8 de 12 |

La cuenta por pareja compara cada tema y tono una sola vez por reseña, que es como está marcada la hoja. La cuenta por filas, que castiga la repetición, da 46,2% de precisión al modelo: devuelve 106 filas para 52 parejas distintas, 2,04 por pareja. Ese ruido se mide aparte y no se esconde.

Dos límites que conviene decir en voz alta. La muestra es pequeña: 20 reseñas y 56 parejas, así que un par de aciertos mueve varios puntos. Y las marcas se revisaron después de ver la primera respuesta del modelo, así que la nota puede estar algo alta; para una medida limpia hacen falta reseñas nuevas marcadas a ciegas.

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
