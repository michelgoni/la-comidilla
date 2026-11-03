# Decisión 11. El examen corre también en promptfoo

Fecha: 3 de noviembre de 2026.

Se aprueba el paso 1 de la propuesta `docs/proposals/06_eval_harness.md`, hablada y aprobada por Michel en la conversación del mismo día.

Motivo: la ruta de aprendizaje por lectura no produjo nada. El paso 1 pone el examen que ya existe en una herramienta de pruebas del oficio (promptfoo) para que los pasos siguientes tengan dónde apoyarse: comparar modelos, contador de coste y puerta automática en GitHub.

Queda así:

1. Entra la herramienta **promptfoo**, licencia MIT, ejecutada con `npx promptfoo@latest`. No se instala en el proyecto y no se añade ninguna librería de Python. El examen sigue siendo del proyecto: la hoja marcada, la rúbrica y las cuentas no se delegan.
2. Se crea la carpeta `evals/`, única excepción a la norma de que la raíz solo tenga `AGENTS.md` y `README.md`. Dentro viven la configuración, el proveedor propio y el generador del conjunto de pruebas.
3. El conjunto de pruebas sale de `labelled/reviews_blind.json`: 30 reseñas y 87 juicios. El fichero generado no entra en el repositorio, porque son textos de terceros.
4. Se aprueban **30 llamadas al modelo**, una por reseña, con el prompt v4 y el modelo que ya apunta `~/.hermes/secrets/comidilla.env`. No se cambia el prompt, ni el modelo, ni la hoja, ni el corpus.
5. El proveedor propio repite la petición de `src/extract.py`, con el user-agent de navegador y la cabecera `x-opencode-session` (decisión 04), para que el examen no dependa de que el servidor se parezca a otro.
6. Las cuentas no se reescriben: se reutilizan las funciones de comparación de `src/measure.py` sobre las respuestas que produzca la herramienta.

Comprobación: la tabla de promptfoo da los mismos números que `python3 src/recount.py`, con menos de un punto de diferencia. Si no coinciden, no se toca la hoja ni el prompt: se busca la causa en la forma de la petición, en el recuento por pareja frente a por fila, o en el modelo usado, y se deja escrito.
