"""Tests for the program that measures against the hand-labelled sheet."""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import threading
import unittest
from collections import Counter
from contextlib import contextmanager, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import extract
import measure

REVIEW_TEXT = "La comida estaba buenísima y el servicio un desastre."

MINE = [
    {"tema": "comida", "polaridad": "positivo", "trozo": "buenísima"},
    {"tema": "servicio", "polaridad": "negativo", "trozo": "desastre"},
]

GOOD_REPEAT = json.dumps(
    [
        {
            "tema": "comida",
            "polaridad": "positivo",
            "trozo": "La comida estaba buenísima",
        }
    ],
    ensure_ascii=False,
)


def model_answer(content: str) -> str:
    """Wrap one answer in the shape an OpenAI-compatible server returns."""
    return json.dumps({"choices": [{"message": {"content": content}}]})


@contextmanager
def fake_server(responses: list):
    """Run a local server with a sequence of (status, body) responses."""
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8", errors="replace")
            try:
                calls.append(json.loads(body))
            except json.JSONDecodeError:
                calls.append({})
            status, text = responses[min(len(calls) - 1, len(responses) - 1)]
            data = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/v1", calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def write_sheet(folder: Path, rows: list) -> Path:
    """Write a labelled sheet from (numero, marked, mine) rows."""
    reviews = [
        {
            "numero": numero,
            "local": f"Local {numero}",
            "estrellas": 4,
            "texto": REVIEW_TEXT,
            "valoraciones": mine,
            "nota": "",
            "marcada": marked,
        }
        for numero, marked, mine in rows
    ]
    path = folder / "reviews_to_label.json"
    path.write_text(json.dumps(reviews, ensure_ascii=False), encoding="utf-8")
    return path


def read_lines(path: Path) -> list:
    """Read a JSONL file into a list of dictionaries."""
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class CompareTests(unittest.TestCase):
    """The comparison counts pairs by how many times they appear."""

    def test_two_mine_one_model_counts_each_side_once(self) -> None:
        model_judgments = [
            {"tema": "comida", "polaridad": "positivo", "trozo": "x"},
            {"tema": "precio", "polaridad": "negativo", "trozo": "y"},
        ]
        comparison = measure.compare(MINE, model_judgments)

        self.assertEqual(comparison["aciertos"], 1)
        self.assertEqual(comparison["inventadas"], 1)
        self.assertEqual(comparison["omitidas"], 1)

    def test_repeats_count_as_many_times_as_they_appear(self) -> None:
        mine = [
            {"tema": "comida", "polaridad": "negativo"},
            {"tema": "comida", "polaridad": "negativo"},
        ]
        model_judgments = [{"tema": "comida", "polaridad": "negativo"}]

        comparison = measure.compare(mine, model_judgments)

        self.assertEqual(comparison["aciertos"], 1)
        self.assertEqual(comparison["inventadas"], 0)
        self.assertEqual(comparison["omitidas"], 1)

    def test_counts_do_not_care_about_the_snippet(self) -> None:
        mine = [{"tema": "comida", "polaridad": "positivo", "trozo": "uno"}]
        model_judgments = [
            {"tema": "comida", "polaridad": "positivo", "trozo": "otro"}
        ]

        comparison = measure.compare(mine, model_judgments)

        self.assertEqual(comparison["aciertos"], 1)

    def test_pair_counts_keep_invalid_judgments_for_the_comparison(self) -> None:
        counts = measure.pair_counts(
            [{"tema": "comida", "polaridad": "coral"}]
        )

        self.assertEqual(counts, Counter({("comida", "coral"): 1}))


class MeasureTests(unittest.TestCase):
    """The meter measures the sheet, resumes and survives bad answers."""

    def run_main(self, folder: Path, base_url: str, sheet: Path) -> tuple:
        """Run the program over the test sheet and capture what it prints."""
        result = folder / "result_marked.jsonl"
        prompt = folder / "prompt_de_prueba.txt"
        prompt.write_text("Prompt de prueba", encoding="utf-8")

        env = {
            "COMIDILLA_BASE_URL": base_url,
            "COMIDILLA_MODEL": "modelo-de-prueba",
            "COMIDILLA_API_KEY": "",
            "COMIDILLA_PROMPT": str(prompt),
        }

        output = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(
                    extract, "SECRETS_PATH", folder / "missing.env"
                ), mock.patch.object(
                    measure, "LABELLED_PATH", sheet
                ), mock.patch.object(
                    measure, "RESULT_PATH", result
                ), redirect_stdout(output):
            measure.main()

        return result, output.getvalue()

    def test_simple_case_counts_by_hand(self) -> None:
        answer = model_answer(
            json.dumps(
                [
                    {
                        "tema": "comida",
                        "polaridad": "positivo",
                        "trozo": "La comida estaba buenísima",
                    },
                    {
                        "tema": "precio",
                        "polaridad": "negativo",
                        "trozo": "un desastre",
                    },
                ],
                ensure_ascii=False,
            )
        )
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            sheet = write_sheet(folder, [(11, True, MINE)])
            with fake_server([(200, answer)]) as (base_url, calls):
                result, printed = self.run_main(folder, base_url, sheet)

            entries = read_lines(result)

        self.assertEqual(len(calls), 1)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["numero"], 11)
        self.assertEqual(entry["mias"], MINE)
        self.assertEqual(len(entry["del_modelo"]), 2)
        self.assertEqual(entry["comparacion"]["aciertos"], 1)
        self.assertEqual(entry["comparacion"]["inventadas"], 1)
        self.assertEqual(entry["comparacion"]["omitidas"], 1)
        self.assertEqual(
            {"aciertos": 1, "inventadas": 1, "omitidas": 1},
            entry["comparacion"],
        )
        self.assertEqual(entry["prompt"], "prompt_de_prueba.txt")
        self.assertEqual(entry["modelo"], "modelo-de-prueba")
        self.assertIn("Precisión: 0.500", printed)
        self.assertIn("recuerdo: 0.500", printed)
        self.assertIn("Lo que más inventa: precio / negativo", printed)
        self.assertIn("Lo que más se deja: servicio / negativo", printed)

    def test_malformed_answer_saves_empty_list_and_an_aviso(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            sheet = write_sheet(folder, [(12, True, MINE)])
            with fake_server(
                [(200, model_answer("No fue una lista"))]
            ) as (base_url, calls):
                result, printed = self.run_main(folder, base_url, sheet)

            entries = read_lines(result)

        self.assertEqual(len(calls), 1)
        self.assertEqual(entries[0]["del_modelo"], [])
        self.assertTrue(entries[0]["avisos"])
        self.assertEqual(entries[0]["comparacion"]["omitidas"], 2)
        self.assertIn("no aplica", printed)

    def test_invented_snippet_keeps_the_judgment_and_reports_an_aviso(
        self,
    ) -> None:
        answer = model_answer(
            json.dumps(
                [
                    {
                        "tema": "comida",
                        "polaridad": "positivo",
                        "trozo": "trozo que no está en la reseña",
                    }
                ],
                ensure_ascii=False,
            )
        )
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            sheet = write_sheet(folder, [(13, True, MINE)])
            with fake_server([(200, answer)]) as (base_url, calls):
                result, _ = self.run_main(folder, base_url, sheet)

            entries = read_lines(result)

        self.assertEqual(entries[0]["comparacion"]["aciertos"], 1)
        self.assertNotEqual(entries[0]["del_modelo"], [])
        self.assertTrue(entries[0]["avisos"])

    def test_resume_skips_the_reviews_already_measured(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            sheet = write_sheet(folder, [(10, True, MINE), (11, True, MINE)])
            result = folder / "result_marked.jsonl"
            result.write_text(
                json.dumps(
                    {
                        "numero": 10,
                        "mias": MINE,
                        "del_modelo": [],
                        "comparacion": {
                            "aciertos": 0,
                            "inventadas": 0,
                            "omitidas": 2,
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            with fake_server([(200, model_answer(GOOD_REPEAT))]) as (
                base_url,
                calls,
            ):
                result, _ = self.run_main(folder, base_url, sheet)

            entries = read_lines(result)

        self.assertEqual(len(calls), 1)
        self.assertEqual(len(entries), 2)
        self.assertEqual(
            sorted(entry["numero"] for entry in entries), [10, 11]
        )

    def test_sheet_with_nothing_marked_stops_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            sheet = write_sheet(folder, [(10, False, [])])
            result = folder / "result_marked.jsonl"

            with fake_server([(200, model_answer(GOOD_REPEAT))]) as (
                base_url,
                calls,
            ):
                with redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as caught:
                        self.run_main(folder, base_url, sheet)
            printed = str(caught.exception)

        self.assertEqual(calls, [])
        self.assertFalse(result.exists())
        self.assertIn("No review in the labelled sheet is marked", printed)


if __name__ == "__main__":
    unittest.main()
