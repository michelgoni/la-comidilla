# Decisión 04. Repasar las fallidas con Haiku 5.5 por OpenCode Go

Fecha: 1 de noviembre de 2026.

Se aprueba la propuesta `docs/proposals/04_opencode_go_headers.md`, ya hablada y aprobada por Michel en la conversación del mismo día.

Motivo: Nous se quedó sin crédito y no tiene Sonnet en OpenCode Go. Michel eligió repasar las 39 reseñas con error 402 usando `claude-haiku-5-5` por OpenCode Go (suscripción de 10 dólares al mes, ese modelo a coste 0), tras saber que el Sonnet 4.5 de la corrida no está disponible ahí.

Queda así:

1. `src/extract.py` manda dos cabeceras más en `call_model`: un user-agent de navegador (Cloudflare bloquea el de Python) y `x-opencode-session` con el valor fijo `comidilla` (el endpoint la exige). Se mandan siempre; los endpoints que no las usan las ignoran.
2. `~/.hermes/secrets/comidilla.env` apunta a `https://opencode.ai/zen/go/v1` con el modelo `claude-haiku-5-5` y la clave real de la suscripción. La clave vive ahí, fuera de la carpeta del proyecto. Cuando Nous vuelva a tener crédito, volver al Sonnet 4.5 es cambiar esa línea.
3. El corpus queda mezclado y se acepta: 1.134 reseñas con `anthropic/claude-sonnet-4.5` y 39 con `claude-haiku-5-5`, cada línea con su modelo en el campo `modelo`. La especificación 03 tendrá que tenerlo en cuenta al medir.
4. Se mantiene la decisión del mismo día de no repasar las 32 reseñas con avisos: se quedan y cuentan como `forma_correcta` falso.

La comprobación queda en las pruebas (las dos cabeceras en toda petición) y en el propio repase: 1.173 líneas, una por reseña, las 39 nuevas con su modelo apuntado.
