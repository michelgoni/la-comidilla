"""Tests for the program that walks the whole review corpus."""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import threading
import unittest
from contextlib import contextmanager, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import extract
import correr_corpus

REVIEW_TEXT = "La comida estaba buenísima."
GOOD_ANSWER = json.dumps(
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


def write_corpus(folder: Path, count: int) -> Path:
    """Write a small corpus whose reviews share one easy-to-check text."""
    reviews = [
        [f"Local {number}", 4, REVIEW_TEXT]
        for number in range(count)
    ]
    path = folder / "corpus.json"
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


class CorpusRunnerTests(unittest.TestCase):
    """The runner walks the corpus, resumes and survives failures."""

    def run_main(
        self,
        folder: Path,
        base_url: str,
        corpus: Path,
        extra_arguments: list = None,
        add_config: bool = True,
    ) -> tuple:
        """Run the program with temporary files and capture what it prints."""
        result = folder / "result_corpus.jsonl"
        errors = folder / "errors_corpus.jsonl"
        prompt = folder / "prompt.txt"
        prompt.write_text("Prompt de prueba", encoding="utf-8")

        env = {
            "COMIDILLA_BASE_URL": base_url,
            "COMIDILLA_MODEL": "modelo-de-prueba",
            "COMIDILLA_API_KEY": "",
            "COMIDILLA_PROMPT": str(prompt),
        }
        if not add_config:
            env = {}

        arguments = [
            "correr_corpus.py",
            "--corpus",
            str(corpus),
            *(extra_arguments or []),
        ]
        sleeps = []
        output = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(
                    extract, "SECRETS_PATH", folder / "missing.env"
                ), mock.patch.object(
                    correr_corpus, "RESULT_PATH", result
                ), mock.patch.object(
                    correr_corpus, "ERROR_PATH", errors
                ), mock.patch.object(
                    correr_corpus.time, "sleep", sleeps.append
                ), mock.patch.object(
                    sys, "argv", arguments
                ), redirect_stdout(
                    output
                ):
            correr_corpus.main()

        return result, errors, output.getvalue(), sleeps

    def test_first_pass_writes_one_line_per_review(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            corpus = write_corpus(folder, 5)
            with fake_server([(200, model_answer(GOOD_ANSWER))]) as (
                base_url,
                calls,
            ):
                result, _, _, _ = self.run_main(folder, base_url, corpus)

            entries = read_lines(result)

        self.assertEqual(len(calls), 5)
        self.assertEqual(len(entries), 5)
        self.assertEqual(
            [entry["numero"] for entry in entries], [0, 1, 2, 3, 4]
        )
        self.assertTrue(all(entry["forma_correcta"] for entry in entries))
        self.assertTrue(all(entry["error"] == "" for entry in entries))

    def test_resume_skips_the_numbers_already_written(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            corpus = write_corpus(folder, 5)
            result = folder / "result_corpus.jsonl"
            result.write_text(
                '{"numero": 0}\n{"numero": 1}\n', encoding="utf-8"
            )
            with fake_server([(200, model_answer(GOOD_ANSWER))]) as (
                base_url,
                calls,
            ):
                result, _, _, _ = self.run_main(folder, base_url, corpus)

            entries = read_lines(result)

        self.assertEqual(len(calls), 3)
        self.assertEqual(len(entries), 5)
        self.assertEqual(
            [entry["numero"] for entry in entries], [0, 1, 2, 3, 4]
        )

    def test_retry_succeeds_after_two_failures(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            corpus = write_corpus(folder, 1)
            responses = [
                (500, '{"error": "roto"}'),
                (500, '{"error": "roto"}'),
                (200, model_answer(GOOD_ANSWER)),
            ]
            with fake_server(responses) as (base_url, calls):
                result, errors, _, sleeps = self.run_main(
                    folder,
                    base_url,
                    corpus,
                    ["--reintentos", "2"],
                )

            entries = read_lines(result)

        self.assertEqual(len(calls), 3)
        self.assertEqual(sleeps, [2, 4])
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]["forma_correcta"])
        self.assertEqual(entries[0]["error"], "")
        self.assertEqual(read_lines(errors), [])

    def test_exhausted_retries_are_saved_and_the_walk_goes_on(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            corpus = write_corpus(folder, 2)
            with fake_server([(500, '{"error": "roto"}')]) as (
                base_url,
                calls,
            ):
                result, errors, _, sleeps = self.run_main(
                    folder,
                    base_url,
                    corpus,
                    ["--reintentos", "1"],
                )

            entries = read_lines(result)
            error_entries = read_lines(errors)

        self.assertEqual(len(calls), 4)
        self.assertEqual(sleeps, [2, 2])
        self.assertEqual(len(entries), 2)
        self.assertEqual([entry["numero"] for entry in entries], [0, 1])
        self.assertTrue(all(entry["error"] for entry in entries))
        self.assertEqual(len(error_entries), 2)
        self.assertEqual(error_entries, entries)

    def test_range_end_is_not_included(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            corpus = write_corpus(folder, 5)
            with fake_server([(200, model_answer(GOOD_ANSWER))]) as (
                base_url,
                calls,
            ):
                result, _, _, _ = self.run_main(
                    folder,
                    base_url,
                    corpus,
                    ["--desde", "2", "--hasta", "4"],
                )

            entries = read_lines(result)

        self.assertEqual(len(calls), 2)
        self.assertEqual([entry["numero"] for entry in entries], [2, 3])

    def test_wrong_shape_keeps_the_raw_answer_and_no_error_row(self) -> None:
        bad_answer = json.dumps(
            [
                {
                    "tema": "comida",
                    "polaridad": "positivo",
                    "trozo": "inventado",
                }
            ],
            ensure_ascii=False,
        )
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            corpus = write_corpus(folder, 1)
            with fake_server([(200, model_answer(bad_answer))]) as (
                base_url,
                _,
            ):
                result, errors, _, _ = self.run_main(
                    folder, base_url, corpus
                )

            entries = read_lines(result)

        self.assertEqual(len(entries), 1)
        self.assertFalse(entries[0]["forma_correcta"])
        self.assertEqual(entries[0]["del_modelo"], [])
        self.assertTrue(entries[0]["avisos"])
        self.assertEqual(entries[0]["respuesta_cruda"], bad_answer)
        self.assertEqual(entries[0]["error"], "")
        self.assertEqual(read_lines(errors), [])

    def test_missing_configuration_stops_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            corpus = write_corpus(folder, 1)
            result = folder / "result_corpus.jsonl"
            errors = folder / "errors_corpus.jsonl"

            with mock.patch.dict(os.environ, {}, clear=True), \
                    mock.patch.object(
                        extract, "SECRETS_PATH", folder / "missing.env"
                    ), mock.patch.object(
                        correr_corpus, "RESULT_PATH", result
                    ), mock.patch.object(
                        correr_corpus, "ERROR_PATH", errors
                    ), mock.patch.object(
                        sys, "argv",
                        [
                            "correr_corpus.py",
                            "--corpus",
                            str(corpus),
                        ],
                    ), redirect_stdout(
                        io.StringIO()
                    ):
                with self.assertRaises(SystemExit):
                    correr_corpus.main()

            self.assertFalse(result.exists())
            self.assertFalse(errors.exists())


if __name__ == "__main__":
    unittest.main()
