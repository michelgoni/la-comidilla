# Especificación 04. El rival sin modelo

Estado: propuesta para revisión de Michel. Si la apruebas, se copia a `docs/decisions/` y se empieza a programar.

## Para qué existe

Este programa marca reseñas sin usar ningún modelo. Solo mira palabras. Existe por una razón: si el modelo con inteligencia artificial no supera a unas listas de palabras escritas a mano, el modelo no aporta nada y el proyecto no tiene sentido. Es el rival más tonto posible. Si el modelo no le gana, mal asunto.

También sirve para tener una referencia barata. Este programa no gasta dinero ni tarda. Se puede lanzar mil veces.

## Qué recibe

- **La hoja marcada a mano.** `labelled/reviews_to_label.json`, igual que el programa de la especificación 03. Solo se usan las reseñas con `marcada` en verdadero. La versión antigua usaba todas, incluidas las no marcadas, y eso hacía que el rival pareciera peor de lo que es. Aquí se corrige.
- **El léxico.** Va dentro del programa, en el anexo de abajo. Son listas de palabras y trozos de palabras para cada tema.
- Nada más. Ni configuración, ni modelo, ni clave, ni conexión.

## Qué devuelve

1. **`labelled/result_rules.json`.** Una lista con una entrada por reseña. Cada entrada lleva numero, tus juicios (`mias`) y los del programa (`del_modelo`).
2. **Por pantalla:**
   - Total de parejas tuyas, total del programa y aciertos.
   - Precisión y recuerdo.
   - Por tema: en cuántas reseñas coincide el tema, de cuántas en las que alguno de los dos lo menciona.
   - Cuando coincide el tema, en cuántas coincide también el tono.
   - Cuántas líneas de juicio saca el programa en total.

## Cómo funciona, paso a paso

1. Carga la hoja y filtra las reseñas marcadas.
2. Parte el texto en frases. Se corta después de un punto, una interrogación, una exclamación o unos puntos suspensivos, cuando detrás hay un espacio o un salto de línea. También se corta en cada salto de línea.
3. Para cada frase y cada tema: si la frase contiene una pista de ese tema, se mira si también contiene una palabra de elogio o una de queja. Si contiene elogio, se apunta un juicio positivo con el tema y la frase entera como trozo. Si contiene queja, se apunta uno negativo. Si contiene las dos cosas, se apuntan los dos.
4. Quita juicios repetidos. Si dos son iguales en tema, tono y trozo, solo queda uno.
5. Compara con tus marcas. Aquí la comparación es por pareja de tema y tono, sin contar cuántas veces aparece. Es decir, se convierte la lista en un conjunto y se mira si la pareja está o no. Esto es distinto del programa de la especificación 03, que sí cuenta las veces. Es a propósito: el rival es más simple.
6. Escribe el resultado y enseña el resumen.

## Línea de comandos

```
python3 src/reglas.py
```

No tiene opciones. Siempre usa la hoja entera.

## Lo que no hace

- No llama a ningún modelo. No gasta dinero.
- No entiende el texto. Solo busca palabras.
- No distingue ironía, sarcasmo ni dobles sentidos. Eso es parte de la gracia: enseñar dónde se rompe.
- No cambia el léxico según los resultados. El léxico se escribe una vez y no se ajusta mirando las marcas. Si se ajustara, la comparación no valdría nada: el rival estaría haciendo trampa.

## Cómo se comprueba que funciona

Con una hoja de prueba de tres reseñas y un léxico corto.

1. **Frase con elogio.** Una frase que hable de comida con una palabra de elogio. Saca un juicio positivo de comida con la frase entera.
2. **Frase con queja.** Una frase que hable de servicio con una palabra de queja. Saca un juicio negativo de servicio.
3. **Frase con las dos caras.** Una frase que hable de comida con elogio y queja a la vez. Saca dos juicios, uno positivo y uno negativo.
4. **Frase sin pista.** Una frase que no hable de ningún tema. No saca nada.
5. **Repetidos.** Dos frases idénticas. Solo queda un juicio.
6. **Comparación.** Con tres reseñas marcadas a mano, la precisión y el recuerdo se calculan a mano y tienen que coincidir con lo que enseña el programa.

## Dependencias

Solo la librería estándar de Python. No importa el programa de la especificación 01, porque no habla con ningún modelo. Nada que instalar.

## Anexo. El léxico que produjo los números publicados

Este es el léxico exacto que se usó para medir. Se escribió de una vez y no se ajustó después. Si lo cambias, los números cambian y hay que volver a medir. Cada tema tiene tres listas: pistas de que la frase va de ese tema, palabras de elogio y palabras de queja. Las listas son expresiones regulares, así que `ric[oa]s?` encuentra `rico`, `rica`, `ricos` y `ricas`.

### comida

- Pistas: `gilda|brava|bravioli|tapa|raci[oó]n|plato|comida|carta|tosta|bocadillo|anchoa|vermut|vino|cerveza|copa|callos|ensaladilla|patata|pulpo|mollete|piparra|calamar|tortilla|postre|caf[eé]|chicharro|chicharr|mayonesa|queso|jam[oó]n|aceituna|encurtid|sabor|producto|bebida|comimos|pedimos|bocata|s[aá]ndwich|pan|carne|pescado|helado|vino`
- Elogio: `ric[oa]s?|delicios|espectacular|riqu[ií]sim|buen[ií]sim|estupend|exquisit|sabros|genialid|casero|fresc|muy buen|estaba buen|nos gust|de 10|incre[ií]ble|perfect|buen[ií]sim`
- Queja: `sos[oa]|sin sabor|corrient|regular|seco|seca|ranci|de bote|industrial|peor|mal[ií]sim|ins[ií]pid|congelad|duro|dura|no son para tanto|no me gust|arenos|espinas|apenas ten|condelad|sabor a nada|floj|decepcion`

### servicio

- Pistas: `servicio|camarer|personal|staff|trato|atenci[oó]n|atend|nos atiend|mesero|emplead|due[ñn]`
- Elogio: `amab|simp[aá]tic|maj[oa]|atent|profesional|correct|agradable|sonrisa|un 10|encantador|servicial|r[aá]pid|eficac`
- Queja: `borde|maleducad|malas maneras|mal trato|desorganizad|brusc|dej[oó] bastante que desear|poca atenci[oó]n|fr[ií]o|no nos hicieron caso|ignor|se mostr|mal educad|chulo|prepotent|no nos dej|denegad`

### precio

- Pistas: `precio|car[oa]|barat|euros|€|cuenta|cost|vale|pagamos|pagas|car[ií]sim|dinero|ticket`
- Elogio: `barat|razonable|correct|bien de precio|s[uú]per precio|merece la pena|normal|asequible|econ[oó]mic|no es caro`
- Queja: `car[oa]s?|car[ií]sim|elevad|sobreprecio|inflad|no merece|un ojo|abusiv|pasada|desproporcionad`

### ambiente

- Pistas: `ambiente|local|sitio|lugar|terraza|m[uú]sica|decoraci[oó]n|ruido|barrio|peque|lleno|aforo|encanto|est[eé]tica|mesa|barra|ba[ñn]o|rollo|bail|futbol|f[uú]tbol|concierto|paredes|luz|acogedor`
- Elogio: `encanto|acogedor|agradable|chul|aut[eé]ntic|bonit|guap|relajad|animad|se est[aá] bien|cool|muy bien montado|buen ambiente|precios|gusta el sitio|buena m[uú]sica|aire|espectacular`
- Queja: `ruidos|reducid|peque|abarrotad|cuesta moverse|no hay sitio|cutre|feo|suci|inc[oó]mod|apretad|sin aire|caos|desventaja`

### espera

- Pistas: `espera|esperar|esperamos|cola|tard|minutos|lent`
- Elogio: `al momento|sin esperar|no esperamos|enseguida|r[aá]pid|inmediat`
- Queja: `esperamos|tard|cola|minutos de espera|lent|nos tuvieron|media hora|se hizo largo|bastante tiempo`

## Cómo se trabaja esta especificación

- El trabajo va en la rama `spec-04-rules-baseline`, nunca directamente sobre `main`.
- Se abre una pull request contra `main` cuando la rama está lista.
- GitHub ejecuta las pruebas solo, en cada pull request. Si alguna falla, no se fusiona.
- Solo se fusiona con las pruebas en verde y con el visto bueno de Michel.
- El método completo, con los comandos, está en `docs/working-method.md`.
