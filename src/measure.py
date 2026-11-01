"""Measure the model's judgments against the hand-labelled sheet."""

from __future__ import annotations

import json
import os
import time
from collections import Counter
from pathlib import Path

import extract

PROJECT = Path(__file__).resolve().parent.parent
LABELLED_PATH = PROJECT / "labelled" / "reviews_to_label.json"
RESULT_PATH = PROJECT / "labelled" / "result_marked.jsonl"
DEFAULT_PROMPT_PATH = PROJECT / "prompts" / "prompt_v4.txt"
ENV_PROMPT = "COMIDILLA_PROMPT"

RAW_ANSWER_LIMIT = 2000


def load_marked(path: Path) -> list:
    """Load the hand-labelled sheet; keep only the marked reviews."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(
            f"Could not read the labelled sheet {path}: {exc}"
        ) from exc

    try:
        reviews = json.loads(content)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"The labelled sheet {path} is not valid JSON: {exc}"
        ) from exc

    if not isinstance(reviews, list) or not reviews:
        raise SystemExit(f"The labelled sheet {path} must be a non-empty list.")

    marked = []
    for position, review in enumerate(reviews):
        if not isinstance(review, dict):
            raise SystemExit(
                f"Entry {position} in the labelled sheet is not an object."
            )
        if not isinstance(review.get("numero"), int):
            raise SystemExit(
                f"Entry {position} in the labelled sheet has no valid numero."
            )
        if not isinstance(review.get("texto"), str):
            raise SystemExit(
                f"Review {review['numero']} in the labelled sheet has no text."
            )
        if not isinstance(review.get("valoraciones"), list):
            raise SystemExit(
                f"Review {review['numero']} has no valid valoraciones list."
            )
        if review.get("marcada"):
            marked.append(review)

    if not marked:
        raise SystemExit(
            "No review in the labelled sheet is marked. "
            "Mark some with marcada in true before measuring."
        )

    return marked


def load_saved_entries(path: Path) -> dict:
    """Return the saved rows by number; ignore unusable lines."""
    if not path.exists():
        return {}

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SystemExit(
            f"Could not read the result file {path}: {exc}"
        ) from exc

    saved = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict) and isinstance(entry.get("numero"), int):
            saved[entry["numero"]] = entry

    return saved


def parse_judgments(cleaned_answer: str):
    """Turn the cleaned answer into a list, or None if it is not one."""
    try:
        judgments = json.loads(cleaned_answer)
    except json.JSONDecodeError:
        return None
    return judgments if isinstance(judgments, list) else None


def pair_counts(judgments: list) -> Counter:
    """Count how many times each (tema, polaridad) pair appears."""
    counts = Counter()
    for judgment in judgments:
        if not isinstance(judgment, dict):
            continue
        counts[(str(judgment.get("tema")), str(judgment.get("polaridad")))] += 1
    return counts


def show_pair(pair: tuple) -> str:
    """Render one (tema, polaridad) pair the way the sheet reads them."""
    return f"{pair[0]} / {pair[1]}"


def compare(mine: list, model_judgments: list) -> dict:
    """Compare by pair and count hits, invented and missed judgements."""
    mine_counts = pair_counts(mine)
    model_counts = pair_counts(model_judgments)

    aciertos = sum((mine_counts & model_counts).values())
    inventadas = sum((model_counts - mine_counts).values())
    omitidas = sum((mine_counts - model_counts).values())

    return {
        "aciertos": aciertos,
        "inventadas": inventadas,
        "omitidas": omitidas,
    }


def build_entry(
    marked_review: dict,
    mine: list,
    judgments: list,
    problems: list,
    raw: str,
    milliseconds: int,
    model: str,
    prompt_name: str,
) -> dict:
    """Build one result row with the fields the specification asks for."""
    return {
        "numero": marked_review["numero"],
        "local": marked_review["local"],
        "estrellas": marked_review["estrellas"],
        "mias": mine,
        "del_modelo": judgments,
        "avisos": problems,
        "comparacion": compare(mine, judgments),
        "respuesta_cruda": raw[:RAW_ANSWER_LIMIT],
        "milisegundos": milliseconds,
        "modelo": model,
        "prompt": prompt_name,
        "fecha": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def write_entry(handle: object, entry: dict) -> None:
    """Append one JSON line and flush it so a cut leaves whole rows."""
    handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    handle.flush()


def measure_review(config: dict, prompt: str, marked_review: dict) -> tuple:
    """Call the model once and return the judgements, avisos and raw text.

    The judgements are kept even when their shape has problems; it is
    only when the whole answer cannot be read as a list that they are lost.
    """
    payload = extract.build_payload(
        config["model"], prompt, marked_review["texto"]
    )
    raw, milliseconds = extract.call_model(
        config["base_url"], config["api_key"], payload
    )

    cleaned = extract.clean_answer(raw)
    judgments = parse_judgments(cleaned)
    if judgments is None:
        judgments = []
        problems = extract.check_shape(cleaned, marked_review["texto"])
    else:
        problems = extract.check_shape(judgments, marked_review["texto"])
    return judgments, problems, raw, milliseconds


def pair_differences(entries: dict, marked: list) -> dict:
    """Add up per pair the judgements the model invented and missed.

    The entries only carry totals, so the pairs come again from the two
    judgement lists of every marked review that has been measured.
    """
    invented = Counter()
    missed = Counter()

    for review in marked:
        entry = entries.get(review["numero"])
        if not entry:
            continue
        mine_counts = pair_counts(entry.get("mias", []))
        model_counts = pair_counts(entry.get("del_modelo", []))
        invented += model_counts - mine_counts
        missed += mine_counts - model_counts

    return {
        "invented": invented,
        "missed": missed,
    }


def most_common(counter: Counter) -> tuple:
    """Return the pair with the highest count, or None when there is none."""
    if not counter:
        return None
    pair, count = counter.most_common(1)[0]
    return show_pair(pair), count


def show_summary(entries: dict, marked: list) -> None:
    """Add up every measured review and show the exam results."""
    measured = [
        entry for entry in (entries.get(r["numero"]) for r in marked)
        if entry
    ]
    if not measured:
        print("Reseñas medidas: 0. No hay nada que resumir.")
        return

    mine_total = sum(len(entry.get("mias", [])) for entry in measured)
    model_total = sum(len(entry.get("del_modelo", [])) for entry in measured)
    aciertos = sum(entry["comparacion"]["aciertos"] for entry in measured)
    inventadas = sum(entry["comparacion"]["inventadas"] for entry in measured)
    omitidas = sum(entry["comparacion"]["omitidas"] for entry in measured)

    precision = (
        f"{aciertos / model_total:.3f}" if model_total else "no aplica"
    )
    recall = f"{aciertos / mine_total:.3f}" if mine_total else "no aplica"

    avisos_total = sum(len(entry.get("avisos", [])) for entry in measured)
    empty_implies_missed = sum(
        1 for entry in measured
        if entry.get("mias") and not entry.get("del_modelo")
    )

    differences = pair_differences(entries, marked)
    top_invented = most_common(differences["invented"])
    top_missed = most_common(differences["missed"])

    print()
    print("Resumen del examen")
    print(f"- Reseñas medidas: {len(measured)}")
    print(f"- Juicios tuyos: {mine_total} | juicios del modelo: {model_total}")
    print(f"- Aciertos (tema y tono): {aciertos}")
    print(f"- Precisión: {precision} | recuerdo: {recall}")
    print(f"- Inventados: {inventadas} | omitidos: {omitidas}")
    print(f"- Avisos de forma: {avisos_total}")
    print(
        f"- Reseñas que el modelo dejó vacías sin serlo: "
        f"{empty_implies_missed}"
    )
    print()
    print("Lo que más inventa: ", end="")
    if top_invented:
        print(f"{top_invented[0]} ({top_invented[1]})")
    else:
        print("nada")
    print("Lo que más se deja: ", end="")
    if top_missed:
        print(f"{top_missed[0]} ({top_missed[1]})")
    else:
        print("nada")


def run() -> None:
    """Measure every marked review that is not measured yet."""
    config = extract.load_config()
    prompt_path = Path(os.environ.get(ENV_PROMPT, str(DEFAULT_PROMPT_PATH)))
    prompt = extract.load_prompt(prompt_path)
    marked = load_marked(LABELLED_PATH)
    saved = load_saved_entries(RESULT_PATH)

    pending = [review for review in marked if review["numero"] not in saved]
    already = len(marked) - len(pending)
    print(
        f"Hoja: {len(marked)} reseñas marcadas | ya medidas: {already} | "
        f"pendientes: {len(pending)}"
    )
    print(f"Modelo: {config['model']} | prompt: {prompt_path.name}")

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("a", encoding="utf-8") as result_file:
        for review in pending:
            judgments, problems, raw, milliseconds = measure_review(
                config, prompt, review
            )
            entry = build_entry(
                review,
                review["valoraciones"],
                judgments,
                problems,
                raw,
                milliseconds,
                config["model"],
                prompt_path.name,
            )
            write_entry(result_file, entry)
            saved[review["numero"]] = entry
            print(
                f"  Reseña {review['numero']} ({review['local']}): "
                f"{entry['comparacion']['aciertos']} aciertos | "
                f"{entry['comparacion']['inventadas']} inventadas | "
                f"{entry['comparacion']['omitidas']} omitidas"
            )

    show_summary(saved, marked)


def main() -> None:
    """Measure the whole hand-labelled sheet with no options at all."""
    run()


if __name__ == "__main__":
    main()
