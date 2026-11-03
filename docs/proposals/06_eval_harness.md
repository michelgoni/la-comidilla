# Propuesta 06. Convertir el examen en un banco de pruebas y aprender con él

Fecha: 3 de noviembre de 2026.
Estado: pendiente de revisión por Michel.

## Por qué esta propuesta y no la ruta de antes

La ruta anterior era leer primero y practicar después: capítulos del libro de Chip Huyen, cursos de DataCamp, y un ejercicio por bloque que reusaba algo ya terminado. No funcionó por dos motivos concretos:

1. **No había nada que decidir.** El proyecto ya estaba medido y cerrado, así que cada ejercicio consistía en volver a mirar trabajo hecho. Mirar no es construir.
2. **Los cursos enseñan a hacer lo que ya hiciste.** El examen, la hoja marcada a ciegas y el rival de reglas son justo la parte que un curso da por supuesta. Diez cursos de vídeo no te van a decir qué falta.

Lo que falta no es teoría. Falta la parte del oficio que va después de medir una vez: comparar modelos, saber cuánto cuesta cada respuesta, y que un cambio malo no llegue a fusionarse. Eso se aprende tocando este repositorio, no leyendo.

## Qué propongo

Cinco pasos. Cada uno deja un fichero, un número y una decisión escrita. Ninguno cambia el prompt v4, ni la hoja marcada, ni el corpus.

### Paso 1. El mismo examen, en una herramienta de pruebas (30 llamadas)

Un fichero de configuración con tres piezas separadas: las 30 reseñas, el prompt v4 y el modelo. Un comando. La tabla de siempre, sin que la escriba tu medidor.

- **Ficheros:** `evals/promptfooconfig.yaml`, `evals/provider.mjs`, `evals/dataset.jsonl` (este último no entra en el repositorio: son textos de terceros).
- **Proveedor propio:** un fichero de unas quince líneas que manda la misma petición que `src/extract.py`, con el user-agent de navegador y la cabecera `x-opencode-session` que el endpoint exige (decisión 04). Así el examen no depende de que el servidor se parezca a otro.
- **Qué se aprende:** separar datos, prompt y modelo; correr un examen con un comando; ver por qué las herramientas de este oficio se configuran en vez de programarse.
- **Cómo se comprueba:** las cifras salen igual que en `src/recount.py`, con menos de un punto de diferencia. 75 juicios encontrados de 87, 19 inventados de 94, 12 omitidos.

### Paso 2. Reglas automáticas sobre la respuesta (0 llamadas)

Tres comprobaciones que no dependen de mirar a ojo, sobre la misma pasada del paso 1:

1. La respuesta es una lista con `tema`, `polaridad` y `trozo`, y los valores están entre los cinco temas y las tres polaridades.
2. El trozo aparece literal en la reseña. Si no aparece, la respuesta falla y dice cuál no aparece.
3. Cada respuesta cabe en un umbral de tiempo y de coste.

- **Qué se aprende:** la diferencia entre comprobar con código (no perdona, no cuesta) y juzgar con modelo (entiende, pero hay que vigilarlo). Es la base de todo lo demás.
- **Cómo se comprueba:** una respuesta con el trozo cambiado a mano falla con el motivo escrito, no con una nota más baja.

### Paso 3. La misma hoja contra tres modelos (60 llamadas)

El prompt v4 tal cual, contra el modelo actual y otros dos baratos. Una sola tabla con precisión y recuerdo por pareja, precisión por fila, segundos y coste por cada mil reseñas.

- **Qué se aprende:** que el prompt es la mitad y el modelo la otra; que el más caro no siempre gana; que el coste por documento es un número que se pone en una entrevista y casi nadie trae.
- **Cómo se comprueba:** una decisión escrita con el modelo elegido, el motivo, y el número que lo sostiene. Si los tres empatan, eso también es una decisión y se escribe.

### Paso 4. Que el examen impida fusionar una regresión (30 llamadas por cambio de prompt)

Una ejecución automática en GitHub que salta cuando un cambio toca `prompts/` o `evals/`. Corre el examen y falla si el F1 por pareja baja más de dos puntos respecto a la línea base guardada. Con memoria de respuestas para no pagar dos veces lo mismo.

- **Qué se aprende:** puerta de calidad, línea base guardada, coste del examen dentro de la ejecución automática. Es la pieza que separa un proyecto de portafolio de un cuaderno.
- **Cómo se comprueba:** un cambio de prompt hecho a propósito para empeorar, y GitHub lo rechaza con los números delante. Esa captura vale más que la sección de resultados del README.

### Paso 5. Opcional, solo si lo pides: servicio y trazas

Un servicio mínimo con una dirección `/extract` y un registro de coste y latencia por documento. Para trazas hay dos caminos: las que ya da la herramienta del paso 1, o Langfuse en el servidor (necesita cuatro piezas: base de datos, ClickHouse, Redis y almacenamiento; el servidor lo aguanta, pero para un lote no hace falta).

- **Qué se aprende:** la diferencia entre un programa que se ejecuta a mano y uno que responde a peticiones, y qué se mira cuando algo va lento o caro en producción.

## Qué cuesta

- 30 llamadas en el paso 1, 60 en el paso 3, y 30 por cada cambio de prompt en el paso 4. Mismo orden de gasto que la medida del 2 de noviembre. Nada de esto se lanza sin que lo apruebes.
- Una herramienta nueva: **promptfoo**. Licencia MIT, se ejecuta con `npx`, no entra en el código del proyecto. Node 22.23.2 ya está instalado en el servidor y la versión pedida es 22.22. Tú decides si entra.
- Una carpeta nueva: `evals/`. Va contra la norma de que la raíz solo tenga `AGENTS.md` y `README.md`, y por eso lo pido aquí en vez de crearla.

## Alternativa si no quieres herramienta nueva

Los pasos 1 y 2 se pueden hacer ampliando `src/measure.py`, y los pasos 3 y 4 a mano con Python. Se aprende más de cómo se construye un examen y menos de las herramientas que se usan en el oficio. Yo recomiendo promptfoo porque el paso 4 sin él es el doble de código, y porque saber montar una puerta de calidad con una herramienta estándar es lo que se pregunta en una entrevista. Pero es tu decisión y no cambia el resto del plan.

## Lo que no entra

Búsqueda vectorial, recuperación de documentos, agentes, llamada a herramientas, ajuste fino y multimodal. La Comidilla no usa nada de eso, y meterlo aquí sería empezar otro proyecto. Si algún día los quieres, van en un segundo proyecto con su propia medida.

## Las referencias, con lo que dan y lo que no

1. **promptfoo** (`github.com/promptfoo/promptfoo`, licencia MIT, 26.700 estrellas, actualizado el 3 de noviembre de 2026). Da: examen por configuración, comparación de modelos en una sola tabla, comprobaciones en código, ejecución automática en GitHub, interfaz web local para mirar los fallos, memoria de respuestas para no repetir llamadas. No da: la rúbrica. Eso sigue siendo tuyo. Aviso: la empresa pasó a formar parte de OpenAI este año; el código sigue libre con licencia MIT.
2. **LLM Zoomcamp de DataTalks.Club** (`github.com/DataTalksClub/llm-zoomcamp`, gratis, licencia MIT). Siete módulos. Te sirven el 04 (evaluación), el 05 (monitorización) y el 07 (proyecto de ejemplo). Los módulos 01, 02 y 03 son recuperación, búsqueda vectorial y agentes: no.
3. **El material de evaluación de Hamel Husain** (`hamel.dev/blog/posts/evals-faq`). Da: cómo analizar errores agrupándolos hasta que salen tres o cuatro causas, y cómo calibrar un juez automático contra tu propio criterio. Es el capítulo que te falta: tus 19 inventados no son invenciones, son tres desacuerdos de etiqueta repetidos. Su curso es de pago; el artículo y su guía pública no.
4. **Los recursos del libro de Chip Huyen** (`github.com/chiphuyen/aie-book`). Da: el mapa por capítulos, casos de estudio reales y la lista de lecturas de cada tema. No da: ejercicios. Es para consultar cuando un paso te deje una duda, no para leerlo entero antes de empezar.

## Cómo sabemos que el plan sirvió

Al terminar el paso 4, la respuesta a estas tres preguntas se puede enseñar sin prepararla:

1. ¿Cómo sabes que el sistema funciona? (la hoja marcada a ciegas, dos formas de contar, y el rival de reglas)
2. ¿Cuánto cuesta y cuánto tarda cada documento? (paso 3)
3. ¿Qué impide que un cambio lo empeore? (paso 4)

Hoy tienes la primera. Las otras dos son el hueco.

## Decisión que necesito

1. ¿Entra la herramienta y la carpeta `evals/`, o lo hacemos ampliando `measure.py`?
2. ¿Apruebas las 30 llamadas del paso 1 para empezar?
3. ¿Empezamos por el paso 1, o prefieres el 3 (comparar modelos) primero porque es el que más se pregunta en una entrevista?
