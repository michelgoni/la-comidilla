# Especificación 01. Extraer los juicios de una reseña

Estado: aprobada el 29 de octubre de 2026. La decisión está en `docs/decisions/01_extraction.md`.

## Para qué existe

El programa coge una sola reseña y la convierte en una lista de juicios con forma fija. Un juicio dice tres cosas: de qué habla la reseña (el tema), si habla bien o mal (la polaridad) y el trozo exacto que lo demuestra. Nada más.

Sirve para dos cosas. Primero, para probar el prompt con una reseña concreta sin gastar llamadas en todo el corpus. Segundo, para ser la pieza que los otros programas reutilizan cuando necesitan hablar con el modelo. Sin este programa no hay nada: el que recorre el corpus y el que mide lo importan.

## Qué recibe

- **Una reseña del corpus de Gilda.** `/home/ubuntu/gastronomy/gilda-report/corpus_reviews.json`. Es una lista de listas, cada una con `[local, estrellas, texto]`. 174 reseñas. Solo se lee, nunca se toca.
- **El texto del prompt**, en un fichero aparte. La ruta se puede cambiar con la variable de entorno `COMIDILLA_PROMPT`. Por defecto, `prompts/prompt_v4.txt`. La v3 se queda en la carpeta para poder comparar.
- **La dirección del modelo, su nombre y la clave.** Primero del entorno: `COMIDILLA_BASE_URL`, `COMIDILLA_MODEL`, `COMIDILLA_API_KEY`. Si no están, de `/home/ubuntu/.hermes/secrets/comidilla.env`, con líneas `NOMBRE=valor`. La clave nunca vive dentro de la carpeta del proyecto.
- **El número de reseña** que se quiere analizar, por línea de comandos. Por defecto 0, la primera.

## Qué devuelve

1. **Por pantalla:** la reseña elegida, la respuesta cruda del modelo, si la forma es correcta, los problemas encontrados y lo que tardó.
2. **Un registro en `data/registry.json`.** Una entrada por llamada. Cada llamada añade una entrada sin borrar las anteriores. Campos: `fecha`, `modelo`, `direccion`, `numero`, `local`, `estrellas`, `prompt_sistema`, `mensaje_usuario`, `respuesta`, `milisegundos`, `error`. Los nombres de los campos van en castellano, igual que los de los demás ficheros de datos y los de tu hoja marcada. La regla de escribir el código en inglés es para los nombres de ficheros, las funciones y los comentarios, no para los datos.

## Cómo funciona, paso a paso

1. Lee la configuración. Si falta la dirección o el nombre del modelo, para y dice qué falta. La clave puede ir vacía si el servidor no la pide.
2. Carga el corpus y comprueba que es una lista no vacía.
3. Comprueba que el número pedido existe. Si no, para y dice cuántas reseñas hay y el rango válido.
4. Lee el prompt del fichero. Ese texto va como mensaje de sistema. El mensaje de usuario es la reseña entre comillas triples: `Reseña:` seguido de tres comillas, el texto y tres comillas.
5. Llama al modelo con una petición POST a `{direccion}/chat/completions`. El cuerpo lleva el nombre del modelo, temperatura 0 y dos mensajes, uno de sistema y otro de usuario. Las cabeceras llevan el tipo de contenido, la clave como `Bearer` y un identificador de sesión. La espera máxima son 120 segundos.
6. Si el servidor devuelve un error, para y enseña el código de error y los primeros 400 caracteres del cuerpo. Si no hay conexión, para y enseña el motivo. Si la respuesta no trae el texto donde se espera, para y enseña lo que llegó.
7. Limpia la respuesta. El modelo a veces envuelve el json en bloques de código. Quita las vallas y deja solo la lista. Si no hay vallas, corta desde el primer corchete hasta el último.
8. Revisa la forma. Tiene que ser una lista. Cada elemento tiene que ser un objeto con `tema`, `polaridad` y `trozo`. El tema tiene que ser uno de comida, servicio, precio, ambiente o espera. La polaridad, uno de positivo, negativo o mixto. El trozo tiene que ser texto no vacío y tiene que aparecer de verdad en la reseña, comparando sin espacios de más. Si el trozo une dos frases con ` ... `, cada parte tiene que aparecer por separado. No se corrige el contenido, solo se avisa.
9. Enseña el resultado y apunta la llamada en el registro, haya ido bien o mal.

## Cómo es el código

Un solo fichero: `src/extract.py`. Nada de clases ni de capas: funciones sueltas, cada una con una tarea y un nombre que dice lo que hace. Así se puede leer de arriba abajo y probar cada trozo por separado.

Los comentarios dentro del código van en inglés, como decidiste para todo el código del proyecto. La explicación en español va aquí debajo, función por función, para que no tengas que pelearte con el código para entenderlo.

Al principio del fichero van las constantes, que son los datos fijos que no cambian: la carpeta del proyecto, las rutas de los ficheros, la lista de temas permitidos y la lista de polaridades permitidas.

```python
"""Extract judgments from a single restaurant review."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
CORPUS_PATH = Path("/home/ubuntu/gastronomy/gilda-report/corpus_reviews.json")
SECRETS_PATH = Path("/home/ubuntu/.hermes/secrets/comidilla.env")
REGISTRY_PATH = PROJECT / "data" / "registry.json"
DEFAULT_PROMPT_PATH = PROJECT / "prompts" / "prompt_v3.txt"

THEMES = ("comida", "servicio", "precio", "ambiente", "espera")
POLARITIES = ("positivo", "negativo", "mixto")
```

Y estas son las ocho funciones. Cada línea de comentario dice qué hace esa función, no cómo.

```python
def load_config() -> dict:
    """Return base_url, model and api_key from the environment or the secrets file."""


def load_corpus(path: Path) -> list:
    """Return the list of reviews. Stop with a clear message if the file is not a list."""


def pick_review(reviews: list, index: int) -> tuple:
    """Return the review at that index. Stop with a clear message if the index is out of range."""


def load_prompt(path: Path) -> str:
    """Return the prompt text. Stop with a clear message if the file is missing or empty."""


def build_payload(model: str, prompt: str, review_text: str) -> dict:
    """Return the request body: temperature 0, one system message and one user message."""


def call_model(base_url: str, api_key: str, payload: dict, timeout: int = 120) -> tuple:
    """Send the POST request. Return the answer text and the milliseconds it took."""


def clean_answer(raw: str) -> str:
    """Return only the JSON list, removing code fences if the model added them."""


def check_shape(judgments: object, review_text: str) -> list:
    """Return the list of problems found with the answer. An empty list means it is well formed."""


def append_registry(entry: dict) -> None:
    """Add one entry to data/registry.json without removing the previous ones."""


def main() -> None:
    """Read one review, ask the model, check the answer, show it and log the call."""
```

Qué hace cada una, en castellano:

- **`load_config`.** Mira primero las tres variables de entorno y, si no están, lee el fichero de secretos. Devuelve un diccionario con la dirección, el modelo y la clave. Si falta la dirección o el modelo, para el programa con un mensaje que dice cuál falta. La clave puede venir vacía, porque el servidor de pruebas no la pide.
- **`load_corpus`.** Abre el json del corpus. Comprueba que lo que hay dentro es una lista y que no está vacía. Si el fichero no existe o no es una lista, para con un mensaje claro. No sigue adelante con datos raros.
- **`pick_review`.** Coge la reseña del número pedido. Comprueba que ese número existe. Si no, para y dice cuántas reseñas hay y hasta dónde llega el rango. Devuelve las tres piezas: local, estrellas y texto.
- **`load_prompt`.** Lee el fichero del prompt y lo devuelve como texto. Si el fichero no está o está vacío, para. Un prompt vacío haría que el modelo improvisara, y eso es peor que no llamar.
- **`build_payload`.** Monta el cuerpo de la petición: el nombre del modelo, temperatura 0 (para que la respuesta sea lo más repetible posible) y los dos mensajes, el de sistema con el prompt y el de usuario con la reseña entre comillas triples. Esta función no llama a nadie, solo construye el paquete. Separarla permite ver el paquete antes de gastar una llamada.
- **`call_model`.** Envía la petición y recoge la respuesta. Cuenta los milisegundos. Si el servidor contesta con un error, para y enseña el código y los primeros 400 caracteres del cuerpo. Si no hay conexión, para y enseña el motivo. Si la respuesta no trae el texto donde se espera, para y enseña lo que llegó. Los cuatro parones son distintos a propósito: cada uno te dice dónde se rompió.
- **`clean_answer`.** El modelo a veces envuelve la lista en vallas de código. Esta función quita las vallas. Si no hay vallas, corta desde el primer corchete hasta el último. Devuelve solo la lista.
- **`check_shape`.** La más importante para ti. Convierte el texto en datos y revisa cuatro cosas: que sea una lista, que cada elemento tenga los tres campos, que el tema y la polaridad sean de las listas permitidas, y que el trozo aparezca de verdad en la reseña. Para comparar el trozo, quita los espacios de más de los dos lados. Si el trozo une dos frases con ` ... `, comprueba cada parte por separado. Devuelve una lista de problemas. Si esa lista está vacía, la forma es correcta.
- **`append_registry`.** Añade una entrada con lo que se mandó, lo que volvió y lo que tardó. Lee lo que había, añade la nueva al final y vuelve a guardar. Así nunca se pierden las llamadas anteriores.
- **`main`.** Es el director de orquesta. Llama a las otras en orden: configuración, corpus, reseña, prompt, paquete, llamada, limpieza, revisión, pantalla y registro. Se lee de arriba abajo y cada paso es una línea.

Un detalle del diseño que conviene entender: el registro se escribe siempre, también cuando algo falla. Un fallo apuntado es información. Un fallo perdido es un misterio.

## En qué orden construirlo

No se pide el fichero entero de una vez. Se pide por trozos y cada trozo se ejecuta antes de pasar al siguiente. Cuando un trozo funciona, se guarda en git. Así, si el siguiente rompe algo, se vuelve atrás y se ve qué cambió.

El orden va de lo que no llama a nadie a lo que sí llama. Primero los pasos que no gastan nada, y el envío al modelo se deja para cuando lo demás ya está probado.

- **Paso 0. El esqueleto y la línea de comandos.** Se crea `src/extract.py` con las constantes, los `import` y un `main` que solo lee la opción `--index`. Qué se pide a OpenCode: la estructura del fichero y el `argparse`. Qué se ve: al ejecutarlo sin nada, un mensaje que dice qué número de reseña va a usar. Prueba: ejecutarlo con `--index 3` y ver que lo entiende.
- **Paso 1. Leer la configuración.** Se escribe `load_config`. Qué se ve: al ejecutarlo sin variables y sin fichero de secretos, un mensaje que dice que falta la dirección del modelo. Prueba: poner la dirección en una variable y ver que ya no se queja de esa.
- **Paso 2. Cargar el corpus.** Se escriben `load_corpus` y `pick_review`. Qué se ve: el local y las estrellas de la reseña pedida, y el principio del texto. Prueba: pedir la reseña 0, luego la 5, luego la 900 para ver el mensaje de número fuera de rango.
- **Paso 3. Leer el prompt.** Se escribe `load_prompt`. Qué se ve: la primera línea del prompt y cuántos caracteres tiene. Prueba: apuntar `COMIDILLA_PROMPT` a un fichero que no existe y ver el parón.
- **Paso 4. Montar el paquete.** Se escribe `build_payload`. Qué se ve: el paquete entero por pantalla, con la clave tapada. Aquí todavía no se llama a nadie, así que se puede mirar con calma que el mensaje de usuario lleva la reseña bien metida entre comillas triples.
- **Paso 5. Enviar la petición.** Se escribe `call_model`. Qué se ve: la respuesta cruda del servidor falso y los milisegundos. Prueba: levantar el servidor falso, apuntar la dirección a él y ejecutar. Después, apagar el servidor y ejecutar otra vez para ver el parón por falta de conexión.
- **Paso 6. Limpiar la respuesta.** Se escribe `clean_answer`. Qué se ve: la respuesta limpia, sin vallas. Prueba: hacer que el servidor falso devuelva la lista metida en vallas y comprobar que el programa la acepta igual.
- **Paso 7. Revisar la forma.** Se escribe `check_shape`. Es el paso que más se va a notar. Qué se ve: si la forma es correcta, una línea que lo dice; si no, la lista de problemas. Prueba: respuesta buena, trozo inventado, tema que no vale, respuesta que no es una lista.
- **Paso 8. Enseñar y apuntar.** Se escribe `append_registry` y se remata `main` para que enseñe el resumen y apunte la llamada. Qué se ve: la entrada nueva al final de `data/registry.json`. Prueba: ejecutar dos veces y comprobar que hay dos entradas, que la primera no se ha perdido.

## Línea de comandos

```
python3 src/extract.py                 (la reseña 0)
python3 src/extract.py --index 17      (la reseña 17)
```

El número empieza en 0. No hay más opciones.

## Lo que no hace

- No llama a más de un modelo a la vez.
- No reintenta. Si falla, falla y lo apunta. Los reintentos son cosa del programa que recorre el corpus.
- No puntúa el local ni resume la reseña. Devuelve juicios.
- No inventa texto. Todo trozo sale de la reseña.
- No escribe en la hoja marcada a mano.

## Cómo se comprueba que funciona

Con un servidor falso que devuelva siempre la misma respuesta. Se levanta en local y se apunta `COMIDILLA_BASE_URL` a él. No se gasta dinero.

1. **Caso bueno.** Respuesta con un juicio cuyo trozo está de verdad en la reseña. El programa dice que la forma es correcta y escribe la entrada en el registro.
2. **Trozo inventado.** El trozo no aparece en la reseña. El programa dice que la forma es incorrecta y explica que el trozo no está.
3. **Tema que no vale.** Tema `limpieza`. El programa lo rechaza y dice por qué.
4. **Respuesta con vallas.** El modelo devuelve el json dentro de un bloque de código. El programa lo limpia y lo acepta.
5. **Trozo de dos frases.** El trozo une dos frases con ` ... `. El programa comprueba cada parte y lo acepta si las dos aparecen.
6. **Sin configuración.** Sin dirección ni nombre de modelo. El programa para con un mensaje claro y no llama a nadie.

Cada uno de estos casos es una prueba automática en `tests/test_extract.py`, con la librería de pruebas que viene con Python. Se ejecutan con `python3 -m unittest`. El paso 5 se prueba con el servidor falso, sin gastar llamadas.

## Dependencias

Solo la librería estándar de Python. Nada que instalar.

## Decisiones propuestas, cámbialas si no te valen

1. **El fichero se llama `extract.py`, en inglés.** La versión antigua lo llamaba `extraer.py`. La regla del proyecto es que los ficheros de código y los comentarios van en inglés, así que el nombre cambia. Los datos que se guardan dentro siguen en castellano, porque son los mismos campos de tu hoja marcada y de los otros ficheros de datos. El archivo viejo del registro está archivado en `data/registry_old_2026-10-21.json`.
2. **Un solo prompt para todos los programas.** La versión antigua tenía una trampa: el programa de medir usaba un prompt y el de extraer usaba otro, así que los resultados guardados decían un prompt que no era el que se había usado. La propuesta es una única ruta de prompt, configurable, y que todos los programas usen la misma. El defecto es `prompts/prompt_v4.txt`, que es el que llevaba los tres arreglos de la última revisión. La v3 se queda para poder reproducir las medidas anteriores.
3. **El registro, un json por línea.** La versión antigua guardaba una lista con sangría. Para muchas llamadas, un fichero de texto con un json por línea es más fácil de procesar y de cortar por la mitad. La propuesta es cambiar a ese formato.

## Cómo se trabaja esta especificación

- El trabajo va en la rama `spec-01-extraction`, nunca directamente sobre `main`.
- Se abre una pull request contra `main` cuando la rama está lista.
- GitHub ejecuta las pruebas solo, en cada pull request. Si alguna falla, no se fusiona.
- Solo se fusiona con las pruebas en verde y con el visto bueno de Michel.
- El método completo, con los comandos, está en `docs/working-method.md`.
