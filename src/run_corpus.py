"""Run the extraction over the whole corpus, one JSON line per review."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import extract

PROJECT = Path(__file__).resolve().parent.parent
DEFAULT_CORPUS_PATH = PROJECT / "data" / "full_corpus.json"
RESULT_PATH = PROJECT / "labelled" / "result_corpus.jsonl"
ERROR_PATH = PROJECT / "labelled" / "errors_corpus.jsonl"
DEFAULT_PROMPT_PATH = PROJECT / "prompts" / "prompt_v4.txt"
ENV_PROMPT = "COMIDILLA_PROMPT"

DEFAULT_RETRIES = 2
RETRY_DELAY_SECONDS = 2
PROGRESS_EVERY = 25
RAW_ANSWER_LIMIT = 2000


def load_saved_entries(path: Path) -> dict:
    """Return the last line saved per review; ignore unusable lines."""
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


def done_numbers(saved: dict, retry_failed: bool) -> set:
    """Return the reviews that count as done; failed ones may rejoin."""
    if retry_failed:
        return {
            number
            for number, entry in saved.items()
            if not entry.get("error")
        }
    return set(saved)


def drop_error_lines(path: Path, numbers: list) -> None:
    """Remove failed lines of retried reviews; the errors file keeps them."""
    if not path.exists():
        return

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SystemExit(
            f"Could not read the result file {path}: {exc}"
        ) from exc

    kept = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            entry = json.loads(stripped)
        except json.JSONDecodeError:
            kept.append(line)
            continue
        failed = (
            isinstance(entry, dict)
            and entry.get("numero") in numbers
            and entry.get("error")
        )
        if not failed:
            kept.append(line)

    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        "".join(line + "\n" for line in kept), encoding="utf-8"
    )
    temporary.replace(path)


def pending_numbers(total: int, start: int, end: int, done: set) -> list:
    """Return the numbers in the requested range that are still missing."""
    first = max(0, start)
    last = min(end, total)
    return [number for number in range(first, last) if number not in done]


def ask_with_retries(
    base_url: str, api_key: str, payload: dict, retries: int
) -> tuple:
    """Call the model; wait 2, 4, 6... seconds between attempts."""
    total_milliseconds = 0
    error = ""

    for attempt in range(retries + 1):
        started = time.perf_counter()
        try:
            raw, milliseconds = extract.call_model(base_url, api_key, payload)
            total_milliseconds += milliseconds
            return raw, total_milliseconds, ""
        except (SystemExit, Exception) as exc:
            total_milliseconds += int(
                (time.perf_counter() - started) * 1000
            )
            error = str(exc)
            if attempt < retries:
                time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))

    return "", total_milliseconds, error


def parse_judgments(cleaned_answer: str):
    """Turn the cleaned answer into a list, or return None if it is not one."""
    try:
        judgments = json.loads(cleaned_answer)
    except json.JSONDecodeError:
        return None
    return judgments if isinstance(judgments, list) else None


def build_entry(
    number: int,
    local: str,
    stars: object,
    text: str,
    judgments: list,
    problems: list,
    raw: str,
    milliseconds: int,
    error: str,
    model: str,
    prompt_name: str,
) -> dict:
    """Build one result row with the fields the specification asks for."""
    shape_is_right = not error and not problems
    return {
        "numero": number,
        "local": local,
        "estrellas": stars,
        "caracteres": len(text),
        "del_modelo": judgments if shape_is_right else [],
        "forma_correcta": shape_is_right,
        "avisos": problems,
        "milisegundos": milliseconds,
        "error": error,
        "fecha": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "modelo": model,
        "prompt": prompt_name,
        "respuesta_cruda": raw[:RAW_ANSWER_LIMIT] if problems else "",
    }


def write_entry(handle: object, entry: dict) -> None:
    """Append one JSON line and flush it so a cut leaves whole rows."""
    handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    handle.flush()


def print_start(
    total: int, done: int, pending: int, model: str, prompt_name: str
) -> None:
    """Show the size of the corpus, the saved work and this pass."""
    print(
        f"Corpus: {total} reseñas | ya hechas: {done} | "
        f"pendientes en este pase: {pending}"
    )
    print(f"Modelo: {model} | prompt: {prompt_name}")


def print_progress(
    processed: int,
    pending: int,
    number: int,
    local: str,
    judgments: int,
    failures: int,
    elapsed: float,
) -> None:
    """Show the pace and a rough estimate of the minutes still to go."""
    remaining = pending - processed
    minutes = 0
    if processed:
        minutes = round(elapsed / processed * remaining / 60)
    print(
        f"  {processed}/{pending} | {number} | {local} | "
        f"{judgments} juicios | fallos {failures} | quedan ~{minutes} min"
    )


def run(args: argparse.Namespace) -> None:
    """Read the pending reviews, call the model and append one line each."""
    config = extract.load_config()
    prompt_path = Path(os.environ.get(ENV_PROMPT, str(DEFAULT_PROMPT_PATH)))
    prompt = extract.load_prompt(prompt_path)
    reviews = extract.load_corpus(Path(args.corpus))

    total = len(reviews)
    end = total if args.end is None else min(args.end, total)
    saved = load_saved_entries(RESULT_PATH)
    done = done_numbers(saved, args.retry_failed)
    pending = pending_numbers(total, args.start, end, done)

    print_start(
        total, len(done), len(pending), config["model"], prompt_path.name
    )

    if not pending:
        print("Hechas en este pase: 0 | fallos: 0 | tiempo: 0.0 min")
        return

    if args.retry_failed:
        drop_error_lines(RESULT_PATH, pending)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ERROR_PATH.parent.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    processed = 0
    failures = 0

    with RESULT_PATH.open("a", encoding="utf-8") as result_file, \
            ERROR_PATH.open("a", encoding="utf-8") as error_file:
        for number in pending:
            local, stars, text = extract.pick_review(reviews, number)
            payload = extract.build_payload(config["model"], prompt, text)
            raw, milliseconds, error = ask_with_retries(
                config["base_url"],
                config["api_key"],
                payload,
                args.retries,
            )

            problems = []
            judgments = []
            if not error:
                cleaned = extract.clean_answer(raw)
                problems = extract.check_shape(cleaned, text)
                if not problems:
                    judgments = parse_judgments(cleaned)
                    if judgments is None:
                        problems = ["La respuesta no es una lista."]
                        judgments = []

            if error:
                failures += 1

            entry = build_entry(
                number,
                local,
                stars,
                text,
                judgments,
                problems,
                raw,
                milliseconds,
                error,
                config["model"],
                prompt_path.name,
            )
            write_entry(result_file, entry)
            if error:
                write_entry(error_file, entry)

            processed += 1
            if processed % PROGRESS_EVERY == 0:
                print_progress(
                    processed,
                    len(pending),
                    number,
                    local,
                    len(judgments),
                    failures,
                    time.perf_counter() - started,
                )

    elapsed = time.perf_counter() - started
    print(
        f"Hechas en este pase: {processed} | fallos: {failures} | "
        f"tiempo: {elapsed / 60:.1f} min"
    )


def main() -> None:
    """Read the options and walk every review that is still missing."""
    parser = argparse.ArgumentParser(
        description="Recorrer el corpus entero de reseñas de La Comidilla."
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=DEFAULT_CORPUS_PATH,
        help="Fichero de reseñas. Por defecto data/full_corpus.json.",
    )
    parser.add_argument(
        "--desde",
        dest="start",
        metavar="N",
        type=int,
        default=0,
        help="Primera reseña del pase. Empieza en 0.",
    )
    parser.add_argument(
        "--hasta",
        dest="end",
        metavar="N",
        type=int,
        default=None,
        help="Final del pase, sin incluirlo. Por defecto, el final.",
    )
    parser.add_argument(
        "--reintentos",
        dest="retries",
        metavar="N",
        type=int,
        default=DEFAULT_RETRIES,
        help="Reintentos por reseña si el modelo falla.",
    )
    parser.add_argument(
        "--reintentar-fallidas",
        dest="retry_failed",
        action="store_true",
        help="Volver a pasar las reseñas cuya línea lleva error.",
    )
    args = parser.parse_args()

    if args.start < 0:
        parser.error("--desde no puede ser negativo.")
    if args.end is not None and args.end < 0:
        parser.error("--hasta no puede ser negativo.")
    if args.retries < 0:
        parser.error("--reintentos no puede ser negativo.")

    run(args)


if __name__ == "__main__":
    main()
