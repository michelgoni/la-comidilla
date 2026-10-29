# Decisión 01. Extraer los juicios de una reseña

Fecha: 29 de octubre de 2026.

Se aprueba la especificación `docs/specs/01_extraction.md` y se implementa en `src/extract.py`, con sus pruebas en `tests/test_extract.py`.

Motivo: Michel pidió implementar la especificación. La propuesta ya describía el programa completo, así que no se añaden reglas nuevas.

Se aceptan las tres decisiones propuestas en la especificación:

1. El código vive en `src/extract.py`, con nombres de ficheros, funciones y comentarios en inglés. Los datos guardados dentro del registro siguen en castellano.
2. Todos los programas usan una única ruta de prompt, configurable con `COMIDILLA_PROMPT`. Por defecto se usa `prompts/prompt_v4.txt`.
3. El registro `data/registry.json` guarda un json por línea, para que se pueda leer igual que los resultados del corpus y se pueda cortar sin romper el fichero.

El registro antiguo con sangría queda archivado en `data/registry_old_2026-10-21.json` y no se toca. El registro nuevo empieza vacío.
