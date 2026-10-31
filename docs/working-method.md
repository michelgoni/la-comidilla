# Método de trabajo

Fecha: 29 de octubre de 2026.

Una rama por especificación, una pull request por cambio, y las pruebas automáticas antes de fusionar.

## La norma

1. **Una rama por especificación.** La rama lleva el nombre de lo que implementa: `spec-01-extraction`, `spec-02-run-corpus`, `spec-03-measure-against-marks`, `spec-04-rules-baseline`. Lo que no es una especificación, como el mantenimiento del proyecto, también lleva su propia rama.
2. **`main` no se escribe nunca directamente.** Todo cambio llega por una pull request.
3. **Las pruebas se ejecutan solas.** El flujo `.github/workflows/tests.yml` lanza la suite entera en cada pull request y en cada subida a `main`.
4. **Solo se fusiona con las pruebas en verde.** Una prueba en rojo significa que no se fusiona, por pequeño que sea el cambio.
5. **Un tema por pull request.** Si la pull request se llena de un segundo tema, se parte en dos.
6. **Michel fusiona.** El asistente abre la pull request, lee las comprobaciones y cuenta el resultado. La fusión la decide Michel, salvo que diga lo contrario.
7. **Los mensajes de commit van en inglés**, en una línea y en imperativo.

## En comandos

```
git checkout main
git pull
git checkout -b spec-02-run-corpus

... trabajo, en pasos pequeños ...

python3 -m unittest discover -s tests     (en local, antes de subir)

git add <ficheros>
git commit -m "Add the corpus runner"
git push -u origin spec-02-run-corpus

gh pr create --base main --fill
gh pr checks --watch                      (esperar a que las pruebas estén en verde)
```

## Por qué

- Sin ramas, un cambio a medias rompe `main` y no hay forma limpia de volver atrás.
- Sin pruebas automáticas, la suite se queda en rojo sin que nadie lo note. Ya ha pasado: el primer commit del proyecto tenía una prueba que fallaba, y nadie lo vio hasta que se montó este flujo.
- Sin una comprobación obligatoria en `main`, la norma depende de la memoria de cada uno.
