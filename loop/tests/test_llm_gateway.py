"""Tests for the Vertex LLM gateway (loop/llm_gateway.py).

The gateway's whole reason to exist is that a Vertex bearer dies after ~60
minutes and no consumer refreshes it, so the tests that matter are the ones
about token lifetime: that a stale credential is refreshed before the next
call, that an upstream 401 forces exactly one refresh and retry, and that
concurrent requests do not race to refresh. The rest guard the traps --
the shared secret must never leak upstream, and the model name must arrive
in the `google/` form Vertex's openapi shim expects.

Upstream is a real stub HTTP server rather than a mocked transport, copying
the pattern from chia/models/tests/test_openai_compat.py: it exercises the
actual header/status/streaming path and spends no credits.
"""

import gzip
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from fastapi.testclient import TestClient

import llm_gateway

GATEWAY_SECRET = "gateway-secret-not-a-google-token"
GOOGLE_TOKEN = "ya29.fake-google-token"


class _StubHandler(BaseHTTPRequestHandler):
    """Records what Vertex would have seen, and replays a canned answer.

    The request model name doubles as the control channel, the same trick
    test_openai_compat.py uses: "status-401" makes the stub answer 401 once.
    """

    def log_message(self, *args):  # silence per-request logging
        pass

    def do_POST(self):
        length = int(self.headers.get("content-length", 0) or 0)
        body = json.loads(self.rfile.read(length) or b"{}")
        self.server.seen.append(
            {
                "path": self.path,
                "authorization": self.headers.get("authorization"),
                "quota_project": self.headers.get("x-goog-user-project"),
                "model": body.get("model"),
                "stream": bool(body.get("stream")),
            }
        )

        if body.get("model") == "google/status-401" and not self.server.retried:
            self.server.retried = True
            self._send(401, {"error": {"message": "UNAUTHENTICATED"}})
            return

        if body.get("stream"):
            # gzipped, like the real Vertex SSE stream. This is deliberate:
            # forwarding httpx's aiter_raw() here ships still-compressed bytes
            # to a client told it is reading text/event-stream, which showed up
            # as binary garbage against live Vertex.
            payload = b""
            for piece in ("one", "two"):
                chunk = json.dumps({"choices": [{"delta": {"content": piece}}]})
                payload += f"data: {chunk}\n\n".encode()
            payload += b"data: [DONE]\n\n"
            payload = gzip.compress(payload)
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.send_header("content-encoding", "gzip")
            self.send_header("content-length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            self.wfile.flush()
            return

        self._send(
            200,
            {
                "id": "chatcmpl-stub",
                "object": "chat.completion",
                "model": body.get("model"),
                "choices": [
                    {"index": 0, "message": {"role": "assistant", "content": "OK"},
                     "finish_reason": "stop"}
                ],
                "usage": {
                    "prompt_tokens": 3,
                    "completion_tokens": 11,
                    "total_tokens": 14,
                    "completion_tokens_details": {"reasoning_tokens": 55},
                },
            },
        )

    def _send(self, code, payload):
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class _FakeCreds:
    """Stands in for a google.auth credential: valid until told otherwise."""

    def __init__(self, valid=True):
        self.valid = valid
        self.token = GOOGLE_TOKEN
        self.expiry = None
        self.refresh_calls = 0

    def refresh(self, _request):
        self.refresh_calls += 1
        self.token = f"{GOOGLE_TOKEN}-{self.refresh_calls}"
        self.valid = True


@pytest.fixture
def upstream():
    server = HTTPServer(("127.0.0.1", 0), _StubHandler)
    server.seen = []
    server.retried = False
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=5)


@pytest.fixture
def creds(monkeypatch):
    fake = _FakeCreds()
    monkeypatch.setattr(llm_gateway, "_creds", fake)
    return fake


@pytest.fixture
def client(monkeypatch, upstream, creds, tmp_path):
    host, port = upstream.server_address
    monkeypatch.setattr(llm_gateway, "_VERTEX_HOST", f"http://{host}:{port}")
    monkeypatch.setattr(llm_gateway, "PROJECT", "test-project")
    monkeypatch.setattr(llm_gateway, "TOKEN", GATEWAY_SECRET)
    monkeypatch.setattr(llm_gateway, "MODEL_LOCATIONS", {})
    monkeypatch.setattr(llm_gateway, "DEFAULT_LOCATION", "global")
    monkeypatch.setattr(llm_gateway, "ACCOUNTING_PATH", tmp_path / "gateway.jsonl")
    with TestClient(llm_gateway.app) as tc:
        yield tc


def _post(client, model="google/gemini-3.5-flash", secret=GATEWAY_SECRET, **extra):
    body = {"model": model, "messages": [{"role": "user", "content": "hi"}], **extra}
    headers = {"Authorization": f"Bearer {secret}"} if secret else {}
    return client.post("/v1/chat/completions", json=body, headers=headers)


# ------------------------------------------------------------ caller auth
def test_a_request_without_the_shared_secret_is_rejected(client, upstream):
    assert _post(client, secret=None).status_code == 401
    assert upstream.seen == [], "an unauthenticated call must not reach Vertex"


def test_a_request_with_the_wrong_shared_secret_is_rejected(client, upstream):
    assert _post(client, secret="wrong").status_code == 401
    assert upstream.seen == []


def test_a_request_with_the_right_shared_secret_is_forwarded(client, upstream):
    assert _post(client).status_code == 200
    assert len(upstream.seen) == 1


# --------------------------------------------------------- credential swap
def test_the_caller_secret_is_replaced_by_a_google_bearer_upstream(client, upstream):
    _post(client)
    sent = upstream.seen[0]["authorization"]
    assert sent == f"Bearer {GOOGLE_TOKEN}"
    assert GATEWAY_SECRET not in sent, "the gateway secret must never leak to Google"


def test_the_quota_project_header_is_sent(client, upstream):
    _post(client)
    assert upstream.seen[0]["quota_project"] == "test-project"


# ------------------------------------------------------- the actual point
def test_an_expired_credential_is_refreshed_before_the_next_call(client, upstream, creds):
    """The regression test for the bug this whole gateway exists to fix."""
    _post(client)
    assert creds.refresh_calls == 0, "a valid token should not be refreshed"

    creds.valid = False  # what happens ~60 minutes into a run
    assert _post(client).status_code == 200

    assert creds.refresh_calls == 1
    assert upstream.seen[-1]["authorization"] == f"Bearer {GOOGLE_TOKEN}-1", (
        "the retried call must carry the new token, not the stale one"
    )


def test_an_upstream_401_forces_one_refresh_and_one_retry(client, upstream, creds):
    resp = _post(client, model="google/status-401")
    assert resp.status_code == 200, "the retry should succeed"
    assert creds.refresh_calls == 1
    assert len(upstream.seen) == 2
    assert upstream.seen[0]["authorization"] != upstream.seen[1]["authorization"]


def test_concurrent_requests_refresh_the_credential_only_once(creds):
    """8 concurrent requests are possible (max_parallel_iterations: 8), and a
    google.auth credential is not thread-safe."""
    creds.valid = False
    tokens, errors = [], []

    def call():
        try:
            tokens.append(llm_gateway.bearer())
        except Exception as exc:  # pragma: no cover - only on a lock bug
            errors.append(exc)

    threads = [threading.Thread(target=call) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert creds.refresh_calls == 1, "the lock should collapse the refresh stampede"
    assert set(tokens) == {f"{GOOGLE_TOKEN}-1"}


# --------------------------------------------------------- naming/routing
def test_a_bare_gemini_name_is_normalised_to_the_google_prefix(client, upstream):
    _post(client, model="gemini-3.5-flash")
    assert upstream.seen[0]["model"] == "google/gemini-3.5-flash"


def test_an_already_prefixed_name_is_left_alone(client, upstream):
    _post(client, model="google/gemini-3.5-flash")
    assert upstream.seen[0]["model"] == "google/gemini-3.5-flash"


def test_the_model_location_map_selects_the_upstream_region(client, upstream, monkeypatch):
    monkeypatch.setattr(
        llm_gateway, "MODEL_LOCATIONS", {"google/gemini-3.5-flash": "us-central1"}
    )
    _post(client)
    assert "/locations/us-central1/" in upstream.seen[0]["path"]


def test_an_unmapped_model_falls_back_to_the_default_location(client, upstream):
    _post(client)
    assert "/locations/global/" in upstream.seen[0]["path"]


# ---------------------------------------------------------------- shapes
def test_streaming_responses_pass_through_as_decoded_sse(client, upstream):
    """The upstream stub gzips, as Vertex does; the caller must get plain SSE."""
    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={"model": "google/gemini-3.5-flash", "messages": [], "stream": True},
        headers={"Authorization": f"Bearer {GATEWAY_SECRET}"},
    ) as resp:
        assert resp.status_code == 200
        text = "".join(resp.iter_text())
    assert "data: " in text and "[DONE]" in text
    assert '"content": "one"' in text and '"content": "two"' in text
    assert upstream.seen[0]["stream"] is True


def test_usage_counts_are_written_to_the_accounting_log(client):
    _post(client)
    rows = [
        json.loads(line)
        for line in llm_gateway.ACCOUNTING_PATH.read_text().splitlines()
        if line
    ]
    assert len(rows) == 1
    assert rows[0]["input_tokens"] == 3
    assert rows[0]["output_tokens"] == 11
    assert rows[0]["reasoning_tokens"] == 55
    assert rows[0]["model"] == "google/gemini-3.5-flash"
    assert rows[0]["status"] == 200


def test_the_bare_chat_completions_alias_also_works(client, upstream):
    resp = client.post(
        "/chat/completions",
        json={"model": "google/gemini-3.5-flash", "messages": []},
        headers={"Authorization": f"Bearer {GATEWAY_SECRET}"},
    )
    assert resp.status_code == 200
    assert len(upstream.seen) == 1


def test_healthz_reports_liveness_without_leaking_the_token(client):
    payload = client.get("/healthz").json()
    assert payload["ok"] is True
    assert payload["auth_required"] is True
    assert GOOGLE_TOKEN not in json.dumps(payload)


# ------------------------------------------------------- upstream failures
def test_an_unreachable_upstream_becomes_an_openai_shaped_502(client, monkeypatch):
    """A raw exception would escape as an HTML 500 traceback, which a consumer
    parsing JSON misreports as a schema error."""
    # Port 1 on localhost refuses connections immediately.
    monkeypatch.setattr(llm_gateway, "_VERTEX_HOST", "http://127.0.0.1:1")
    resp = _post(client)
    assert resp.status_code == 502
    assert resp.json()["error"]["type"] == "upstream_unreachable"


def test_a_failed_request_is_still_accounted(client, monkeypatch):
    monkeypatch.setattr(llm_gateway, "_VERTEX_HOST", "http://127.0.0.1:1")
    _post(client)
    rows = [
        json.loads(line)
        for line in llm_gateway.ACCOUNTING_PATH.read_text().splitlines()
        if line
    ]
    assert rows[-1]["status"] == 502
    assert "error" in rows[-1]


# ------------------------------------------------------------ startup guard
def test_binding_beyond_loopback_without_a_secret_refuses_to_start(monkeypatch):
    """Anything that can reach the port can spend the project's credits."""
    monkeypatch.setattr(llm_gateway, "PROJECT", "test-project")
    monkeypatch.setattr(llm_gateway, "HOST", "10.128.0.2")
    monkeypatch.setattr(llm_gateway, "TOKEN", "")
    with pytest.raises(SystemExit, match="P2P_GATEWAY_TOKEN"):
        llm_gateway.main()


def test_a_missing_project_refuses_to_start(monkeypatch):
    monkeypatch.setattr(llm_gateway, "PROJECT", "")
    with pytest.raises(SystemExit, match="GCP_PROJECT"):
        llm_gateway.main()
