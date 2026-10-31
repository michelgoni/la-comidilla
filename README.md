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

- **Terminado:** el extractor, en `src/extract.py`. Coge una reseña, llama al modelo, limpia la respuesta, revisa que la forma sea la correcta y apunta la llamada en un registro. Tiene sus pruebas y GitHub las ejecuta en cada cambio.
- **Especificado y pendiente:** recorrer el corpus entero (`docs/specs/02_run_corpus.md`), medir contra las reseñas marcadas a mano (`docs/specs/03_measure_against_marks.md`) y el rival de reglas (`docs/specs/04_rules_baseline.md`).

## Cómo se trabaja aquí

Cada pieza sigue el mismo camino: se escribe la especificación, se propone, se decide y se deja la decisión por escrito, y solo entonces se programa. Cada especificación tiene su rama, cada cambio su pull request, y las pruebas se ejecutan solas antes de fusionar. El detalle está en `docs/working-method.md`.

## Cómo se ejecuta

```
python3 src/extract.py --index 3                  (analiza la reseña número 3)
python3 -m unittest discover -s tests             (las pruebas, sin gastar llamadas)
```

Solo necesita la librería estándar de Python, nada que instalar. Para llamar de verdad al modelo hacen falta tres datos en el entorno: la dirección, el nombre del modelo y la clave.

## Lo que no está en este repositorio, a propósito

El corpus y la hoja de reseñas marcadas a mano no se publican. Son textos de terceros y una hoja de trabajo personal, así que quedan fuera con el `.gitignore`. Para ejecutar el programa hace falta un corpus propio con esta forma: `[local, estrellas, texto]`.

## Resultados, provisionales

Medido con el prototipo anterior sobre 20 reseñas marcadas a mano. «Tema» y «tono» cuentan cada valoración por separado; «precisión» y «recuerdo» cuentan cada pareja de tema y tono una sola vez.

| Medida | tema | tono | precisión | recuerdo |
| --- | --- | --- | --- | --- |
| Modelo, con la regla del mixto en el prompt | 75% | 86% | 73% | 84% |
| Rival de reglas, listas de palabras | 66% | 74% | 68% | 68% |

La frase que lo resume: las reglas se pierden uno de cada tres juicios; el modelo, uno de cada seis. La precisión casi empata, así que el modelo se justifica por lo que no se le escapa, no por ser más limpio.

Estas cifras salen del prototipo anterior y hay que repetirlas con este código, que se está reconstruyendo con especificaciones. Mientras no se repitan, valen como orden de magnitud, no como resultado final.

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
