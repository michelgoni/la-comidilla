"""Tests for the program that recounts the saved results."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import measure
import recount


def sheet_review(number: int, marks: list) -> dict:
    """Build one marked review with the fields the sheet needs."""
    return {
        "numero": number,
        "local": "Bar de prueba",
        "estrellas": 4,
        "texto": "Texto de prueba.",
        "valoraciones": marks,
        "marcada": True,
    }


def judgment(tema: str, polaridad: str, trozo: str = "texto") -> dict:
    """Build one judgment with the three fields the project uses."""
    return {"tema": tema, "polaridad": polaridad, "trozo": trozo}


class PairTotalsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.marked = [
            sheet_review(
                1,
                [
                    judgment("comida", "positivo"),
                    judgment("servicio", "negativo"),
                ],
            ),
            sheet_review(2, [judgment("ambiente", "positivo")]),
        ]

    def test_counts_each_pair_once_per_review(self) -> None:
        entries = {
            1: {
                "numero": 1,
                "del_modelo": [
                    judgment("comida", "positivo"),
                    judgment("comida", "positivo", "otro trozo"),
                    judgment("precio", "negativo"),
                ],
            },
            2: {"numero": 2, "del_modelo": []},
        }
        totals = recount.pair_totals(entries, self.marked)
        self.assertEqual(
            {"hits": 1, "emitted": 2, "own": 3, "invented": 1, "missed": 2},
            totals,
        )

    def test_counts_each_row_when_asked(self) -> None:
        entries = {
            1: {
                "numero": 1,
                "del_modelo": [
                    judgment("comida", "positivo"),
                    judgment("comida", "positivo", "otro trozo"),
                    judgment("precio", "negativo"),
                ],
            },
            2: {"numero": 2, "del_modelo": []},
        }
        totals = recount.row_totals(entries, self.marked)
        # A repeated pair does not add hits: only the marked count hits,
        # and the extra row counts as invented, which is the whole point
        # of keeping this count apart from the headline.
        self.assertEqual(
            {"hits": 1, "emitted": 3, "own": 3, "invented": 2, "missed": 2},
            totals,
        )

    def test_skips_reviews_without_a_saved_answer(self) -> None:
        entries = {1: {"numero": 1, "del_modelo": []}}
        totals = recount.pair_totals(entries, self.marked)
        self.assertEqual(2, totals["own"])
        self.assertEqual(0, totals["hits"])


class F1Test(unittest.TestCase):
    def test_one_review_f1_by_hand(self) -> None:
        marks = [judgment("comida", "positivo")]
        judgments = [
            judgment("comida", "positivo"),
            judgment("precio", "negativo"),
        ]
        self.assertAlmostEqual(2 / 3, recount.one_review_f1(marks, judgments))

    def test_one_review_f1_is_zero_when_nothing_matches(self) -> None:
        self.assertEqual(
            0.0,
            recount.one_review_f1(
                [judgment("comida", "positivo")],
                [judgment("precio", "negativo")],
            ),
        )

    def test_mean_only_counts_reviews_with_marks(self) -> None:
        marked = [
            sheet_review(1, [judgment("comida", "positivo")]),
            sheet_review(2, []),
        ]
        entries = {
            1: {"numero": 1, "del_modelo": [judgment("comida", "positivo")]},
            2: {"numero": 2, "del_modelo": []},
        }
        mean, reviews = recount.review_f1_mean(entries, marked)
        self.assertEqual(1, reviews)
        self.assertAlmostEqual(1.0, mean)


class TopicTotalsTest(unittest.TestCase):
    def test_counts_marks_hits_and_emitted_pairs_per_topic(self) -> None:
        marked = [
            sheet_review(
                1,
                [
                    judgment("comida", "positivo"),
                    judgment("servicio", "negativo"),
                ],
            )
        ]
        entries = {
            1: {
                "numero": 1,
                "del_modelo": [
                    judgment("comida", "positivo"),
                    judgment("comida", "negativo"),
                ],
            }
        }
        stats = recount.topic_totals(entries, marked)
        self.assertEqual(
            {"marks": 1, "hits": 1, "emitted": 2}, stats["comida"]
        )
        self.assertEqual(
            {"marks": 1, "hits": 0, "emitted": 0}, stats["servicio"]
        )


class SheetMismatchTest(unittest.TestCase):
    def test_reports_the_reviews_whose_saved_marks_changed(self) -> None:
        marked = [sheet_review(1, [judgment("comida", "positivo")])]
        entries = {
            1: {"numero": 1, "mias": [judgment("comida", "negativo")]},
        }
        self.assertEqual([1], recount.saved_mismatches(entries, marked))

    def test_says_nothing_when_the_saved_marks_match(self) -> None:
        marked = [sheet_review(1, [judgment("comida", "positivo")])]
        entries = {
            1: {"numero": 1, "mias": [judgment("comida", "positivo")]},
        }
        self.assertEqual([], recount.saved_mismatches(entries, marked))


class SheetVersionTest(unittest.TestCase):
    def test_fingerprint_changes_when_the_sheet_changes(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "sheet.json"
            path.write_text("[]", encoding="utf-8")
            first = recount.sheet_version(path)
            path.write_text("[1]", encoding="utf-8")
            second = recount.sheet_version(path)
        self.assertNotEqual(first, second)
        self.assertEqual(64, len(first))

    def test_measure_and_recount_agree_on_the_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "sheet.json"
            path.write_text(json.dumps([{"numero": 1}]), encoding="utf-8")
            self.assertEqual(
                measure.sheet_version(path), recount.sheet_version(path)
            )


class SourceLoadingTest(unittest.TestCase):
    def test_reads_a_json_list_and_ignores_bad_entries(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "result.json"
            path.write_text(
                json.dumps(
                    [
                        {"numero": 3, "del_modelo": []},
                        {"numero": "x"},
                        "basura",
                    ]
                ),
                encoding="utf-8",
            )
            entries = recount.load_source(path)
        self.assertEqual([3], list(entries))

    def test_reads_json_lines(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "result.jsonl"
            path.write_text(
                '{"numero": 4, "del_modelo": []}\n', encoding="utf-8"
            )
            entries = recount.load_source(path)
        self.assertEqual([4], list(entries))


class PublishedNumbersTest(unittest.TestCase):
    def test_the_current_files_give_the_published_numbers(self) -> None:
        project = Path(__file__).resolve().parent.parent
        sheet = project / "labelled" / "reviews_to_label.json"
        model = project / "labelled" / "result_marked.jsonl"
        rules = project / "labelled" / "result_rules.json"
        if not (sheet.exists() and model.exists() and rules.exists()):
            self.skipTest("the private exam files are not present")

        # The pinned numbers only speak about the sheet they were measured
        # on. If the sheet changes, the check is skipped, not failed.
        if not recount.sheet_version(sheet).startswith("46cc8b2296e4"):
            self.skipTest("the sheet is not the one behind the published numbers")

        marked = measure.load_marked(sheet)
        saved = {
            "model": recount.pair_totals(recount.load_source(model), marked),
            "rules": recount.pair_totals(recount.load_source(rules), marked),
        }

        self.assertEqual(49, saved["model"]["hits"])
        self.assertEqual(52, saved["model"]["emitted"])
        self.assertEqual(3, saved["model"]["invented"])
        self.assertEqual(7, saved["model"]["missed"])
        self.assertEqual(35, saved["rules"]["hits"])
        self.assertEqual(44, saved["rules"]["emitted"])
        self.assertEqual(9, saved["rules"]["invented"])
        self.assertEqual(21, saved["rules"]["missed"])

    def test_recount_agrees_with_the_measure_program(self) -> None:
        project = Path(__file__).resolve().parent.parent
        sheet = project / "labelled" / "reviews_to_label.json"
        model = project / "labelled" / "result_marked.jsonl"
        if not (sheet.exists() and model.exists()):
            self.skipTest("the private exam files are not present")

        marked = measure.load_marked(sheet)
        entries = recount.load_source(model)
        recounted = recount.pair_totals(entries, marked)
        measured = measure.pair_totals(
            [entry for entry in (entries.get(r["numero"]) for r in marked) if entry]
        )
        self.assertEqual(measured[0], recounted["hits"])
        self.assertEqual(measured[1], recounted["emitted"])
        self.assertEqual(measured[2], recounted["own"])
        self.assertEqual(measured[3], recounted["invented"])
        self.assertEqual(measured[4], recounted["missed"])


if __name__ == "__main__":
    unittest.main()
