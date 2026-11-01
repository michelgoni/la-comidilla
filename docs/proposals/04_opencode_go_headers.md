# Propuesta 04. Hablar con OpenCode Go desde `src/extract.py`

Fecha: 1 de noviembre de 2026.

## Qué quiero hacer

Que `src/extract.py` pueda llamar al endpoint de OpenCode Go (`https://opencode.ai/zen/go/v1`). Hoy no puede: el endpoint rechaza las peticiones del cliente de Python. Hace falta añadir dos cabeceras a `call_model`:

1. **User-Agent de navegador.** OpenCode Go está detrás de Cloudflare, y Cloudflare bloquea el user-agent por defecto de Python (error 403, código 1010). Con un user-agent de navegador normal, pasa.
2. **`x-opencode-session`.** El endpoint la exige para enrutar la petición (sin ella responde `MissingSessionID`). Vale cualquier valor; proponemos el fijo `comidilla`.

Con eso, la configuración de `~/.hermes/secrets/comidilla.env` pasa a apuntar a OpenCode Go con su clave real y el modelo `claude-haiku-5-5`, y se pueden repasar las 39 reseñas que quedaron con error 402. La clave sigue fuera de la carpeta del proyecto.

## Por qué hace falta

Nous, el proveedor de toda la corrida, se quedó sin crédito y el Sonnet 4.5 que usamos no está en OpenCode Go. Michel decidió hoy repasar las 39 con `claude-haiku-5-5` por OpenCode Go (coste 0, incluido en la suscripción de 10 dólares al mes). Sin estas dos cabeceras, el endpoint no acepta las llamadas.

## Consecuencia para los datos

El corpus queda mezclado: 1.134 reseñas con `anthropic/claude-sonnet-4.5` y 39 con `claude-haiku-5-5`. Cada línea lleva su modelo en el campo `modelo`, así que la mezcla es trazable. La especificación 03, al medir, tendrá que tenerlo en cuenta.

## Qué toco

- `src/extract.py`: dos cabeceras más en `call_model`. Nada más.
- `tests/test_extract.py`: una prueba que comprueba que las peticiones llevan las dos cabeceras.
- `~/.hermes/secrets/comidilla.env`: base_url, modelo y clave de OpenCode Go. Fuera de la carpeta del proyecto, como manda la regla de secretos.

## Qué no toco

- El prompt, el corpus, la hoja marcada y el resto de `src/`.
- Las dos cabeceras se mandan siempre, también a otros endpoints. Son cabeceras ordinarias: los servidores que no las usan las ignoran.

## Coste

La prueba y el repase usan la suscripción de OpenCode Go. El modelo `claude-haiku-5-5` sale a coste 0. Son 39 reseñas más sus reintentos.

## Cómo se comprueba que funciona

1. Una llamada de prueba por la ruta exacta de producción responde.
2. La prueba nueva comprueba que toda petición lleva user-agent de navegador y `x-opencode-session`.
3. La suite entera en verde.
4. El repase de las 39 deja `result_corpus.jsonl` con 1.173 líneas, una por reseña, y las 39 nuevas llevan `modelo` = `claude-haiku-5-5`.

## Qué necesito de ti

Ya lo aprobaste en la conversación de hoy, con el detalle de las dos cabeceras. Esta propuesta lo deja escrito. Si ves algo que cambiar, dilo antes de fusionar la pull request.
