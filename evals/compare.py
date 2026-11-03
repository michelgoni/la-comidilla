"""Print a promptfoo run as the same table src/recount.py prints.

The counting is not rewritten here. Every number comes from src/recount.py,
which in turn uses src/measure.py: this program only reads promptfoo's JSON,
turns each answer into the row shape those programs already understand, and
prints. If a number here disagrees with recount.py, the bug is in this bridge
or in the request, never in a second counter.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "src"))

import extract  # noqa: E402
import measure  # noqa: E402
import recount  # noqa: E402

RESULTS_PATH = PROJECT / "evals" / "results.json"
SHEET_PATH = PROJECT / "labelled" / "reviews_blind.json"
SAVED_PATH = PROJECT / "labelled" / "result_blind.jsonl"
SHEET_ENV = "COMIDILLA_SHEET"


def load_results(path: Path) -> list:
    """Read promptfoo's output file; keep the answer rows and nothing else."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"Could not read the results {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"The results {path} are not valid JSON: {exc}") from exc

    rows = data.get("results", data) if isinstance(data, dict) else data
    if isinstance(rows, dict):
        rows = rows.get("results", [])
    if not isinstance(rows, list) or not rows:
        raise SystemExit(f"The results {path} hold no answer rows.")
    return rows


def answer_text(row: dict) -> str:
    """Return the model text of one promptfoo row, or an empty string."""
    response = row.get("response")
    if isinstance(response, dict):
        output = response.get("output")
    else:
        output = row.get("output")
    return output if isinstance(output, str) else ""


def build_entries(rows: list) -> tuple:
    """Turn each answer into the row shape recount reads, counting the empties."""
    entries = {}
    empty = []
    for row in rows:
        numero = (row.get("vars") or {}).get("numero")
        if not isinstance(numero, int):
            continue
        text = answer_text(row)
        if not text.strip():
            empty.append(numero)
            entries[numero] = {"numero": numero, "del_modelo": []}
            continue
        judgments = measure.parse_judgments(extract.clean_answer(text))
        entries[numero] = {"numero": numero, "del_modelo": judgments or []}
    return entries, sorted(empty)


def points(hits: int, first: int, second: int | None = None):
    """Read one ratio back as a number, so two tables can be subtracted."""
    text = recount.ratio(hits, first) if second is None else recount.f1_text(
        hits, first, second
    )
    try:
        return float(text) * 100
    except ValueError:
        return None


def show_block(name: str, entries: dict, marked: list) -> dict:
    """Print one table with recount's own functions and return its headline."""
    measured = sum(1 for review in marked if review["numero"] in entries)
    pairs = recount.pair_totals(entries, marked)
    rows = recount.row_totals(entries, marked)
    mean_f1, reviews_with_marks = recount.review_f1_mean(entries, marked)

    print()
    print(f"{name}: {measured} de {len(marked)} reseñas")
    print("Por pareja (lo que decide)")
    print(
        f"- Aciertos: {pairs['hits']} | parejas emitidas: {pairs['emitted']} "
        f"| parejas tuyas: {pairs['own']}"
    )
    print(
        f"- Precisión: {recount.ratio(pairs['hits'], pairs['emitted'])} | "
        f"recuerdo: {recount.ratio(pairs['hits'], pairs['own'])} | "
        f"F1: {recount.f1_text(pairs['hits'], pairs['emitted'], pairs['own'])}"
    )
    print(f"- Inventadas: {pairs['invented']} | omitidas: {pairs['missed']}")
    print()
    print("Por fila (repetición)")
    print(
        f"- Aciertos: {rows['hits']} | filas: {rows['emitted']} | "
        f"precisión: {recount.ratio(rows['hits'], rows['emitted'])} | "
        f"recuerdo: {recount.ratio(rows['hits'], rows['own'])} | "
        f"F1: {recount.f1_text(rows['hits'], rows['emitted'], rows['own'])}"
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
    for topic, count in recount.topic_totals(entries, marked).items():
        print(
            f"- {topic}: {count['marks']} marcas, {count['hits']} aciertos, "
            f"{count['emitted']} emitidas | "
            f"recuerdo {recount.ratio(count['hits'], count['marks'])} | "
            f"precisión {recount.ratio(count['hits'], count['emitted'])}"
        )

    return {
        "precision": points(pairs["hits"], pairs["emitted"]),
        "recall": points(pairs["hits"], pairs["own"]),
        "f1": points(pairs["hits"], pairs["emitted"], pairs["own"]),
    }


def main() -> None:
    """Print the promptfoo table, the saved table and the gap between them."""
    parser = argparse.ArgumentParser(
        description="Print a promptfoo run with the project's own counter."
    )
    parser.add_argument("--results", default=str(RESULTS_PATH))
    parser.add_argument("--saved", default=str(SAVED_PATH))
    args = parser.parse_args()

    sheet_path = Path(os.environ.get(SHEET_ENV, str(SHEET_PATH)))
    marked = measure.load_marked(sheet_path)
    rows = load_results(Path(args.results))
    entries, empty = build_entries(rows)

    print(
        f"Sheet: {sheet_path.name} | {len(marked)} reseñas | "
        f"{sum(len(review['valoraciones']) for review in marked)} marcas"
    )
    print(f"Answers: {len(rows)} rows | empty: {len(empty)}")
    if empty:
        print(f"Empty reviews: {', '.join(str(numero) for numero in empty)}")

    new = show_block("promptfoo", entries, marked)

    saved_path = Path(args.saved)
    if saved_path.exists():
        saved = recount.load_source(saved_path)
        if saved:
            old = show_block(f"Guardado ({saved_path.name})", saved, marked)
            print()
            print("Diferencia promptfoo menos guardado (puntos)")
            for key, label in (
                ("precision", "Precisión por pareja"),
                ("recall", "Recuerdo por pareja"),
                ("f1", "F1 por pareja"),
            ):
                print(f"- {label}: {new[key] - old[key]:+.1f}")


if __name__ == "__main__":
    main()
