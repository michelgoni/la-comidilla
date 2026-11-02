"""Tests for the rival without a model: the rule-based baseline."""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import rules

# A short lexicon, as the specification's exam asks for.
MINI = {
    "comida": {
        "pistas": r"comida|plato",
        "elogio": r"ric[oa]|buen[ií]sim",
        "queja": r"sos[oa]|malo",
    },
    "servicio": {
        "pistas": r"servicio|camarer",
        "elogio": r"amable",
        "queja": r"maleducad|borde",
    },
}


class SplitTest(unittest.TestCase):
    """The splitter must cut at the marks the specification names."""

    def test_cuts_after_punctuation_and_newlines(self):
        text = "Uno. Dos?\nTres... ¡Cuatro!\r\nCinco"
        self.assertEqual(
            rules.split_sentences(text),
            ["Uno.", "Dos?", "Tres...", "¡Cuatro!", "Cinco"],
        )

    def test_keeps_ellipsis_in_the_sentence(self):
        self.assertEqual(
            rules.split_sentences("Fue un desastre...\nSe fueron."),
            ["Fue un desastre...", "Se fueron."],
        )

    def test_skips_empty_pieces(self):
        self.assertEqual(rules.split_sentences("\n\n  .  \n"), ["."])


class JudgeTest(unittest.TestCase):
    """One sentence, one or zero judgements per face the lexicon finds."""

    def test_praise_sentence(self):
        text = "La comida estaba rica."
        self.assertEqual(
            rules.judge_sentence(text, MINI),
            [{"tema": "comida", "polaridad": "positivo", "trozo": text}],
        )

    def test_complaint_sentence(self):
        text = "El camarero fue maleducado."
        self.assertEqual(
            rules.judge_sentence(text, MINI),
            [{"tema": "servicio", "polaridad": "negativo", "trozo": text}],
        )

    def test_two_faced_sentence(self):
        text = "La comida estaba rica pero sosa."
        self.assertEqual(
            rules.judge_sentence(text, MINI),
            [
                {"tema": "comida", "polaridad": "positivo", "trozo": text},
                {"tema": "comida", "polaridad": "negativo", "trozo": text},
            ],
        )

    def test_hintless_sentence(self):
        self.assertEqual(rules.judge_sentence("Fuimos con amigos.", MINI), [])

    def test_praise_without_hint_is_silent(self):
        self.assertEqual(
            rules.judge_sentence("Riquísima pero no era comida.", MINI),
            [],
        )

    def test_matches_case_insensitively(self):
        text = "Comida Rica de verdad."
        self.assertEqual(
            rules.judge_sentence(text, MINI),
            [{"tema": "comida", "polaridad": "positivo", "trozo": text}],
        )

    def test_identical_sentences_leave_one_row(self):
        self.assertEqual(
            rules.judge_review("Comida rica. Comida rica.", MINI),
            [{"tema": "comida", "polaridad": "positivo", "trozo": "Comida rica."}],
        )

    def test_empty_review_has_no_rows(self):
        self.assertEqual(rules.judge_review("", MINI), [])


class ComparisonTest(unittest.TestCase):
    """The exam with three reviews, checked by hand as the spec asks."""

    def entries(self):
        """Build the three-review sheet exactly as the program would."""
        return [
            {
                "numero": 1,
                "mias": [{"tema": "comida", "polaridad": "positivo"}],
                "del_modelo": [
                    {"tema": "comida", "polaridad": "positivo", "trozo": "a"}
                ],
            },
            {
                "numero": 2,
                "mias": [{"tema": "servicio", "polaridad": "negativo"}],
                "del_modelo": [
                    {"tema": "servicio", "polaridad": "negativo", "trozo": "a"}
                ],
            },
            {
                "numero": 3,
                "mias": [{"tema": "comida", "polaridad": "mixed"}],
                "del_modelo": [
                    {"tema": "comida", "polaridad": "positivo", "trozo": "a"},
                    {"tema": "comida", "polaridad": "negativo", "trozo": "a"},
                ],
            },
        ]

    def test_totals_by_hand(self):
        # Own pairs 3, rules pairs 4; reviews 1 and 2 hit, review 3 misses.
        numbers = rules.totals(self.entries())
        self.assertEqual(numbers["mine_pairs"], 3)
        self.assertEqual(numbers["model_pairs"], 4)
        self.assertEqual(numbers["hits"], 2)
        self.assertEqual(numbers["rows"], 4)
        self.assertEqual(rules.format_ratio(2, 4), "0.500")
        self.assertEqual(rules.format_ratio(2, 3), "0.667")

    def test_topic_stats_by_hand(self):
        # Both mention comida in reviews 1 and 3; the tone matches in none,
        # because review 3 names mixed while the rival names positivo.
        stats = rules.topic_stats(self.entries())
        self.assertEqual(
            stats["comida"],
            {"coinciden": 2, "mencionan": 2, "tono": 1},
        )
        self.assertEqual(
            stats["servicio"],
            {"coinciden": 1, "mencionan": 1, "tono": 1},
        )

    def test_summary_prints_the_numbers(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            rules.show_summary(self.entries())
        out = buffer.getvalue()
        self.assertIn("Parejas tuyas: 3", out)
        self.assertIn("parejas del programa: 4", out)
        self.assertIn("aciertos: 2", out)
        self.assertIn("Precisión: 0.500", out)
        self.assertIn("recuerdo: 0.667", out)
        self.assertIn("Líneas de juicio del programa: 4", out)

    def test_ratio_without_denominator(self):
        self.assertEqual(rules.format_ratio(0, 0), "no aplica")


class RunTest(unittest.TestCase):
    """The program can be pointed at another sheet from the environment."""

    def test_environment_selects_another_sheet_and_result(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            sheet = folder / "hoja.json"
            sheet.write_text(
                json.dumps(
                    [
                        {
                            "numero": 5,
                            "local": "Local 5",
                            "estrellas": 4,
                            "texto": "La comida estaba rica.",
                            "valoraciones": [
                                {
                                    "tema": "comida",
                                    "polaridad": "positivo",
                                    "trozo": "La comida estaba rica",
                                }
                            ],
                            "marcada": True,
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            chosen = folder / "resultado.json"
            env = {
                "COMIDILLA_SHEET": str(sheet),
                "COMIDILLA_RESULT": str(chosen),
            }
            with mock.patch.dict(os.environ, env, clear=True), \
                    mock.patch.object(rules, "LABELLED_PATH", folder / "no.json"), \
                    mock.patch.object(
                        rules, "RULES_PATH", folder / "no_resultado.json"
                    ), redirect_stdout(io.StringIO()):
                rules.run()

            self.assertTrue(chosen.exists())
            self.assertFalse((folder / "no_resultado.json").exists())
            self.assertEqual(json.loads(chosen.read_text())[0]["numero"], 5)


if __name__ == "__main__":
    unittest.main()
