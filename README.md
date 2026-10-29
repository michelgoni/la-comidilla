# La Comidilla

Proyecto de aprendizaje de ingeniería de inteligencia artificial aplicada a reseñas de restaurantes. Coge reseñas escritas por personas y las convierte en juicios con forma fija: de qué habla la reseña (el tema), si habla bien o mal (la polaridad) y el trozo exacto que lo demuestra.

## Estado

El código antiguo se ha borrado. Se está reconstruyendo desde cero a partir de las especificaciones de `docs/specs/`, con ayuda de OpenCode. Los cuatro programas viejos están guardados fuera del proyecto, en `~/.hermes/cache/scratch/comidilla_legacy_backup`, solo por si hace falta comparar. No se usan.

## Por dónde empezar

Leer las especificaciones en este orden:

1. `docs/specs/01_extraction.md`. Extraer los juicios de una reseña. Es la base: los otros programas la importan.
2. `docs/specs/02_run_corpus.md`. Recorrer el corpus entero y guardar el resultado.
3. `docs/specs/03_measure_against_marks.md`. Medir el modelo contra las reseñas marcadas a mano.
4. `docs/specs/04_rules_baseline.md`. El rival sin modelo: listas de palabras.

## Carpetas

| Carpeta | Qué guarda |
| --- | --- |
| `docs/specs/` | Lo que cada programa tiene que hacer. |
| `docs/proposals/` | Propuestas antes de programar. |
| `docs/decisions/` | Decisiones tomadas, con fecha y motivo. |
| `src/` | El código. Ahora está vacío. |
| `tests/` | Las pruebas. Ahora está vacío. |
| `prompts/` | Las versiones del texto que se manda al modelo. |
| `labelled/` | Las 20 reseñas marcadas a mano y los resultados de cada medición. |
| `data/` | El corpus de trabajo y las salidas antiguas. |

## Datos

- El corpus original de Gilda: `/home/ubuntu/gastronomy/gilda-report/corpus_reviews.json`. 174 reseñas con la forma `[local, estrellas, texto]`. Solo se lee.
- El corpus ancho: `data/full_corpus.json`. 1.173 reseñas con la misma forma. Sirve para recorrer muchos locales.
- El examen: `labelled/reviews_to_label.json`. 20 reseñas marcadas a mano, 44 juicios en total. No se toca sin permiso de Michel.

## Secretos

La dirección del modelo, su nombre y la clave se leen del entorno o de `/home/ubuntu/.hermes/secrets/comidilla.env`. La clave nunca vive dentro de esta carpeta. Mientras ese fichero esté vacío, los programas que llaman al modelo se paran con un aviso claro.
