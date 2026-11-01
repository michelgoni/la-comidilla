"""Tests for the single-review extraction program."""

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


def model_answer(content: str) -> str:
    """Wrap one answer in the shape an OpenAI-compatible server returns."""
    return json.dumps({"choices": [{"message": {"content": content}}]})


@contextmanager
def fake_server(body: str, status: int = 200, headers_seen: list = None):
    """Run a local HTTP server that always returns the same body."""

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(length)
            if headers_seen is not None:
                headers_seen.append(
                    {
                        "User-Agent": self.headers.get("User-Agent", ""),
                        "x-opencode-session": self.headers.get(
                            "x-opencode-session", ""
                        ),
                    }
                )
            data = body.encode("utf-8")
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
        yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class ConfigTests(unittest.TestCase):
    """Configuration comes from the environment or from the secrets file."""

    def test_environment_wins(self) -> None:
        env = {
            "COMIDILLA_BASE_URL": "http://example.test/v1",
            "COMIDILLA_MODEL": "modelo-de-prueba",
            "COMIDILLA_API_KEY": "clave",
        }
        with tempfile.TemporaryDirectory() as folder:
            secrets = Path(folder) / "missing.env"
            with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(
                extract, "SECRETS_PATH", secrets
            ):
                config = extract.load_config()
        self.assertEqual(config["base_url"], "http://example.test/v1")
        self.assertEqual(config["model"], "modelo-de-prueba")
        self.assertEqual(config["api_key"], "clave")

    def test_reads_secrets_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            secrets = Path(folder) / "comidilla.env"
            secrets.write_text(
                "COMIDILLA_BASE_URL=http://secreto.test/v1\n"
                "COMIDILLA_MODEL=modelo-secreto\n"
                "COMIDILLA_API_KEY=clave-secreta\n",
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
                extract, "SECRETS_PATH", secrets
            ):
                config = extract.load_config()
        self.assertEqual(config["base_url"], "http://secreto.test/v1")
        self.assertEqual(config["model"], "modelo-secreto")
        self.assertEqual(config["api_key"], "clave-secreta")

    def test_missing_configuration_stops(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            secrets = Path(folder) / "missing.env"
            with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
                extract, "SECRETS_PATH", secrets
            ):
                with self.assertRaises(SystemExit) as caught:
                    extract.load_config()
        self.assertIn("COMIDILLA_BASE_URL", str(caught.exception))


class CorpusTests(unittest.TestCase):
    """The corpus is read and one review is picked by number."""

    def test_load_and_pick(self) -> None:
        reviews = [["Local", 4, "Texto de la reseña"]]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "corpus.json"
            path.write_text(json.dumps(reviews, ensure_ascii=False), encoding="utf-8")
            loaded = extract.load_corpus(path)
        self.assertEqual(loaded, reviews)
        self.assertEqual(extract.pick_review(loaded, 0), ("Local", 4, "Texto de la reseña"))

    def test_bad_corpus_stops(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "corpus.json"
            path.write_text('{"no": "es una lista"}', encoding="utf-8")
            with self.assertRaises(SystemExit):
                extract.load_corpus(path)

    def test_index_out_of_range_stops(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            extract.pick_review([["Local", 4, "Texto"]], 900)
        self.assertIn("There are 1 reviews", str(caught.exception))
        self.assertIn("0 to 0", str(caught.exception))


class PromptTests(unittest.TestCase):
    """The prompt file must exist and carry text."""

    def test_reads_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prompt.txt"
            path.write_text("Primera línea\nSegunda línea", encoding="utf-8")
            self.assertEqual(
                extract.load_prompt(path), "Primera línea\nSegunda línea"
            )

    def test_missing_prompt_stops(self) -> None:
        with self.assertRaises(SystemExit):
            extract.load_prompt(Path("/tmp/no-existe-comidilla.txt"))

    def test_empty_prompt_stops(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prompt.txt"
            path.write_text("   \n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                extract.load_prompt(path)


class PayloadTests(unittest.TestCase):
    """The request body has the fixed shape from the specification."""

    def test_payload_shape(self) -> None:
        payload = extract.build_payload("modelo", "Prompt", "Texto")
        self.assertEqual(payload["model"], "modelo")
        self.assertEqual(payload["temperature"], 0)
        self.assertEqual(payload["messages"][0], {"role": "system", "content": "Prompt"})
        self.assertEqual(
            payload["messages"][1],
            {"role": "user", "content": 'Reseña:\n"""\nTexto\n"""'},
        )


class AnswerTests(unittest.TestCase):
    """The raw answer is cleaned and its shape is checked."""

    def test_clean_plain_brackets(self) -> None:
        self.assertEqual(extract.clean_answer('  [{"a": 1}]  '), '[{"a": 1}]')

    def test_clean_code_fence(self) -> None:
        raw = '```json\n[{"tema": "comida"}]\n```'
        self.assertEqual(extract.clean_answer(raw), '[{"tema": "comida"}]')

    def test_clean_surrounding_text(self) -> None:
        raw = 'Aquí está la lista:\n[{"a": 1}]\nGracias.'
        self.assertEqual(extract.clean_answer(raw), '[{"a": 1}]')

    def test_good_shape_inside_code_fence(self) -> None:
        raw = (
            "```json\n"
            '[{"tema": "comida", "polaridad": "positivo", "trozo": "La comida"}]\n'
            "```"
        )
        self.assertEqual(extract.check_shape(raw, "La comida estaba buenísima."), [])

    def test_good_shape(self) -> None:
        raw = json.dumps(
            [
                {
                    "tema": "comida",
                    "polaridad": "positivo",
                    "trozo": "La comida estaba  buenísima",
                }
            ],
            ensure_ascii=False,
        )
        self.assertEqual(
            extract.check_shape(raw, "La comida estaba buenísima y el sitio era bonito."),
            [],
        )

    def test_invented_snippet(self) -> None:
        raw = json.dumps(
            [{"tema": "comida", "polaridad": "positivo", "trozo": "inventado"}],
            ensure_ascii=False,
        )
        problems = extract.check_shape(raw, "La comida estaba buenísima.")
        self.assertTrue(any("no aparece en la reseña" in problem for problem in problems))

    def test_invalid_theme(self) -> None:
        raw = json.dumps(
            [{"tema": "limpieza", "polaridad": "positivo", "trozo": "La comida"}],
            ensure_ascii=False,
        )
        problems = extract.check_shape(raw, "La comida estaba buenísima.")
        self.assertTrue(any("tema no válido" in problem for problem in problems))

    def test_not_a_list(self) -> None:
        problems = extract.check_shape('{"tema": "comida"}', "La comida estaba buena.")
        self.assertEqual(problems, ["La respuesta no es una lista."])

    def test_missing_field(self) -> None:
        raw = json.dumps([{"tema": "comida", "polaridad": "positivo"}])
        problems = extract.check_shape(raw, "La comida estaba buenísima.")
        self.assertTrue(any("falta el campo trozo" in problem for problem in problems))

    def test_two_sentences_with_ellipsis(self) -> None:
        raw = json.dumps(
            [
                {
                    "tema": "servicio",
                    "polaridad": "negativo",
                    "trozo": "Tardaron mucho ... no volveré",
                }
            ],
            ensure_ascii=False,
        )
        self.assertEqual(
            extract.check_shape(raw, "Tardaron mucho en traer la cuenta. No volveré."),
            ["El trozo del juicio 1 no aparece en la reseña: 'no volveré'."],
        )

    def test_two_sentences_with_ellipsis_matching_case(self) -> None:
        raw = json.dumps(
            [
                {
                    "tema": "servicio",
                    "polaridad": "negativo",
                    "trozo": "Tardaron mucho ... No volveré",
                }
            ],
            ensure_ascii=False,
        )
        self.assertEqual(
            extract.check_shape(raw, "Tardaron mucho en traer la cuenta. No volveré."),
            [],
        )


class ModelCallTests(unittest.TestCase):
    """The model call uses the fake server and reports failures clearly."""

    def test_successful_call(self) -> None:
        with fake_server(model_answer('[{"tema": "comida"}]')) as base_url:
            answer, milliseconds = extract.call_model(
                base_url, "", extract.build_payload("modelo", "Prompt", "Texto")
            )
        self.assertEqual(answer, '[{"tema": "comida"}]')
        self.assertGreaterEqual(milliseconds, 0)

    def test_call_sends_browser_and_session_headers(self) -> None:
        headers_seen = []
        with fake_server(
            model_answer("[]"), headers_seen=headers_seen
        ) as base_url:
            extract.call_model(
                base_url, "", extract.build_payload("modelo", "Prompt", "Texto")
            )

        self.assertEqual(len(headers_seen), 1)
        self.assertTrue(headers_seen[0]["User-Agent"].startswith("Mozilla/5.0"))
        self.assertEqual(headers_seen[0]["x-opencode-session"], "comidilla")

    def test_http_error_shows_code_and_body(self) -> None:
        with fake_server('{"error": "roto"}', status=500) as base_url:
            with self.assertRaises(SystemExit) as caught:
                extract.call_model(
                    base_url, "", extract.build_payload("modelo", "Prompt", "Texto")
                )
        message = str(caught.exception)
        self.assertIn("500", message)
        self.assertIn("roto", message)

    def test_missing_answer_text(self) -> None:
        with fake_server(json.dumps({"choices": []})) as base_url:
            with self.assertRaises(SystemExit) as caught:
                extract.call_model(
                    base_url, "", extract.build_payload("modelo", "Prompt", "Texto")
                )
        self.assertIn("does not contain the expected text", str(caught.exception))


class RegistryTests(unittest.TestCase):
    """Every call appends one line and never loses the previous ones."""

    def test_append_keeps_previous_entries(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            registry = Path(folder) / "registry.json"
            with mock.patch.object(extract, "REGISTRY_PATH", registry):
                extract.append_registry({"numero": 0})
                extract.append_registry({"numero": 1})
            lines = registry.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["numero"], 0)
        self.assertEqual(json.loads(lines[1])["numero"], 1)

    def test_append_reads_old_list_format(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            registry = Path(folder) / "registry.json"
            registry.write_text('[{"numero": 0}]', encoding="utf-8")
            with mock.patch.object(extract, "REGISTRY_PATH", registry):
                extract.append_registry({"numero": 1})
            lines = registry.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["numero"], 0)


class MainTests(unittest.TestCase):
    """The whole program works against the fake server."""

    def test_main_shows_and_logs_the_call(self) -> None:
        judgment = json.dumps(
            [
                {
                    "tema": "comida",
                    "polaridad": "positivo",
                    "trozo": "La comida estaba buenísima",
                }
            ],
            ensure_ascii=False,
        )
        review_text = "La comida estaba buenísima y el sitio era bonito."
        with tempfile.TemporaryDirectory() as folder:
            folder_path = Path(folder)
            corpus = folder_path / "corpus.json"
            corpus.write_text(
                json.dumps([["Local de prueba", 4, review_text]], ensure_ascii=False),
                encoding="utf-8",
            )
            prompt = folder_path / "prompt.txt"
            prompt.write_text("Prompt de prueba", encoding="utf-8")
            registry = folder_path / "registry.json"
            env = {
                "COMIDILLA_BASE_URL": "",
                "COMIDILLA_MODEL": "modelo-de-prueba",
                "COMIDILLA_API_KEY": "",
                "COMIDILLA_PROMPT": str(prompt),
            }
            with fake_server(model_answer(judgment)) as base_url:
                env["COMIDILLA_BASE_URL"] = base_url
                with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(
                    extract, "CORPUS_PATH", corpus
                ), mock.patch.object(
                    extract, "REGISTRY_PATH", registry
                ), mock.patch.object(
                    extract, "SECRETS_PATH", folder_path / "missing.env"
                ), mock.patch.object(
                    sys, "argv", ["extract.py", "--index", "0"]
                ), redirect_stdout(
                    io.StringIO()
                ):
                    extract.main()

            lines = registry.read_text(encoding="utf-8").splitlines()

        self.assertEqual(len(lines), 1)
        entry = json.loads(lines[0])
        self.assertEqual(entry["numero"], 0)
        self.assertEqual(entry["local"], "Local de prueba")
        self.assertEqual(entry["estrellas"], 4)
        self.assertEqual(entry["respuesta"], judgment)
        self.assertEqual(entry["error"], "")
        self.assertGreaterEqual(entry["milisegundos"], 0)

    def test_main_without_configuration_stops_before_calling(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            folder_path = Path(folder)
            registry = folder_path / "registry.json"
            with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
                extract, "REGISTRY_PATH", registry
            ), mock.patch.object(
                extract, "SECRETS_PATH", folder_path / "missing.env"
            ), mock.patch.object(
                sys, "argv", ["extract.py"]
            ), redirect_stdout(
                io.StringIO()
            ):
                with self.assertRaises(SystemExit):
                    extract.main()
            self.assertFalse(registry.exists())


if __name__ == "__main__":
    unittest.main()
