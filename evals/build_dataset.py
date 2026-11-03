"""Build the promptfoo test set from the blind sheet.

One test case per review, with only the four fields the model is allowed to
see. The marks stay out: if they travelled in the file the model could see
them, and the exam would stop measuring anything.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SHEET_PATH = PROJECT / "labelled" / "reviews_blind.json"
OUTPUT_PATH = PROJECT / "evals" / "dataset.jsonl"
SHEET_ENV = "COMIDILLA_SHEET"
OUTPUT_ENV = "COMIDILLA_DATASET"
FIELDS = ("numero", "local", "estrellas", "texto")


def load_sheet(path: Path) -> list:
    """Read the blind sheet; stop before building a set that cannot be trusted."""
    try:
        reviews = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"Could not read the sheet {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"The sheet {path} is not valid JSON: {exc}") from exc

    if not isinstance(reviews, list) or not reviews:
        raise SystemExit(f"The sheet {path} must be a non-empty list.")
    return reviews


def build_rows(reviews: list) -> list:
    """Turn each review into one test case; refuse one that is missing a field."""
    rows = []
    for position, review in enumerate(reviews):
        if not isinstance(review, dict):
            raise SystemExit(f"Entry {position} in the sheet is not an object.")

        missing = [field for field in FIELDS if field not in review]
        if missing:
            raise SystemExit(
                f"Review {review.get('numero', position)} has no "
                f"{', '.join(missing)}."
            )
        if not isinstance(review["numero"], int):
            raise SystemExit(f"Review {position} has a numero that is not a whole number.")
        if not isinstance(review["texto"], str) or not review["texto"].strip():
            raise SystemExit(f"Review {review['numero']} has no text.")

        rows.append({"vars": {field: review[field] for field in FIELDS}})
    return rows


def write_dataset(rows: list, path: Path) -> None:
    """Write one JSON line per case, the shape promptfoo reads as a test file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    """Rebuild the generated set and say how many reviews went in."""
    sheet_path = Path(os.environ.get(SHEET_ENV, str(SHEET_PATH)))
    output_path = Path(os.environ.get(OUTPUT_ENV, str(OUTPUT_PATH)))

    reviews = load_sheet(sheet_path)
    rows = build_rows(reviews)
    write_dataset(rows, output_path)

    marks = sum(len(review.get("valoraciones", [])) for review in reviews)
    print(f"Sheet: {sheet_path.name} | reviews: {len(rows)} | marks: {marks}")
    print(f"Written: {output_path} | test cases: {len(rows)}")


if __name__ == "__main__":
    main()
