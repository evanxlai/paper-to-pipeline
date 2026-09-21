# The project Vertex AI LLM gateway

`loop/llm_gateway.py` is an OpenAI-compatible reverse proxy that sits in
front of Vertex AI and injects a freshly-refreshed Google bearer token on
every request. It exists so that LLM consumers can run longer than the ~60
minutes a Vertex access token lives.

Status: **built and running.** This file was a handover describing the
problem; it is now the gateway's documentation. The section "What was wrong
in the first draft" records two claims the handover made that turned out to
be false on re-probe — read it before trusting anything here that you have
not re-measured yourself.

## Why it exists

There are exactly two HTTP routes to Gemini, and **only one has money behind
it**:

| Route | Host | Result |
|---|---|---|
| Vertex AI | `aiplatform.googleapis.com` | `HTTP 200`, `traffic_type: ON_DEMAND` — bills the GCP project |
| Gemini API (key) | `generativelanguage.googleapis.com` | `HTTP 402` "Your prepayment credits are depleted" |

Vertex is therefore mandatory. But Vertex authenticates with a bearer token
that lives ~1 hour and validates it on every request, and no consumer
refreshes it:

- `skydiscover/llm/openai.py:86` does
  `openai.OpenAI(api_key=self.api_key, base_url=self.api_base)` — the token is
  frozen into the client at construction. `grep` for
  `token_provider|refresh|google.auth` across `skydiscover/llm/` returns
  nothing.
- Its one extension point, `LLMModelConfig.init_client` (`config.py:130`), is
  `Optional[Callable]`, so it cannot come from YAML, and no code of ours runs
  inside the `EvolverNode` actor before skydiscover builds its LLM pool.

A 250-iteration search is ~37 hours. Without the gateway it dies with `401
UNAUTHENTICATED` about an hour in. The gateway owns refresh centrally, so
every HTTP consumer becomes long-run-safe at once.

## Using it

Consumer config:

```yaml
llm:
  api_base: "http://10.128.0.2:8900/v1"
  api_key: ${P2P_GATEWAY_TOKEN}       # the gateway's shared secret, not a Google credential
  models:
    - name: google/gemini-3.5-flash   # the google/ prefix is MANDATORY -- see the trap below
      weight: 1.0
```

Before submitting a job, export the secret so `loop/constants.py` forwards it
into the `EvolverNode` actor's `runtime_env` (skydiscover expands `${VAR}`
inside the actor process, not in your shell):

```bash
export P2P_GATEWAY_TOKEN="$(grep P2P_GATEWAY_TOKEN ~/.config/p2p/gateway.env | cut -d= -f2-)"
chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" --stage dse
```

### The `google/` prefix trap

**A config pointed at the gateway must name the model `google/<model>`, never
`gemini-<model>`.** Any name starting `gemini-` matches skydiscover's
`_BARE_PREFIX_MAP`, and `LLMConfig.__post_init__` then force-overwrites that
model's `api_base` with the public endpoint (`config.py:197-208`) — silently
discarding your gateway URL. This happens **inside skydiscover's own process
at config-parse time, before any HTTP request exists**, so the gateway cannot
defend against it; the request never reaches the gateway at all. Only the
prefix can prevent it.

(The gateway *does* normalise bare `gemini-*` names for its own direct
callers — curl, chia backends. That is convenience for them, and is not a
fix for the above.)

## Operating it

Installed as a `systemd --user` unit on the head, deliberately independent of
Ray so it outlives any single job:

```bash
./scripts/install_llm_gateway.sh            # idempotent; keeps the existing secret
./scripts/install_llm_gateway.sh --rotate   # mint a new secret

systemctl --user status p2p-llm-gateway
systemctl --user restart p2p-llm-gateway
tail -f ~/.local/state/p2p-llm-gateway.log
curl -s http://10.128.0.2:8900/healthz | python -m json.tool
```

**Lingering must be enabled or the unit dies at logout**, which would end a
37-hour run:

```bash
sudo loginctl enable-linger "$USER"
```

Configuration is `~/.config/p2p/gateway.env` (mode 0600): `GCP_PROJECT`,
`P2P_GATEWAY_HOST`, `P2P_GATEWAY_PORT`, `P2P_GATEWAY_TOKEN`. Optional:
`P2P_GATEWAY_MODEL_LOCATIONS` (a `{"model": "location"}` JSON map),
`P2P_GATEWAY_TIMEOUT`, `P2P_GATEWAY_ACCOUNTING`.

### Design decisions, and what they cost

- **Bound to the head's VPC IP (`10.128.0.2:8900`), not loopback**, so
  consumers on worker VMs and in the antigravity Docker container can reach
  it. Consequence: the shared secret is mandatory, and the gateway refuses to
  start if it is bound non-loopback without one. GCP ingress is default-deny
  and only `tcp:22`/ICMP/RDP are open externally, so the port is
  VPC-internal — but anything inside the VPC that learns the secret can spend
  the project's credits.
- **Authenticates as personal ADC** (`google.auth.default()`), i.e. as
  whoever last ran `gcloud auth application-default login`. Moving to a
  service account is a config change, not a code change — `google.auth`
  treats both identically. Note a service account would *not* avoid expiry;
  SA tokens are also 1 hour.
- **The VM's own identity cannot be used.** `chia-head`'s attached compute
  default SA has access scopes that do not include `cloud-platform`, so a
  metadata-server token cannot call Vertex without re-scoping (and stopping)
  the VM.
- **Ports.** 8000-8010 are SSH-tunnel reserved and 8000-8099 are ChiaTool's
  probe range (`chia/models/vllm.py:10-16`), hence 8900.

### Accounting

One JSONL row per request in `out/llm_gateway.jsonl` (gitignored): model,
location, status, latency, and token counts under chia's profiler key names
(`input_tokens`, `output_tokens`, `reasoning_tokens`, `cache_read`,
`cache_write`).

Not wired into `chia.trace.profiler` directly, for two structural reasons:
that collector is a non-detached, per-job Ray actor that dies with the
driver, and `chia viz-profile` only renders counts fed through
`ChiaProfiler.add_info()`, which is thread-local to an in-flight
`ChiaFunction` and unreachable from a separate process
(`chia/trace/profile_viz.py:407-410`).

**Known gap:** streamed requests log no token counts. Usage arrives in the
final SSE chunk, which the gateway passes through without parsing.

## What was wrong in the first draft

Following this project's convention of separating what was confirmed from
what was assumed. Both of these were in the handover version of this
document, were re-probed on 2026-09-20, and were false:

1. **"`google/gemini-3.8-flash` serves on location `global` only, it 404s on
   `us-central1`."** Not true any more: `global` and `us-central1` both return
   `200`, for `gemini-3.8-flash` and `gemini-2.5-flash` alike. Model→location
   routing is insurance, not a hard requirement. Availability drifts —
   re-probe rather than trusting either version of this claim.

2. **"Normalising model names in the gateway permanently defuses the
   `_BARE_PREFIX_MAP` trap."** It cannot, for the reason given under "The
   `google/` prefix trap" above: the damage is done in the client's process
   before a request exists. The handover's "until/unless the gateway
   normalises names, configs must use the `google/` prefix" should read
   "configs must use the `google/` prefix, unconditionally."

A third thing the first implementation got wrong, caught only by testing
against live Vertex rather than a stub: **SSE passthrough used httpx's
`aiter_raw()`, which yields the still-compressed body.** Vertex gzips its
stream, and the gateway does not forward `content-encoding`, so callers got
binary garbage. It must be `aiter_bytes()`. There is now a regression test
whose stub gzips for exactly this reason.

## Verified facts (re-measure rather than trust)

Measured 2026-09-20 from `chia-head` against `chia-hackathon-paper2pipeline`:

- Project has `billingEnabled: true`, billing account
  `01F777-A9E3C2-968C04`, standalone and open.
- **Enabling `generativelanguage.googleapis.com` and creating a
  project-scoped key does NOT make Gemini API usage bill to that account.**
  The key authenticates fine and returns `402 prepayment credits depleted` on
  every model; the Gemini API draws on a separate AI Studio prepay pool.
  Whether an AI Studio billing step would fix it was never tested. Do not
  re-litigate without re-running the probe below — it has cost a session once.
- ADC on `chia-head` is `~/.config/gcloud/application_default_credentials.json`,
  `type: authorized_user`, with a `refresh_token`. Refresh works indefinitely;
  only the access token is short-lived.
- Access token lifetime **3593s**. Vertex answers a bogus bearer with `401
  UNAUTHENTICATED` — expiry fails hard, it does not degrade.
- `google.auth.default()` auto-discovers the project, and a cached expired
  credential refreshed in 0.06s.
- The OpenAI SDK posts to `{base_url}/chat/completions` and sends its
  `api_key` as `Authorization: Bearer <key>`.
- Nothing in skydiscover streams (no `stream` reference in `skydiscover/llm/`).
  The gateway supports it anyway.

### Test recipe

```bash
# Unit tests (stubbed upstream, spends nothing)
pytest loop/tests/test_llm_gateway.py

GW=$(grep P2P_GATEWAY_TOKEN ~/.config/p2p/gateway.env | cut -d= -f2-)
BASE=http://10.128.0.2:8900/v1

# Auth is enforced (expect 401, then 200)
curl -s -o /dev/null -w '%{http_code}\n' -X POST "$BASE/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"google/gemini-3.5-flash","messages":[{"role":"user","content":"hi"}]}'

# Real call: expect 200 and traffic_type ON_DEMAND, which proves GCP billing
curl -s -X POST "$BASE/chat/completions" \
  -H "Authorization: Bearer $GW" -H "Content-Type: application/json" \
  -d '{"model":"google/gemini-3.5-flash","messages":[{"role":"user","content":"reply with OK"}],"max_tokens":2000}'

# Re-confirm the premise directly against Vertex, bypassing the gateway
T=$(gcloud auth application-default print-access-token)
V="https://aiplatform.googleapis.com/v1/projects/$GCP_PROJECT/locations/global/endpoints/openapi"
curl -s "https://oauth2.googleapis.com/tokeninfo?access_token=$T" | grep -o '"expires_in":[0-9]*'
curl -s -o /dev/null -w '%{http_code}\n' -X POST "$V/chat/completions" \
  -H "Authorization: Bearer ya29.bogus" -H "Content-Type: application/json" \
  -d '{"model":"google/gemini-3.8-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":800}'
```

**The test that actually matters** is a call that succeeds after the gateway
has been up for more than 60 minutes — that is the entire point of the
component, and the unproxied behaviour at that moment is a hard 401. The unit
suite covers it deterministically (expire the fake credential, assert one
refresh and the new token on the wire); only wall-clock covers it for real.

## Not covered by the gateway

`chia`'s `antigravity` backend — used by the distill, spec-review and
integrate stages, i.e. five of the six LLM call sites — is **not** an HTTP
client. `chia/models/antigravity.py` shells out to the `agy` CLI and
authenticates via an OAuth login in `~/.gemini`, so it cannot be pointed at
the gateway without replacing the backend.

If that migration is ever wanted, the natural target is *not* this gateway
but chia's own `OpenAICompatLLM`, which already supports a `token_provider`
callable (`openai_compat.py:450`) and ships a Vertex ADC one
(`chia/models/vertex.py:681`). Note it would also need a new `cluster.yaml`
node type: `{"llm": 1.0}` and `{"opencode_creds": 1.0}` currently have no
node advertising them, so flipping `P2P_LLM_BACKEND` today hangs in
`PENDING_NODE_ASSIGNMENT`.

## Known unrelated gaps (do not fix under this issue)

- **`sim-worker-1` (`10.128.0.23`) cannot serve objects above Ray's inline
  threshold.** 1KB returns fine; 500KB times out, 3/3 deterministically,
  while `sim-worker-0` succeeds 3/3. `CBP2025Node.build` returns a ~492KB
  binary, so any evaluation whose build lands there hangs for Ray's 10-minute
  object-fetch timeout and then scores 0 (`ObjectFetchTimedOutError`). Disk
  (77GiB free) and object-manager port reachability were both ruled out.
  Also note `sim-worker-0` is registered **twice** (as `10.128.0.22` and as
  tunnel alias `127.0.0.2`), which is why `cbp2025` reads 96 instead of 64.
  **This blocks a real DSE run independently of the token problem.**
- `sr_params.h` is inert — nothing in the cbp2025 kit `#include`s it, so every
  candidate compiles identically and the search landscape is flat. Stage-2
  integration's job.
- `config_adaevolve.yaml`'s `max_parallel_iterations: 8` races concurrent
  builds against the shared `~/cbp2025` checkout. Needs per-evaluation
  checkouts, or keep it at 1.
- `promote_finalists` in `loop/dse.py` is still `NotImplementedError`.
- Secrets forwarded through `runtime_env` are written to Ray's own logs
  (`/tmp/ray/session_*/logs/runtime_env*.log`) on the head. That now applies
  to a long-lived shared secret rather than a 60-minute token, so rotate it
  (`./scripts/install_llm_gateway.sh --rotate`) rather than treating it as
  permanent.

## Handy commands

```bash
# credentials
gcloud auth application-default print-access-token
gcloud billing projects describe "$GCP_PROJECT"
gcloud services list --enabled --project="$GCP_PROJECT" | grep -iE "aiplatform|generativelanguage"

# what the evolver actor is actually doing when it looks stuck
sudo env "PATH=$PATH" py-spy dump --pid $(pgrep -f "ray::EvolverNode" | head -1)
python -c "
import ray; ray.init(address='auto', log_to_driver=False)
from ray.util.state import list_tasks
print([(t['name'], t['state']) for t in list_tasks(limit=300) if t['state'] not in ('FINISHED','FAILED')])"
```
