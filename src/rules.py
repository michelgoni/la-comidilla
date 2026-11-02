"""The rival without a model: rule-based judgements from fixed word lists.

If this program beats or matches the model, the model adds nothing.
It never calls a model, never spends money, and never changes the lexicon.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
LABELLED_PATH = PROJECT / "labelled" / "reviews_to_label.json"
RULES_PATH = PROJECT / "labelled" / "result_rules.json"
SHEET_ENV = "COMIDILLA_SHEET"
RESULT_ENV = "COMIDILLA_RESULT"

POSITIVE = "positivo"
NEGATIVE = "negativo"

# The lexicon as written for the published numbers; it is never tuned
# against the marks, or the comparison would be rigged.
LEXICON = {
    "comida": {
        "pistas": r"gilda|brava|bravioli|tapa|raci[oó]n|plato|comida|carta|tosta|bocadillo|anchoa|vermut|vino|cerveza|copa|callos|ensaladilla|patata|pulpo|mollete|piparra|calamar|tortilla|postre|caf[eé]|chicharro|chicharr|mayonesa|queso|jam[oó]n|aceituna|encurtid|sabor|producto|bebida|comimos|pedimos|bocata|s[aá]ndwich|pan|carne|pescado|helado|vino",
        "elogio": r"ric[oa]s?|delicios|espectacular|riqu[ií]sim|buen[ií]sim|estupend|exquisit|sabros|genialid|casero|fresc|muy buen|estaba buen|nos gust|de 10|incre[ií]ble|perfect|buen[ií]sim",
        "queja": r"sos[oa]|sin sabor|corrient|regular|seco|seca|ranci|de bote|industrial|peor|mal[ií]sim|ins[ií]pid|congelad|duro|dura|no son para tanto|no me gust|arenos|espinas|apenas ten|condelad|sabor a nada|floj|decepcion",
    },
    "servicio": {
        "pistas": r"servicio|camarer|personal|staff|trato|atenci[oó]n|atend|nos atiend|mesero|emplead|due[ñn]",
        "elogio": r"amab|simp[aá]tic|maj[oa]|atent|profesional|correct|agradable|sonrisa|un 10|encantador|servicial|r[aá]pid|eficac",
        "queja": r"borde|maleducad|malas maneras|mal trato|desorganizad|brusc|dej[oó] bastante que desear|poca atenci[oó]n|fr[ií]o|no nos hicieron caso|ignor|se mostr|mal educad|chulo|prepotent|no nos dej|denegad",
    },
    "precio": {
        "pistas": r"precio|car[oa]|barat|euros|€|cuenta|cost|vale|pagamos|pagas|car[ií]sim|dinero|ticket",
        "elogio": r"barat|razonable|correct|bien de precio|s[uú]per precio|merece la pena|normal|asequible|econ[oó]mic|no es caro",
        "queja": r"car[oa]s?|car[ií]sim|elevad|sobreprecio|inflad|no merece|un ojo|abusiv|pasada|desproporcionad",
    },
    "ambiente": {
        "pistas": r"ambiente|local|sitio|lugar|terraza|m[uú]sica|decoraci[oó]n|ruido|barrio|peque|lleno|aforo|encanto|est[eé]tica|mesa|barra|ba[ñn]o|rollo|bail|futbol|f[uú]tbol|concierto|paredes|luz|acogedor",
        "elogio": r"encanto|acogedor|agradable|chul|aut[eé]ntic|bonit|guap|relajad|animad|se est[aá] bien|cool|muy bien montado|buen ambiente|precios|gusta el sitio|buena m[uú]sica|aire|espectacular",
        "queja": r"ruidos|reducid|peque|abarrotad|cuesta moverse|no hay sitio|cutre|feo|suci|inc[oó]mod|apretad|sin aire|caos|desventaja",
    },
    "espera": {
        "pistas": r"espera|esperar|esperamos|cola|tard|minutos|lent",
        "elogio": r"al momento|sin esperar|no esperamos|enseguida|r[aá]pid|inmediat",
        "queja": r"esperamos|tard|cola|minutos de espera|lent|nos tuvieron|media hora|se hizo largo|bastante tiempo",
    },
}

# Cut after . ! ? or an ellipsis when space or a line break follows,
# and at every line break, so each piece is one whole sentence.
SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+|\r\n|\r|\n")


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
            "Mark some with marcada in true before running."
        )

    return marked


def split_sentences(text: str) -> list:
    """Cut the text into whole sentences, keeping the final punctuation.

    Each sentence is kept whole because the snippet rules require a
    literal copy of the review, character by character.
    """
    sentences = []
    for piece in SENTENCE_SPLIT.split(text):
        piece = piece.strip()
        if piece:
            sentences.append(piece)
    return sentences


def judge_sentence(sentence: str, lexicon: dict) -> list:
    """Judge one sentence against every topic of the lexicon.

    A hint for a topic opens the topic; a praise word adds one positive
    row and a complaint word adds one negative row, with the whole
    sentence as the snippet.
    """
    found = []
    for topic, lists in lexicon.items():
        if not re.search(lists["pistas"], sentence, re.IGNORECASE):
            continue
        for name, polarity in (("elogio", POSITIVE), ("queja", NEGATIVE)):
            if re.search(lists[name], sentence, re.IGNORECASE):
                found.append(
                    {"tema": topic, "polaridad": polarity, "trozo": sentence}
                )
    return found


def dedup(judgments: list) -> list:
    """Drop repeated rows (same topic, tone and snippet), keeping the first.

    Identical rows say nothing new and the comparison works on pairs.
    """
    seen = set()
    unique = []
    for judgment in judgments:
        key = (judgment["tema"], judgment["polaridad"], judgment["trozo"])
        if key not in seen:
            seen.add(key)
            unique.append(judgment)
    return unique


def judge_review(text: str, lexicon: dict) -> list:
    """Judge a whole review: split it, judge each sentence and dedupe."""
    judgments = []
    for sentence in split_sentences(text):
        judgments.extend(judge_sentence(sentence, lexicon))
    return dedup(judgments)


def pair_set(judgments: list) -> set:
    """Return the (tema, polaridad) pairs in the list, each kept once.

    The rival counts pairs, not rows, so hearing one thing twice does
    not make its answer better.
    """
    return {
        (str(judgment.get("tema")), str(judgment.get("polaridad")))
        for judgment in judgments
        if isinstance(judgment, dict)
    }


def format_ratio(hits: int, total: int) -> str:
    """Return the ratio with three decimals, or a word when it has none."""
    return f"{hits / total:.3f}" if total else "no aplica"


def totals(entries: list) -> dict:
    """Add up the pair totals over all entries for the headline numbers."""
    mine_pairs = model_pairs = hits = 0
    for entry in entries:
        own = pair_set(entry.get("mias", []))
        rules = pair_set(entry.get("del_modelo", []))
        hits += len(own & rules)
        mine_pairs += len(own)
        model_pairs += len(rules)
    return {
        "mine_pairs": mine_pairs,
        "model_pairs": model_pairs,
        "hits": hits,
        "rows": sum(len(entry.get("del_modelo", [])) for entry in entries),
    }


def topic_stats(entries: list) -> dict:
    """Count, per topic, whose reviews mention it, match it and match the tone.

    The tone matches when, once the topic coincides, both name the same
    polarity for it in that review.
    """
    stats = {
        topic: {"coinciden": 0, "mencionan": 0, "tono": 0}
        for topic in sorted(LEXICON)
    }
    for entry in entries:
        own = pair_set(entry.get("mias", []))
        rules = pair_set(entry.get("del_modelo", []))
        for topic, count in stats.items():
            own_topic = {pair for pair in own if pair[0] == topic}
            rules_topic = {pair for pair in rules if pair[0] == topic}
            if own_topic or rules_topic:
                count["mencionan"] += 1
            if own_topic and rules_topic:
                count["coinciden"] += 1
                if own_topic & rules_topic:
                    count["tono"] += 1
    return stats


def show_summary(entries: list) -> None:
    """Print the exam summary the specification asks for."""
    numbers = totals(entries)
    stats = topic_stats(entries)
    topic_matches = sum(count["coinciden"] for count in stats.values())
    tone_matches = sum(count["tono"] for count in stats.values())

    print()
    print("Resumen del rival sin modelo")
    print(f"- Reseñas: {len(entries)}")
    print(
        f"- Parejas tuyas: {numbers['mine_pairs']} | "
        f"parejas del programa: {numbers['model_pairs']} | "
        f"aciertos: {numbers['hits']}"
    )
    print(
        f"- Precisión: {format_ratio(numbers['hits'], numbers['model_pairs'])}"
        f" | recuerdo: {format_ratio(numbers['hits'], numbers['mine_pairs'])}"
    )
    print()
    print("Por tema, coincide el tema de las reseñas que lo mencionan:")
    for topic, count in stats.items():
        print(
            f"- {topic}: "
            f"{count['coinciden']} de {count['mencionan']}"
        )
    print(
        f"- Cuando coincide el tema, el tono también coincide en "
        f"{tone_matches} de {topic_matches} parejas de reseña y tema"
    )
    print(f"- Líneas de juicio del programa: {numbers['rows']}")


def write_result(entries: list, path: Path) -> None:
    """Write every entry to the result file, one object per review."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as result_file:
        json.dump(entries, result_file, ensure_ascii=False, indent=2)
        result_file.write("\n")


def run() -> None:
    """Judge every marked review with the lexicon and compare with the marks."""
    sheet_path = Path(os.environ.get(SHEET_ENV, str(LABELLED_PATH)))
    result_path = Path(os.environ.get(RESULT_ENV, str(RULES_PATH)))
    marked = load_marked(sheet_path)
    print(f"Hoja: {sheet_path.name} | {len(marked)} reseñas marcadas")

    entries = []
    for review in marked:
        rules = judge_review(review["texto"], LEXICON)
        entries.append(
            {
                "numero": review["numero"],
                "mias": review["valoraciones"],
                "del_modelo": rules,
            }
        )

    write_result(entries, result_path)
    print(f"Resultado en {result_path}")
    show_summary(entries)


def main() -> None:
    """Judge the whole hand-labelled sheet with no options at all."""
    run()


if __name__ == "__main__":
    main()
