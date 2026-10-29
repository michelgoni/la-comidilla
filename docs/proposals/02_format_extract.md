# Propuesta 02. Formatear `src/extract.py` para leerlo en un panel estrecho

Fecha: 29 de octubre de 2026.

## Qué quiero hacer

Reformatear `src/extract.py` para que se lea de arriba abajo en el panel derecho de VS Code, sin cambiar lo que hace el programa.

- Máximo de 79 caracteres por línea.
- Cada función lleva una frase de ayuda en inglés que dice qué hace y por qué existe. La frase cabe en una línea.
- No añado comentarios dentro del cuerpo de las funciones. Solo la frase de ayuda de cada función y la del principio del fichero.
- Las líneas largas se parten con paréntesis, corchetes y textos encadenados. El texto de los mensajes no cambia ni una letra.
- Las firmas y las llamadas largas se reparten en varias líneas.

## Qué asumo

- En el panel derecho de VS Code caben unas 79 letras con el tamaño de letra que usas. Si no caben, se baja el ancho y se vuelve a formatear.
- Los comentarios van en inglés porque es la regla del proyecto. La explicación en castellano sigue en `docs/specs/01_extraction.md`.
- Los nombres de los campos del registro y los mensajes por pantalla se quedan como están.

## Qué toco

- Solo `src/extract.py`.
- No toco el prompt, el modelo, el corpus, la hoja marcada ni las pruebas.
- No añado dependencias ni paso un formateador automático.

## Frases de ayuda propuestas

| Función | Frase en inglés | Qué dice en castellano |
| --- | --- | --- |
| `load_config` | `"""Load model settings; fail fast so no call runs unconfigured."""` | Carga la configuración y para antes de llamar si falta algo. |
| `load_corpus` | `"""Load the review list; reject bad files before any model call."""` | Carga el corpus y rechaza ficheros raros. |
| `pick_review` | `"""Return one review by number; stop when the number is out of range."""` | Coge una reseña y avisa si el número no existe. |
| `load_prompt` | `"""Read the prompt; refuse an empty one so the model cannot improvise."""` | Lee el prompt y rechaza uno vacío. |
| `build_payload` | `"""Build the request body; keep it separate so it can be checked."""` | Monta el paquete y lo deja aparte para revisarlo sin gastar. |
| `call_model` | `"""Send the request; report each failure where it happened."""` | Envía la petición y dice en qué punto falló. |
| `clean_answer` | `"""Strip code fences; keep only the JSON list the model returned."""` | Quita las vallas y deja solo la lista. |
| `check_shape` | `"""Check every judgment; report problems instead of fixing them."""` | Revisa la forma y avisa sin corregir. |
| `append_registry` | `"""Append one call to the registry; never lose earlier entries."""` | Apunta la llamada sin borrar las anteriores. |
| `main` | `"""Run one review end to end; show the result and log the call."""` | Dirige el programa de principio a fin. |

## Cómo compruebo que no rompo nada

1. `python3 -m py_compile src/extract.py` para ver que el fichero compila.
2. `python3 -m unittest` para pasar las pruebas actuales.
3. Reviso que ninguna línea pase de 79 caracteres.
4. Comparo con la versión anterior para confirmar que solo cambian espacios, saltos de línea y las frases de ayuda.

## Qué no hago

- No parto el fichero en varios.
- No saco funciones nuevas ni cambio nombres.
- No cambio el comportamiento, los mensajes ni el orden de los pasos.
- No toco `data/registry.json` ni gasto llamadas al modelo.

## Qué necesito de ti

Revisa la propuesta y dime si la apruebas. Si la apruebas, escribo la decisión en `docs/decisions/02_format_extract.md` y aplico el cambio en `src/extract.py`.
