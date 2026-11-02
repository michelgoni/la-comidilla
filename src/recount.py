"""Recount the published exam numbers from the saved answers.

The numbers in the README used to be counted by hand. This program reads
the hand-labelled sheet and the saved answers of every program and prints
the counts again, so the published table has a command behind it.
It never calls a model and never writes a file.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import measure

PROJECT = Path(__file__).resolve().parent.parent
SHEET_PATH = PROJECT / "labelled" / "reviews_to_label.json"
SOURCES = (
    ("Modelo", PROJECT / "labelled" / "result_marked.jsonl"),
    ("Rival de reglas", PROJECT / "labelled" / "result_rules.json"),
)
TOPICS = ("ambiente", "comida", "espera", "precio", "servicio")
SHEET_ENV = "COMIDILLA_SHEET"
MODEL_ENV = "COMIDILLA_RESULT"
RULES_ENV = "COMIDILLA_RULES"


def sheet_version(path: Path) -> str:
    """Return the fingerprint of the sheet, so a result can name the exam."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json_list(path: Path) -> dict:
    """Load a result saved as one JSON list, keeping the usable entries."""
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(entries, list):
        return {}
    return {
        entry["numero"]: entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("numero"), int)
    }


def load_source(path: Path) -> dict:
    """Load a result file in either saved shape, json lines or one list."""
    if path.suffix == ".jsonl":
        return measure.load_saved_entries(path)
    return load_json_list(path)


def saved_mismatches(entries: dict, marked: list) -> list:
    """List the reviews whose saved marks no longer match the sheet.

    A saved result only speaks about the exam it was measured against, so
    a mismatch has to be shown instead of silently averaged away.
    """
    different = []
    for review in marked:
        entry = entries.get(review["numero"])
        if not entry:
            continue
        if entry.get("mias") != review["valoraciones"]:
            different.append(review["numero"])
    return different


def pair_totals(entries: dict, marked: list) -> dict:
    """Add up the counts with each pair once per review, the headline."""
    hits = emitted = own = invented = missed = 0
    for review in marked:
        entry = entries.get(review["numero"])
        if not entry:
            continue
        mine = measure.pair_set(review["valoraciones"])
        other = measure.pair_set(entry.get("del_modelo", []))
        hits += len(mine & other)
        emitted += len(other)
        own += len(mine)
        invented += len(other - mine)
        missed += len(mine - other)
    return {
        "hits": hits,
        "emitted": emitted,
        "own": own,
        "invented": invented,
        "missed": missed,
    }


def row_totals(entries: dict, marked: list) -> dict:
    """Add up the same counts with every row a program emits, the noise."""
    hits = emitted = own = invented = missed = 0
    for review in marked:
        entry = entries.get(review["numero"])
        if not entry:
            continue
        mine = measure.pair_counts(review["valoraciones"])
        other = measure.pair_counts(entry.get("del_modelo", []))
        hits += sum((mine & other).values())
        emitted += sum(other.values())
        own += sum(mine.values())
        invented += sum((other - mine).values())
        missed += sum((mine - other).values())
    return {
        "hits": hits,
        "emitted": emitted,
        "own": own,
        "invented": invented,
        "missed": missed,
    }


def one_review_f1(marks: list, judgments: list) -> float:
    """Return the F1 of one review, or zero when it has nothing to match."""
    mine = measure.pair_set(marks)
    other = measure.pair_set(judgments)
    hits = len(mine & other)
    precision = hits / len(other) if other else 0.0
    recall = hits / len(mine) if mine else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def review_f1_mean(entries: dict, marked: list) -> tuple:
    """Return the mean F1 over the reviews that carry at least one mark."""
    scores = [
        one_review_f1(review["valoraciones"], entries[review["numero"]].get("del_modelo", []))
        for review in marked
        if review["numero"] in entries and review["valoraciones"]
    ]
    return (sum(scores) / len(scores) if scores else 0.0, len(scores))


def topic_totals(entries: dict, marked: list) -> dict:
    """Count, per topic, the marked pairs, the hits and the pairs emitted."""
    stats = {topic: {"marks": 0, "hits": 0, "emitted": 0} for topic in TOPICS}
    for review in marked:
        entry = entries.get(review["numero"])
        if not entry:
            continue
        mine = measure.pair_set(review["valoraciones"])
        other = measure.pair_set(entry.get("del_modelo", []))
        for topic, count in stats.items():
            own_topic = {pair for pair in mine if pair[0] == topic}
            other_topic = {pair for pair in other if pair[0] == topic}
            count["marks"] += len(own_topic)
            count["hits"] += len(own_topic & other_topic)
            count["emitted"] += len(other_topic)
    return stats


def ratio(hits: int, total: int) -> str:
    """Return the ratio with three decimals, or a word when it cannot be."""
    return f"{hits / total:.3f}" if total else "no aplica"


def f1_text(hits: int, emitted: int, own: int) -> str:
    """Return the F1 of two counters already added up."""
    precision = hits / emitted if emitted else 0.0
    recall = hits / own if own else 0.0
    if precision + recall == 0:
        return "0.000"
    return f"{2 * precision * recall / (precision + recall):.3f}"


def show_source(name: str, entries: dict, marked: list) -> None:
    """Show the three counts of one program over the same exam."""
    measured = sum(1 for review in marked if review["numero"] in entries)
    pairs = pair_totals(entries, marked)
    rows = row_totals(entries, marked)
    mean_f1, reviews_with_marks = review_f1_mean(entries, marked)

    print()
    print(f"{name}: {measured} de {len(marked)} reseñas")
    print("Por pareja (titular)")
    print(
        f"- Aciertos: {pairs['hits']} | parejas emitidas: {pairs['emitted']} "
        f"| parejas tuyas: {pairs['own']}"
    )
    print(
        f"- Precisión: {ratio(pairs['hits'], pairs['emitted'])} | "
        f"recuerdo: {ratio(pairs['hits'], pairs['own'])} | "
        f"F1: {f1_text(pairs['hits'], pairs['emitted'], pairs['own'])}"
    )
    print(f"- Inventadas: {pairs['invented']} | omitidas: {pairs['missed']}")
    print()
    print("Por fila (repetición)")
    print(
        f"- Aciertos: {rows['hits']} | filas: {rows['emitted']} | "
        f"precisión: {ratio(rows['hits'], rows['emitted'])} | "
        f"recuerdo: {ratio(rows['hits'], rows['own'])} | "
        f"F1: {f1_text(rows['hits'], rows['emitted'], rows['own'])}"
    )
    print(
        f"- Inventadas por fila: {rows['invented']} | "
        f"omitidas por fila: {rows['missed']}"
    )
    print(
        f"- F1 medio por reseña: {mean_f1:.3f} "
        f"({reviews_with_marks} reseñas con marcas)"
    )
    print()
    print("Por tema (parejas: marcas, aciertos, emitidas)")
    for topic, count in topic_totals(entries, marked).items():
        print(
            f"- {topic}: {count['marks']} marcas, {count['hits']} aciertos, "
            f"{count['emitted']} emitidas | "
            f"recuerdo {ratio(count['hits'], count['marks'])} | "
            f"precisión {ratio(count['hits'], count['emitted'])}"
        )

    different = saved_mismatches(entries, marked)
    if different:
        print()
        print(
            "Aviso: las marcas guardadas no coinciden con la hoja en las "
            f"reseñas {', '.join(str(number) for number in different)}. "
            "La cuenta usa la hoja actual."
        )


def run() -> None:
    """Recount every saved source against the current sheet and show it."""
    sheet_path = Path(os.environ.get(SHEET_ENV, str(SHEET_PATH)))
    sources = (
        ("Modelo", Path(os.environ.get(MODEL_ENV, str(SOURCES[0][1])))),
        ("Rival de reglas", Path(os.environ.get(RULES_ENV, str(SOURCES[1][1])))),
    )
    marked = measure.load_marked(sheet_path)
    print(
        f"Hoja: {sheet_path.name} | {len(marked)} reseñas | "
        f"{sum(len(review['valoraciones']) for review in marked)} marcas | "
        f"sha256 {sheet_version(sheet_path)[:12]}"
    )
    for name, path in sources:
        entries = load_source(path)
        if not entries:
            print()
            print(f"{name}: sin resultados guardados en {path.name}")
            continue
        show_source(name, entries, marked)


def main() -> None:
    """Recount the published numbers with no options and no model call."""
    run()


if __name__ == "__main__":
    main()
