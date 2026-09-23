"""Stage 4 has to reach its LLM from inside a Ray job, and say so when it cannot.

A Ray job does not inherit the submitting shell's environment. On 2026-09-22
the job's driver therefore had no HEAD_IP and no P2P_GATEWAY_TOKEN, fell back
to 127.0.0.1 and an empty token, and every evolver call failed. The search
still "completed", with only its seed scored. These tests pin the three parts
of the fix: the driver reads the gateway's own env file, the probe names a dead
route before any build, and a seed-only search is not reported as a result.
"""

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from types import SimpleNamespace

import pytest

import constants as C
import dse

LOOP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _constants_in_clean_env(env_file, **extra):
    """What constants.py resolves in a process with none of the shell's
    variables, which is what a job's driver gets."""
    env = {"PATH": os.environ.get("PATH", ""), "HOME": "/nonexistent",
           "PYTHONPATH": LOOP_DIR, "P2P_GATEWAY_ENV_FILE": str(env_file), **extra}
    out = subprocess.run(
        [sys.executable, "-c",
         "import json, constants as C; print(json.dumps({'url': C.GATEWAY_URL, "
         "'token': C.GATEWAY_TOKEN, 'forwarded': C.RUNTIME_ENV['env_vars']}))"],
        env=env, capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def test_a_driver_with_no_env_reads_the_gateway_env_file(tmp_path):
    env_file = tmp_path / "gateway.env"
    env_file.write_text("# comment\nP2P_GATEWAY_HOST=10.9.8.7\n"
                        "P2P_GATEWAY_PORT=8911\nP2P_GATEWAY_TOKEN=s3cret\n")
    got = _constants_in_clean_env(env_file)
    assert got["url"] == "http://10.9.8.7:8911/v1"
    assert got["token"] == "s3cret"
    # The actor expands ${P2P_GATEWAY_TOKEN} from its own environment, so a
    # token that only the driver knows is a token the search never sends.
    assert got["forwarded"]["P2P_GATEWAY_TOKEN"] == "s3cret"
    assert got["forwarded"]["P2P_GATEWAY_URL"] == "http://10.9.8.7:8911/v1"


def test_the_environment_wins_over_the_file(tmp_path):
    env_file = tmp_path / "gateway.env"
    env_file.write_text("P2P_GATEWAY_HOST=10.9.8.7\nP2P_GATEWAY_TOKEN=from-file\n")
    got = _constants_in_clean_env(env_file, HEAD_IP="10.1.1.1",
                                  P2P_GATEWAY_TOKEN="from-env")
    assert got["url"] == "http://10.1.1.1:8900/v1"
    assert got["token"] == "from-env"


def test_no_file_and_no_env_is_not_loopback(tmp_path):
    """The gateway binds the head's VPC address, and the driver runs on the
    head, so the node's own address is the right last resort."""
    got = _constants_in_clean_env(tmp_path / "absent.env")
    assert got["url"] == f"http://{C._node_ip()}:8900/v1"
    assert got["token"] == ""
    assert "P2P_GATEWAY_TOKEN" not in got["forwarded"]


# ------------------------------------------------------------------ the probe


class _Gateway(BaseHTTPRequestHandler):
    status = 200
    seen: list = []

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).seen.append((self.path, self.headers["Authorization"], body["model"]))
        self.send_response(type(self).status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"choices": []}')

    def log_message(self, *args):
        pass


@pytest.fixture
def gateway():
    _Gateway.seen = []
    _Gateway.status = 200
    server = HTTPServer(("127.0.0.1", 0), _Gateway)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server
    server.shutdown()


def _config(tmp_path, *models):
    path = tmp_path / "search.yaml"
    path.write_text(
        "llm:\n  api_base: ${P2P_GATEWAY_URL}\n  api_key: ${P2P_GATEWAY_TOKEN}\n"
        "  models:\n" + "".join(f"    - name: {m}\n      weight: 1.0\n" for m in models))
    return str(path)


def test_probe_asks_every_model_with_the_forwarded_url_and_key(tmp_path, gateway, monkeypatch):
    url = f"http://127.0.0.1:{gateway.server_port}/v1"
    monkeypatch.setitem(C.RUNTIME_ENV["env_vars"], "P2P_GATEWAY_URL", url)
    monkeypatch.setitem(C.RUNTIME_ENV["env_vars"], "P2P_GATEWAY_TOKEN", "tok")
    report = dse.check_llm(_config(tmp_path, "google/a", "google/b"))
    assert report["errors"] == []
    assert report["models"] == {"google/a": "ok", "google/b": "ok"}
    assert _Gateway.seen == [("/v1/chat/completions", "Bearer tok", "google/a"),
                             ("/v1/chat/completions", "Bearer tok", "google/b")]


def test_probe_reports_a_refusal(tmp_path, gateway, monkeypatch):
    _Gateway.status = 401
    monkeypatch.setitem(C.RUNTIME_ENV["env_vars"], "P2P_GATEWAY_URL",
                        f"http://127.0.0.1:{gateway.server_port}/v1")
    monkeypatch.setitem(C.RUNTIME_ENV["env_vars"], "P2P_GATEWAY_TOKEN", "wrong")
    report = dse.check_llm(_config(tmp_path, "google/a"))
    assert len(report["errors"]) == 1 and "HTTP 401" in report["errors"][0]


def test_probe_reports_an_unset_placeholder_without_sending(tmp_path, monkeypatch):
    """skydiscover would send the literal text "${P2P_GATEWAY_TOKEN}" as the
    key, and the failure would read as an opaque auth error."""
    monkeypatch.delitem(C.RUNTIME_ENV["env_vars"], "P2P_GATEWAY_TOKEN", raising=False)
    monkeypatch.delenv("P2P_GATEWAY_TOKEN", raising=False)
    report = dse.check_llm(_config(tmp_path, "google/a"))
    assert report["errors"] == ["google/a: P2P_GATEWAY_TOKEN not set in the evolver's environment"]


def test_probe_reports_a_dead_address(tmp_path, monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), _Gateway)
    port = server.server_port
    server.server_close()  # nothing listens there now
    monkeypatch.setitem(C.RUNTIME_ENV["env_vars"], "P2P_GATEWAY_URL", f"http://127.0.0.1:{port}/v1")
    monkeypatch.setitem(C.RUNTIME_ENV["env_vars"], "P2P_GATEWAY_TOKEN", "tok")
    report = dse.check_llm(_config(tmp_path, "google/a"))
    assert len(report["errors"]) == 1 and "unreachable" in report["errors"][0]


def test_a_config_with_no_models_is_an_error(tmp_path):
    path = tmp_path / "empty.yaml"
    path.write_text("llm:\n  api_base: http://x/v1\n")
    assert dse.check_llm(str(path))["errors"]


# ------------------------------------------------------------ the outcome


def _result(status, count, error=None):
    return SimpleNamespace(terminal_status=status, iteration_count=count, error_message=error)


def test_a_search_that_scored_only_its_seed_is_not_a_result():
    status, error = dse.search_outcome(_result("completed", 1))
    assert status == "no_candidates" and status not in dse.DSE_OK
    assert "seed" in error


def test_a_search_with_proposals_keeps_its_status():
    assert dse.search_outcome(_result("completed", 4)) == ("completed", None)
    assert dse.search_outcome(_result("error", 0, "boom")) == ("error", "boom")
