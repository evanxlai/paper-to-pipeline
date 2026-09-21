"""Project-wide OpenAI-compatible gateway in front of Vertex AI.

Why this exists (all re-measured 2026-09-20 against
chia-hackathon-paper2pipeline, see docs/llm-gateway.md):

  * Vertex is the only funded route to Gemini. The public endpoint
    (generativelanguage.googleapis.com) draws on a separate AI Studio prepay
    pool which is empty and answers 402; Vertex answers 200 with
    traffic_type: ON_DEMAND, i.e. it genuinely bills the GCP project.
  * Vertex authenticates with an ADC bearer that lives ~1h (measured
    expires_in=3593) and validates it on *every* request -- a stale token is
    a hard 401, not a degraded response.
  * No consumer refreshes it. skydiscover freezes the token into
    openai.OpenAI(api_key=...) at construction (skydiscover/llm/openai.py:86)
    and has no token_provider/refresh/google.auth anywhere. Its one hook,
    LLMModelConfig.init_client, is Optional[Callable] so it cannot come from
    YAML, and no code of ours runs inside the EvolverNode actor before
    skydiscover builds its LLM pool.

So the refresh has to live outside the consumer. This gateway owns it: it
speaks the OpenAI chat/completions dialect, checks a shared secret, swaps in
a freshly-refreshed Google bearer, and forwards to Vertex's
OpenAI-compatibility endpoint. A 37-hour search then just works.

Run it:  python loop/llm_gateway.py
(loop/ is not a package -- modules import each other flat, with loop/ on
PYTHONPATH, the same way adopt_a_paper_loop.py does. Hence no -m.)

TRAP, do not "simplify" this away: a consumer config pointed here must name
the model "google/<model>", never "gemini-<model>". This gateway normalises
bare names for its own callers, but that CANNOT help skydiscover -- its
LLMConfig.__post_init__ matches the "gemini-" prefix and force-overwrites
api_base with the public endpoint inside its own process, at config-parse
time, before any HTTP request exists (skydiscover/config.py:197-208). A bare
name never reaches this process at all.
"""

from __future__ import annotations

import hmac
import json
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional

import google.auth
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from google.auth.transport.requests import Request as GoogleAuthRequest

log = logging.getLogger("p2p.llm_gateway")

# ---------------------------------------------------------------- config
# Ports 8000-8010 are SSH-tunnel reserved and 8000-8099 are ChiaTool's probe
# range (chia/models/vllm.py:10-16), so stay well above them.
HOST = os.environ.get("P2P_GATEWAY_HOST", "127.0.0.1")
PORT = int(os.environ.get("P2P_GATEWAY_PORT", "8900"))
TOKEN = os.environ.get("P2P_GATEWAY_TOKEN", "")
PROJECT = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT", "")

# Matches C.LLM_TIMEOUT_SECONDS: a single agent call is allowed to run 2h,
# i.e. longer than a token lives. httpx's 5s default would truncate these.
TIMEOUT_S = float(os.environ.get("P2P_GATEWAY_TIMEOUT", "7200"))

DEFAULT_LOCATION = os.environ.get("P2P_GATEWAY_LOCATION", "global")
# Availability is per-project, per-region AND changes over time: the handover
# doc recorded gemini-3.8-flash as global-only, but on re-probe it now serves
# on us-central1 too. Everything in use serves on "global", so this map is
# insurance, not a requirement. Override with a {"model": "location"} JSON.
MODEL_LOCATIONS: Dict[str, str] = json.loads(
    os.environ.get("P2P_GATEWAY_MODEL_LOCATIONS", "{}")
)

ACCOUNTING_PATH = Path(
    os.environ.get(
        "P2P_GATEWAY_ACCOUNTING",
        str(Path(__file__).resolve().parent.parent / "out" / "llm_gateway.jsonl"),
    )
)

_VERTEX_HOST = "https://aiplatform.googleapis.com"
_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


def _is_loopback(host: str) -> bool:
    return host in ("127.0.0.1", "localhost", "::1")


# ------------------------------------------------------------- auth core
# Same approach as chia/models/vertex.py:681 _vertex_adc_token_provider, with
# one deliberate difference: that helper calls creds.refresh() unconditionally
# on every invocation, which is fine when it runs once per client build but
# would add a token round-trip to each of the 8 concurrent requests the DSE
# config can have in flight. Refresh only when the cached token is invalid.
_creds = None
_creds_lock = threading.Lock()


def _load_credentials():
    """Caller must hold _creds_lock (or be startup, before any request)."""
    global _creds
    if _creds is None:
        _creds, discovered = google.auth.default(scopes=_SCOPES)
        log.info("ADC loaded (project discovered: %s)", discovered)
    return _creds


def bearer(force: bool = False) -> str:
    """Return a valid Google access token, refreshing in place when stale.

    Everything is inside the lock, load included: google.auth credential
    objects are not thread-safe, and the DSE config allows 8 concurrent
    requests, which would otherwise race to load and refresh the same
    credential.

    Synchronous on purpose. The refresh is a ~50ms network round-trip that
    happens once an hour, and doing it inline stalls the event loop for that
    long rather than adding an async credential path for no real benefit.
    """
    with _creds_lock:
        creds = _load_credentials()
        if force or not creds.valid:
            creds.refresh(GoogleAuthRequest())
            log.info("refreshed Vertex bearer, expires %s", creds.expiry)
        return creds.token


def token_expiry() -> Optional[str]:
    with _creds_lock:
        creds = _load_credentials()
        return str(creds.expiry) if creds.expiry else None


# ---------------------------------------------------------------- helpers
def _caller_authorised(request: Request) -> bool:
    """Constant-time check of the caller's api_key against the shared secret.

    The OpenAI SDK sends its api_key as `Authorization: Bearer <key>`, so the
    consumer's YAML `api_key` field is what lands here.
    """
    if not TOKEN:
        # Only reachable on a loopback bind; main() refuses to start otherwise.
        return True
    header = request.headers.get("authorization", "")
    prefix = "Bearer "
    presented = header[len(prefix):] if header.startswith(prefix) else header
    return hmac.compare_digest(presented, TOKEN)


def normalise_model(name: str) -> str:
    """Accept `gemini-x` as well as `google/gemini-x`.

    Vertex's openapi shim wants the `google/` form. This helps direct callers
    (curl, chia backends); it does NOT rescue a skydiscover config -- see the
    module docstring.
    """
    if name.startswith("gemini-"):
        return "google/" + name
    return name


def location_for(model: str) -> str:
    return MODEL_LOCATIONS.get(model, DEFAULT_LOCATION)


def upstream_url(location: str) -> str:
    return (
        f"{_VERTEX_HOST}/v1/projects/{PROJECT}/locations/{location}"
        f"/endpoints/openapi/chat/completions"
    )


def _upstream_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        # Passing only a bearer drops google-auth's quota-project header and
        # Vertex can answer 403 "requires a quota project" (the lesson baked
        # into chia/models/vertex.py's VertexGenericLLM). Our probes worked
        # without it; send it anyway, it is free.
        "x-goog-user-project": PROJECT,
    }


def _record(event: Dict[str, Any]) -> None:
    """Append one JSONL row per request.

    Deliberately not chia.trace.profiler: that collector is a non-detached,
    per-job Ray actor that dies with the driver, and viz-profile only renders
    counts fed through ChiaProfiler.add_info(), which is thread-local to an
    in-flight ChiaFunction and unreachable from this process. Same event shape
    so the logs can be merged later.
    """
    try:
        ACCOUNTING_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(ACCOUNTING_PATH, "a") as fh:
            fh.write(json.dumps(event, default=str) + "\n")
    except OSError as exc:  # accounting must never break a paid request
        log.warning("could not write accounting row: %s", exc)


def _usage_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten OpenAI `usage` into chia's profiler key names."""
    usage = (payload or {}).get("usage") or {}
    details = usage.get("completion_tokens_details") or {}
    return {
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
        "reasoning_tokens": details.get("reasoning_tokens"),
        "cache_read": (usage.get("prompt_tokens_details") or {}).get("cached_tokens"),
        "cache_write": None,
    }


# ------------------------------------------------------------------- app
@asynccontextmanager
async def _lifespan(application: FastAPI):
    application.state.client = httpx.AsyncClient(timeout=TIMEOUT_S)
    bearer()  # fail at startup, not on the first paid request
    try:
        yield
    finally:
        await application.state.client.aclose()


app = FastAPI(title="p2p Vertex LLM gateway", lifespan=_lifespan)


@app.get("/healthz")
async def healthz() -> JSONResponse:
    """Liveness plus the one fact worth watching. Never returns a token."""
    return JSONResponse(
        {
            "ok": True,
            "project": PROJECT,
            "default_location": DEFAULT_LOCATION,
            "token_expiry": token_expiry(),
            "auth_required": bool(TOKEN),
        }
    )


@app.get("/v1/models")
async def models() -> JSONResponse:
    """Synthesised: Vertex's openapi shim 404s on /models (verified)."""
    known = sorted(MODEL_LOCATIONS) or ["google/gemini-3.5-flash"]
    return JSONResponse(
        {"object": "list", "data": [{"id": m, "object": "model"} for m in known]}
    )


def _upstream_unreachable(exc: Exception, model: str, location: str, started: float):
    """Turn a transport failure into an OpenAI-shaped 502.

    Without this the exception escapes as an HTML 500 traceback, which a
    consumer parsing JSON reports as an unrelated schema error -- the same
    class of misleading downstream failure run_llm guards against.
    """
    log.error("upstream unreachable: %s: %s", type(exc).__name__, exc)
    _record(
        {
            "event": "llm_request",
            "ts": time.time(),
            "model": model,
            "location": location,
            "status": 502,
            "latency_s": round(time.monotonic() - started, 3),
            "stream": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
    )
    return JSONResponse(
        {
            "error": {
                "message": f"gateway could not reach Vertex: {type(exc).__name__}: {exc}",
                "type": "upstream_unreachable",
            }
        },
        status_code=502,
    )


async def _proxy(request: Request):
    if not _caller_authorised(request):
        return JSONResponse({"error": {"message": "bad gateway token"}}, status_code=401)

    try:
        body = json.loads(await request.body() or b"{}")
    except json.JSONDecodeError:
        return JSONResponse({"error": {"message": "body is not JSON"}}, status_code=400)

    model = normalise_model(body.get("model", ""))
    body["model"] = model
    location = location_for(model)
    url = upstream_url(location)
    streaming = bool(body.get("stream"))
    started = time.monotonic()

    client: httpx.AsyncClient = app.state.client

    if streaming:
        return await _proxy_stream(client, url, body, model, location, started)

    try:
        resp = await client.post(url, json=body, headers=_upstream_headers(bearer()))
        if resp.status_code == 401:
            # Clock skew, or the token went stale inside the request window.
            # Force one refresh and retry; a second 401 is the caller's problem.
            log.warning("upstream 401, forcing a token refresh and retrying once")
            resp = await client.post(
                url, json=body, headers=_upstream_headers(bearer(force=True))
            )
    except httpx.ConnectError as exc:
        # The connection never opened, so nothing was billed and a retry is
        # free. Deliberately NOT retrying read timeouts: that request may
        # still be generating upstream, and re-sending would pay twice.
        log.warning("upstream connect error (%s), retrying once", exc)
        try:
            resp = await client.post(
                url, json=body, headers=_upstream_headers(bearer())
            )
        except httpx.RequestError as exc2:
            return _upstream_unreachable(exc2, model, location, started)
    except httpx.RequestError as exc:
        return _upstream_unreachable(exc, model, location, started)

    try:
        payload = resp.json()
    except ValueError:
        payload = None

    _record(
        {
            "event": "llm_request",
            "ts": time.time(),
            "model": model,
            "location": location,
            "status": resp.status_code,
            "latency_s": round(time.monotonic() - started, 3),
            "stream": False,
            **_usage_fields(payload if isinstance(payload, dict) else {}),
        }
    )

    if payload is None:
        return JSONResponse(
            {"error": {"message": "upstream returned non-JSON", "body": resp.text[:500]}},
            status_code=resp.status_code,
        )
    return JSONResponse(payload, status_code=resp.status_code)


async def _proxy_stream(client, url, body, model, location, started):
    """SSE passthrough.

    Nothing in skydiscover streams today (no `stream` reference anywhere in
    skydiscover/llm/), but Vertex supports it and future consumers may, so
    forward chunks unbuffered rather than silently breaking them. No 401
    retry here: once the response has begun we cannot rewind it.
    """
    token = bearer()

    async def chunks():
        status = None
        try:
            async with client.stream(
                "POST", url, json=body, headers=_upstream_headers(token)
            ) as upstream:
                status = upstream.status_code
                # aiter_bytes, NOT aiter_raw: Vertex gzips the SSE stream, and
                # aiter_raw hands back the still-compressed body. We do not
                # forward content-encoding (the chunk boundaries are ours, not
                # upstream's), so the bytes must be decoded here or the client
                # receives binary garbage.
                async for chunk in upstream.aiter_bytes():
                    yield chunk
        finally:
            _record(
                {
                    "event": "llm_request",
                    "ts": time.time(),
                    "model": model,
                    "location": location,
                    "status": status,
                    "latency_s": round(time.monotonic() - started, 3),
                    "stream": True,
                }
            )

    return StreamingResponse(chunks(), media_type="text/event-stream")


@app.post("/v1/chat/completions")
async def chat_completions_v1(request: Request):
    return await _proxy(request)


@app.post("/chat/completions")
async def chat_completions_bare(request: Request):
    """Alias: the OpenAI SDK appends /chat/completions to whatever base_url it
    is given, so a consumer configured without the /v1 suffix lands here."""
    return await _proxy(request)


def main() -> None:
    import uvicorn

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    if not PROJECT:
        raise SystemExit("GCP_PROJECT (or GOOGLE_CLOUD_PROJECT) must be set")
    if not TOKEN and not _is_loopback(HOST):
        # Anything that can reach this port can spend the project's credits.
        raise SystemExit(
            f"refusing to bind {HOST} with no P2P_GATEWAY_TOKEN set: that would "
            "serve the project's Vertex credits to the whole VPC unauthenticated"
        )
    log.info("serving %s:%s -> Vertex project %s", HOST, PORT, PROJECT)
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
