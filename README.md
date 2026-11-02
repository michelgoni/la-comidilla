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

- **Terminado:** el extractor (`src/extract.py`), el programa que recorre el corpus (`src/run_corpus.py`) y el examen que mide contra las reseñas marcadas a mano (`src/measure.py`). Los tres con sus pruebas, y GitHub las ejecuta en cada cambio.
- **Pendiente:** el rival de reglas (`docs/specs/04_rules_baseline.md`), que es el listón contra el que se compara el modelo.

## Cómo se trabaja aquí

Cada pieza sigue el mismo camino: se escribe la especificación, se propone, se decide y se deja la decisión por escrito, y solo entonces se programa. Cada especificación tiene su rama, cada cambio su pull request, y las pruebas se ejecutan solas antes de fusionar. El detalle está en `docs/working-method.md`.

## Cómo se ejecuta

```
python3 src/extract.py --index 3                  (analiza la reseña número 3)
python3 src/run_corpus.py                         (recorre el corpus entero)
python3 -m unittest discover -s tests             (las pruebas, sin gastar llamadas)
```

Solo necesita la librería estándar de Python, nada que instalar. Para llamar de verdad al modelo hacen falta tres datos en el entorno: la dirección, el nombre del modelo y la clave.

## Lo que no está en este repositorio, a propósito

El corpus y la hoja de reseñas marcadas a mano no se publican. Son textos de terceros y una hoja de trabajo personal, así que quedan fuera con el `.gitignore`. Para ejecutar el programa hace falta un corpus propio con esta forma: `[local, estrellas, texto]`.

## Resultados

Medido el 1 de noviembre de 2026 con este código, sobre las 20 reseñas marcadas a mano, que suman 56 juicios. Modelo Claude Haiku 5.5 y prompt `prompt_v4.txt`.

| Medida | Resultado |
| --- | --- |
| Precisión por pareja | 94,2% |
| Recuerdo por pareja | 87,5% |
| Parejas inventadas | 3 de 52 |
| Parejas omitidas | 7 de 56 |
| Avisos de forma | 0 |

La cuenta por pareja compara cada tema y tono una sola vez por reseña, que es como está marcada la hoja. La cuenta por filas, que castiga la repetición, da 46,2% de precisión: el modelo devuelve 106 filas para 52 parejas distintas, 2,04 por pareja. Ese ruido se mide aparte y no se esconde.

Dos límites que conviene decir en voz alta. El rival de reglas todavía no está reconstruido, así que la comparación contra listas de palabras queda para más adelante. Y las marcas se revisaron después de ver la primera respuesta del modelo, así que la nota puede estar algo alta; para una medida limpia hacen falta reseñas nuevas marcadas a ciegas.

## Dónde está cada cosa

| Carpeta | Qué guarda |
| --- | --- |
| `docs/specs/` | Lo que cada programa tiene que hacer. |
| `docs/proposals/` | Las propuestas, antes de programar. |
| `docs/decisions/` | Las decisiones tomadas, con fecha y motivo. |
| `docs/working-method.md` | La norma de trabajo: ramas, pull requests y pruebas. |
| `src/` | El programa de extracción. |
| `tests/` | Las pruebas. |
| `prompts/` | Las versiones del texto que se manda al modelo. |
| `AGENTS.md` | El contrato de trabajo con cualquier asistente que toque este repositorio. |

## De dónde sale el método

De dos sitios. Del libro *AI Engineering*, de Chip Huyen: la división en tres capas del stack (capítulo 1, «The AI Engineering Stack», p. 59) y la idea de definir la evaluación antes de construir (capítulo 4, *evaluation-driven development*, p. 160). Y de la rúbrica de etiquetado del propio proyecto, que vive fuera del repositorio y es la que fija qué es un juicio y qué no.
