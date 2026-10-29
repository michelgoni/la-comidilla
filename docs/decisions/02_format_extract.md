# Decisión 02. Formatear la extracción para leerla en un panel estrecho

Fecha: 29 de octubre de 2026.

Se aprueba la propuesta `docs/proposals/02_format_extract.md`.

Motivo: Michel aprobó la propuesta. Quiere leer `src/extract.py` de arriba abajo en el panel derecho de VS Code, sin desplazarse en horizontal.

Se aplica así:

1. Ninguna línea pasa de 79 caracteres.
2. Cada función conserva una frase de ayuda en inglés que dice qué hace y por qué existe.
3. No se añaden comentarios dentro del cuerpo de las funciones.
4. Solo cambia `src/extract.py`. No cambian el comportamiento, los mensajes, el prompt, el modelo, el corpus ni las pruebas.
5. No se añaden dependencias ni se usa un formateador automático.

La comprobación queda escrita en la propuesta: compilar, pasar las pruebas, medir el ancho de las líneas y comparar con la versión anterior.

Comprobado el 29 de octubre de 2026: el fichero compila, las 28 pruebas pasan y ninguna línea supera los 79 caracteres.
