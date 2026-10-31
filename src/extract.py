"""Extract judgments from a single restaurant review."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
CORPUS_PATH = Path("/home/ubuntu/gastronomy/gilda-report/corpus_reviews.json")
SECRETS_PATH = Path("/home/ubuntu/.hermes/secrets/comidilla.env")
REGISTRY_PATH = PROJECT / "data" / "registry.json"
DEFAULT_PROMPT_PATH = PROJECT / "prompts" / "prompt_v4.txt"

THEMES = ("comida", "servicio", "precio", "ambiente", "espera")
POLARITIES = ("positivo", "negativo", "mixto")

ENV_BASE_URL = "COMIDILLA_BASE_URL"
ENV_MODEL = "COMIDILLA_MODEL"
ENV_API_KEY = "COMIDILLA_API_KEY"
ENV_PROMPT = "COMIDILLA_PROMPT"


def load_config() -> dict:
    """Load model settings; fail fast so no call runs unconfigured."""
    config = {
        "base_url": os.environ.get(ENV_BASE_URL, "").strip(),
        "model": os.environ.get(ENV_MODEL, "").strip(),
        "api_key": os.environ.get(ENV_API_KEY, "").strip(),
    }

    if not all(config.values()) and SECRETS_PATH.exists():
        try:
            lines = SECRETS_PATH.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise SystemExit(
                f"Could not read the secrets file: {exc}"
            ) from exc
        names = {
            ENV_BASE_URL: "base_url",
            ENV_MODEL: "model",
            ENV_API_KEY: "api_key",
        }
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            name = name.strip()
            if name.startswith("export "):
                name = name[7:].strip()
            if name in names and not config[names[name]]:
                config[names[name]] = value.strip().strip('"').strip("'")

    missing = []
    if not config["base_url"]:
        missing.append(ENV_BASE_URL)
    if not config["model"]:
        missing.append(ENV_MODEL)
    if missing:
        raise SystemExit(
            "Missing model configuration: " + ", ".join(missing) + "."
        )

    return config


def load_corpus(path: Path) -> list:
    """Load the review list; reject bad files before any model call."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"Could not read the corpus {path}: {exc}") from exc

    try:
        reviews = json.loads(content)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"The corpus {path} is not valid JSON: {exc}"
        ) from exc

    if not isinstance(reviews, list) or not reviews:
        raise SystemExit(f"The corpus {path} must be a non-empty list.")
    for position, review in enumerate(reviews):
        if (
            not isinstance(review, (list, tuple))
            or len(review) < 3
            or not isinstance(review[2], str)
        ):
            raise SystemExit(
                f"Review {position} in the corpus does not have the form "
                f"[place, stars, text]."
            )

    return reviews


def pick_review(reviews: list, index: int) -> tuple:
    """Return one review by number; stop when the number is out of range."""
    if not isinstance(index, int) or index < 0 or index >= len(reviews):
        raise SystemExit(
            f"Review number {index} does not exist. There are "
            f"{len(reviews)} reviews (0 to {len(reviews) - 1})."
        )

    review = reviews[index]
    if (
        not isinstance(review, (list, tuple))
        or len(review) < 3
        or not isinstance(review[2], str)
    ):
        raise SystemExit(
            f"Review {index} does not have the form [place, stars, text]."
        )

    return review[0], review[1], review[2]


def load_prompt(path: Path) -> str:
    """Read the prompt; refuse an empty one so the model cannot improvise."""
    try:
        prompt = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"Could not read the prompt {path}: {exc}") from exc

    if not prompt.strip():
        raise SystemExit(f"The prompt {path} is empty.")

    return prompt


def build_payload(model: str, prompt: str, review_text: str) -> dict:
    """Build the request body; keep it separate so it can be checked."""
    return {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f'Reseña:\n"""\n{review_text}\n"""',
            },
        ],
    }


def call_model(
    base_url: str, api_key: str, payload: dict, timeout: int = 120
) -> tuple:
    """Send the request; report each failure where it happened."""
    url = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-Session-Id": os.urandom(8).hex(),
    }
    request = urllib.request.Request(
        url, data=body, headers=headers, method="POST"
    )

    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(
            f"The model returned error {exc.code}: {detail[:400]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"Could not connect to the model: {exc.reason}"
        ) from exc
    except TimeoutError as exc:
        raise SystemExit(
            f"The model took longer than {timeout} seconds."
        ) from exc
    elapsed = int((time.perf_counter() - started) * 1000)

    try:
        answer = json.loads(raw)["choices"][0]["message"]["content"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise SystemExit(
            f"The response does not contain the expected text: {raw}"
        ) from exc
    if not isinstance(answer, str):
        raise SystemExit(
            f"The response does not contain the expected text: {raw}"
        )

    return answer, elapsed


def clean_answer(raw: str) -> str:
    """Strip code fences; keep only the JSON list the model returned."""
    text = raw.strip()
    text = re.sub(
        r"^```[ \t]*(?:json)?[ \t]*\r?\n?",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\r?\n?```$", "", text).strip()
    text = text.replace("```", "").strip()

    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end > start:
        return text[start : end + 1]

    return text


def check_shape(judgments: object, review_text: str) -> list:
    """Check every judgment; report problems instead of fixing them."""
    problems = []

    if isinstance(judgments, str):
        try:
            judgments = json.loads(judgments)
        except json.JSONDecodeError:
            try:
                judgments = json.loads(clean_answer(judgments))
            except json.JSONDecodeError as exc:
                return [f"La respuesta no es un JSON válido: {exc}"]
    if not isinstance(judgments, list):
        return ["La respuesta no es una lista."]

    normalized_review = " ".join(review_text.split())

    for position, judgment in enumerate(judgments, start=1):
        if not isinstance(judgment, dict):
            problems.append(f"El juicio {position} no es un objeto.")
            continue

        for field in ("tema", "polaridad", "trozo"):
            if field not in judgment:
                problems.append(
                    f"Al juicio {position} le falta el campo {field}."
                )

        tema = judgment.get("tema")
        if "tema" in judgment and tema not in THEMES:
            problems.append(
                f"El juicio {position} tiene un tema no válido: {tema!r}. "
                f"Temas permitidos: {', '.join(THEMES)}."
            )

        polaridad = judgment.get("polaridad")
        if "polaridad" in judgment and polaridad not in POLARITIES:
            problems.append(
                f"El juicio {position} tiene una polaridad "
                f"no válida: {polaridad!r}. "
                f"Polaridades permitidas: {', '.join(POLARITIES)}."
            )

        trozo = judgment.get("trozo")
        if "trozo" not in judgment:
            continue
        if not isinstance(trozo, str) or not trozo.strip():
            problems.append(
                f"El juicio {position} no trae un trozo de texto."
            )
            continue

        parts = re.split(r"\s+\.\.\.\s+", trozo)
        for part in parts:
            if not part.strip():
                problems.append(f"El juicio {position} tiene un trozo vacío.")
            elif " ".join(part.split()) not in normalized_review:
                problems.append(
                    f"El trozo del juicio {position} no aparece "
                    f"en la reseña: {part!r}."
                )

    return problems


def append_registry(entry: dict) -> None:
    """Append one call to the registry; never lose earlier entries."""
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    if REGISTRY_PATH.exists():
        content = REGISTRY_PATH.read_text(encoding="utf-8")
        if content.strip():
            try:
                previous = json.loads(content)
            except json.JSONDecodeError:
                previous = None
            if isinstance(previous, list):
                lines = [
                    json.dumps(item, ensure_ascii=False)
                    for item in previous
                ]
            elif isinstance(previous, dict):
                lines = [json.dumps(previous, ensure_ascii=False)]
            else:
                lines = [
                    line for line in content.splitlines() if line.strip()
                ]

    lines.append(json.dumps(entry, ensure_ascii=False))
    REGISTRY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """Run one review end to end; show the result and log the call."""
    parser = argparse.ArgumentParser(
        description="Extract judgments from one review of the Gilda corpus."
    )
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help="Review number to analyse. Starts at 0.",
    )
    args = parser.parse_args()

    config = load_config()
    reviews = load_corpus(CORPUS_PATH)
    local, stars, review_text = pick_review(reviews, args.index)
    prompt_path = Path(os.environ.get(ENV_PROMPT, str(DEFAULT_PROMPT_PATH)))
    prompt = load_prompt(prompt_path)
    payload = build_payload(config["model"], prompt, review_text)

    user_message = payload["messages"][1]["content"]
    entry = {
        "fecha": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "modelo": config["model"],
        "direccion": config["base_url"],
        "numero": args.index,
        "local": local,
        "estrellas": stars,
        "prompt_sistema": prompt,
        "mensaje_usuario": user_message,
        "respuesta": "",
        "milisegundos": 0,
        "error": "",
    }

    print(f"Reseña {args.index}: {local} ({stars} estrellas)")
    print(review_text)
    print()

    try:
        raw, milliseconds = call_model(
            config["base_url"], config["api_key"], payload
        )
    except SystemExit as exc:
        entry["error"] = str(exc)
        append_registry(entry)
        raise

    entry["respuesta"] = raw
    entry["milisegundos"] = milliseconds

    cleaned = clean_answer(raw)
    problems = check_shape(cleaned, review_text)

    print("Respuesta cruda del modelo:")
    print(raw)
    print()
    if problems:
        print("Forma correcta: no")
        print("Problemas encontrados:")
        for problem in problems:
            print(f"- {problem}")
    else:
        print("Forma correcta: sí")
        print("Problemas encontrados: ninguno")
    print(f"Tiempo: {milliseconds} ms")

    append_registry(entry)


if __name__ == "__main__":
    main()
