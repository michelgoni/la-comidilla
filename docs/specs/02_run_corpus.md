# Especificación 02. Recorrer el corpus entero

Estado: la decisión de formato (un json por línea) quedó aprobada el 29 de octubre de 2026, en `docs/decisions/02_format_jsonl.md`. El resto de la especificación queda a la espera de que Michel pida la programación.

## Para qué existe

El programa anterior analiza una reseña. Este analiza muchas, sin que nadie tenga que lanzarlo cien veces. Recorre un fichero de reseñas, llama al modelo con cada una y guarda el resultado en un fichero que se puede cortar y retomar. Es el programa que produce los datos que después se miran y se agrupan por local.

No piensa nada nuevo. Toda la conversación con el modelo la hace el programa de la especificación 01, que este importa. Aquí solo se decide qué reseñas faltan, en qué orden, cuántas veces se reintenta un fallo y cómo se apunta el resultado.

## Qué recibe

- **Un fichero de reseñas.** Por defecto `data/full_corpus.json`, que tiene 1.173 reseñas con la forma `[local, estrellas, texto]`. La ruta se puede cambiar con la opción `--corpus`.
- **La configuración del modelo y el prompt**, igual que el programa de la especificación 01. Se leen del entorno o de `/home/ubuntu/.hermes/secrets/comidilla.env`.
- **Opciones por línea de comandos:** desde qué número empezar, hasta qué número llegar y cuántos reintentos hacer por reseña.

## Qué devuelve

1. **`labelled/result_corpus.jsonl`.** Un json por línea, una línea por reseña. Campos: numero, local, estrellas, caracteres, del_modelo (la lista de juicios si la respuesta era válida), forma_correcta (verdadero o falso), avisos (lista de problemas de forma), milisegundos, error, fecha, modelo y prompt.
2. **`labelled/errors_corpus.jsonl`.** Solo las reseñas que fallaron, con el mismo contenido. Sirve para volver a pasarlas sin buscar entre todas.
3. **Por pantalla:** cuántas reseñas hay, cuántas ya estaban hechas, cuántas quedan en este pase, el modelo y el prompt. Cada 25 reseñas enseña el avance, los fallos y una estimación de minutos que quedan. Al final, el total y el tiempo.

## Cómo funciona, paso a paso

1. Lee la configuración y el prompt. Si falta algo, para con un mensaje claro.
2. Carga el fichero de reseñas. Comprueba que es una lista no vacía.
3. Mira si el fichero de salida ya existe. Si existe, lee todas las líneas y apunta los números de reseña que ya están hechos. Esa es la memoria para retomar.
4. Calcula qué números faltan entre el principio y el final pedidos. Los que ya están hechos se saltan sin llamar al modelo.
5. Abre el fichero de salida y el de errores en modo añadir. No borra lo que ya había.
6. Para cada reseña pendiente: prepara el mensaje, llama al modelo con reintentos, revisa la forma de la respuesta y escribe una línea. Si hubo error, escribe también la línea en el fichero de errores.
7. Si el modelo falla, espera un poco antes de reintentar. La espera crece con cada intento: 2 segundos, 4, 6. Si se agotan los reintentos, apunta el fallo y sigue con la siguiente. Un fallo no para el recorrido.
8. Al final, cierra los ficheros y enseña el resumen.

## Cómo se guarda el resultado de cada reseña

- Si la respuesta era válida, `del_modelo` lleva la lista de juicios y `forma_correcta` es verdadero.
- Si la respuesta llegó pero la forma era incorrecta, `del_modelo` va vacío, `forma_correcta` es falso y `avisos` explica los problemas. Se guardan también los primeros 2.000 caracteres de la respuesta cruda, para poder mirar qué dijo el modelo.
- Si no hubo respuesta, `error` lleva el motivo y `del_modelo` va vacío.

## Línea de comandos

```
python3 src/correr_corpus.py                          (todas las que falten)
python3 src/correr_corpus.py --desde 0 --hasta 20      (solo las veinte primeras)
python3 src/correr_corpus.py --reintentos 3            (tres reintentos por fallo)
python3 src/correr_corpus.py --corpus otro.json        (otro fichero de reseñas)
```

## Lo que no hace

- No mide la calidad. Solo guarda lo que el modelo devuelve. La medición es otro programa.
- No cambia el prompt ni el modelo por su cuenta. Usa lo que le digan.
- No borra resultados anteriores. Si una reseña ya está hecha, la salta.
- No para el recorrido por un fallo. Lo apunta y sigue.

## Cómo se comprueba que funciona

Con un servidor falso y cinco reseñas de prueba.

1. **Primera pasada.** Se lanzan las cinco. El fichero de salida tiene cinco líneas, cada una un json válido. Cada línea lleva su número de reseña.
2. **Retomar.** Se borra la salida y se dejan dos hechas. Se vuelve a lanzar. Solo llama a las tres que faltan. Las dos primeras no se repiten.
3. **Fallo y reintento.** El servidor falso falla las dos primeras veces y acierta la tercera. Con `--reintentos 2`, la reseña acaba bien. Si se agotan los reintentos, la reseña aparece en el fichero de errores y el recorrido sigue.
4. **Rango.** Con `--desde 2 --hasta 4` solo procesa las reseñas 2 y 3. La 4 no entra, porque el final no se incluye.
5. **Sin configuración.** Para con un mensaje claro y no escribe nada.

## Dependencias

Solo la librería estándar de Python. Importa el programa de la especificación 01. Nada que instalar.

## Decisión propuesta, cámbiala si no te vale

El programa de la especificación 01 guarda cada llamada en un registro con sangría. Este programa guarda una línea por reseña. Son dos formatos distintos para el mismo tipo de información. La propuesta es que los dos usen un json por línea, para que todo se pueda leer igual y se pueda cortar sin romper el fichero. Si prefieres mantener el registro con sangría, se cambia aquí y en la especificación 01.

## Cómo se trabaja esta especificación

- El trabajo va en la rama `spec-02-run-corpus`, nunca directamente sobre `main`.
- Se abre una pull request contra `main` cuando la rama está lista.
- GitHub ejecuta las pruebas solo, en cada pull request. Si alguna falla, no se fusiona.
- Solo se fusiona con las pruebas en verde y con el visto bueno de Michel.
- El método completo, con los comandos, está en `docs/working-method.md`.
