# Handover: a project-wide Vertex AI LLM gateway

Written 2026-09-20 by an assistant session that verified stage-3 DSE end to
end, then discovered that the only funded path to Gemini expires every 60
minutes. Picking this up should start with "decide where the gateway runs and
who may call it," not with writing the proxy — the code is the easy part.

Scope note: the original framing was "a proxy so skydiscover's search can run
longer than an hour." Per user direction (2026-09-20), that is **too narrow**
— LLMs will be used for more than skydiscover, so build one gateway for the
project rather than a stage-3 shim.

## Why this exists

Every LLM consumer in this project needs Gemini. There are exactly two HTTP
routes to Gemini, and **only one of them has money behind it**:

| Route | Host | Result |
|---|---|---|
| Vertex AI | `aiplatform.googleapis.com` | `HTTP 200`, `traffic_type: ON_DEMAND` — bills the GCP project |
| Gemini API (key) | `generativelanguage.googleapis.com` | `HTTP 402` "Your prepayment credits are depleted" |

Vertex is therefore mandatory. But Vertex authenticates with a **bearer token
that lives 60 minutes**, and no existing consumer refreshes it. A gateway that
owns token refresh centrally is the cheapest way to make every consumer
long-run-safe at once.

## What's confirmed, not guessed

Each of these was measured this session; re-verify rather than trusting the
doc if something behaves oddly.

**Billing / credentials**

- The project `chia-hackathon-paper2pipeline` has `billingEnabled: true`,
  linked to `billingAccounts/01F777-A9E3C2-968C04`, which is standalone
  (`masterBillingAccount: ''`, `parent: ''`, `open: true`).
- **Enabling `generativelanguage.googleapis.com` and creating a
  project-scoped, API-restricted key does NOT make Gemini API usage bill to
  that account.** A correctly created key authenticates fine and then returns
  `402 prepayment credits depleted` on every model. The Gemini API draws on a
  separate AI Studio prepay pool. Do not re-litigate this without first
  re-running the probe in "Test recipe" below; it cost this session a detour.
  Whether an AI Studio billing step would fix the 402 was never tested.
- ADC on `chia-head` resolves to
  `~/.config/gcloud/application_default_credentials.json` with
  `type: authorized_user` and a `refresh_token` present. So refresh is
  possible indefinitely — the access token is short-lived, the credential is
  not.
- Access token lifetime is **3598s** (`oauth2.googleapis.com/tokeninfo`,
  `expires_in`). A service account would *not* avoid this; SA tokens are also
  1 hour. Refresh is required either way.
- Vertex validates the bearer on **every** request: a bogus token returns
  `401 UNAUTHENTICATED`. Expiry fails hard, it does not degrade.

**Model availability is per-route AND per-region, and must be probed**

- Vertex: `google/gemini-3.8-flash` serves on location `global` only — it
  `404`s on `us-central1`. `google/gemini-2.5-flash` serves on both.
- Public endpoint: `gemini-2.5-flash` and `gemini-2.5-pro` return `404 "no
  longer available to new users"`. Names that work on one route may not exist
  on the other.

**Why the consumers can't just fix this themselves**

- `skydiscover/llm/openai.py` does
  `self.client = openai.OpenAI(api_key=self.api_key, base_url=self.api_base)`
  — the token is frozen into the client at construction. `grep` for
  `token_provider|refresh|google.auth` across `skydiscover/llm/` and
  `config.py` returns **nothing**.
- `Config.from_yaml` expands `${VAR}` exactly once, at `run_search` startup,
  and reads `os.environ` **inside the `EvolverNode` actor process** — not in
  the submitting shell. Credentials reach it via the driver's
  `ray.init(runtime_env={"env_vars": ...})`; `loop/constants.py` now forwards
  `GEMINI_API_KEY`, `VERTEX_ACCESS_TOKEN` and `GCP_PROJECT` when set.
- `LLMModelConfig.init_client` exists and `llm_pool.py` prefers it over
  constructing `OpenAILLM` — but it is `Optional[Callable]`, so it cannot come
  from YAML, and no code of ours runs inside the `EvolverNode` actor before
  skydiscover builds its LLM pool (that actor is evolve-flows' own class).
  Using `init_client` therefore means patching skydiscover. **This is why a
  gateway beats an in-process fix.**
- `chia`'s `antigravity` backend (used by distill/integrate) is **not** an
  HTTP client at all — `chia/models/antigravity.py` shells out to the `agy`
  CLI (`agy --print --output-format stream-json`) and authenticates via an
  OAuth login stored in `~/.gemini`. It cannot be pointed at the gateway
  without replacing the backend entirely.

## What the gateway has to do

Hard requirements, all traceable to the confirmed facts above:

1. Speak **OpenAI-compatible `POST /chat/completions`** — that is the only
   dialect skydiscover knows, and Vertex already exposes a compatible shim at
   `/v1/projects/<p>/locations/<loc>/endpoints/openapi`.
2. **Inject a fresh bearer per request**, obtained from `google.auth` (which
   refreshes off the `refresh_token` automatically). Clients then send a dummy
   or gateway-local `api_key`, and skydiscover's frozen-key behaviour stops
   mattering.
3. Survive a **37-hour** run (250 iterations × ~9-10 min/evaluation, measured
   from build + 6-trace fan-out = 517s). This is the whole point.
4. **Route model → location**, because availability is regional. At minimum,
   send `gemini-3.8-flash` to `global`.
5. Optionally **normalise model names** so callers may write either
   `gemini-3.8-flash` or `google/gemini-3.8-flash`. This permanently defuses
   a real trap: skydiscover's `_BARE_PREFIX_MAP` matches any name starting
   `gemini-` and *force-overwrites* that model's `api_base` with the public
   endpoint, silently discarding your gateway URL. Until/unless the gateway
   normalises names, configs pointed at it **must** use the `google/` prefix.
   See `experiments/config_adaevolve_smoke_vertex.yaml` for the worked
   example.

## Decisions to make first (these shape the code)

1. **Where it runs, and what it binds to.** The stage-3 `EvolverNode` actor
   is placed with `resources={"evolver": 1.0}`, which today only the head
   advertises — so `127.0.0.1` would work *for that consumer only*. Since the
   requirement is project-wide, consumers may live on worker VMs, which means
   binding to the head's internal/tailnet address instead. Options: head +
   VPC IP, a Ray detached actor called over Ray, or a per-node sidecar. If you
   bind beyond localhost, note the tunnel/port caveats in
   `chia/base/dispatch_proxy.py` about which ports are actually reachable
   from tunneled workers.
2. **Auth, if non-local.** Anything that can reach the gateway can spend the
   project's credits. A shared secret checked against the incoming
   `Authorization` header is the minimum; that secret is what consumers put in
   their `api_key` field.
3. **Identity.** ADC here is a *personal* `authorized_user` account, so an
   unattended gateway would spend and authenticate as whoever last ran
   `gcloud auth application-default login`. A service account is the right
   answer for something long-lived and multi-tenant (it does not fix expiry,
   but `google.auth` treats both identically, so the code does not change).
4. **Lifecycle.** Who starts it, and does it outlive a job? Candidates: a
   detached Ray actor pinned to the head, a `systemd --user` unit, or a new
   `available_node_types` entry in `cluster/cluster.yaml`. Starting it from
   `run_dse` was considered and rejected as too stage-3-specific.
5. **Streaming.** Unverified: whether any consumer requests `stream=True`.
   skydiscover's calls appeared non-streaming in this session's logs, but that
   was not exhaustively checked. If anything streams, the gateway must pass
   SSE through rather than buffering.
6. **Whether to migrate distill/integrate off Antigravity.** Optional, and a
   bigger change — it means swapping `C.LLM_BACKEND` to an HTTP-speaking
   backend. Worth considering given the Antigravity permission failures seen
   in job `raysubmit_wj5VswCjC9KdNtjq`
   (`Permission denied: '/home/ray/.gemini/antigravity-cli'`), but it is a
   separate decision from building the gateway.

## Implementation sketch

The auth core is small, and this snippet was **run and confirmed working** in
`chia_env` this session: `google.auth` 2.58.0 is already installed,
`google.auth.default()` auto-discovers the project
(`chia-hackathon-paper2pipeline`, so the gateway does not need `GCP_PROJECT`
passed in), and the cached credential came back `valid=False, expired=True`
and then refreshed cleanly to a fresh 254-char token with a new expiry — i.e.
the refresh path works off the existing `refresh_token` with no extra setup.

```python
import google.auth
from google.auth.transport.requests import Request

_creds, _project = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

def bearer() -> str:
    # Refreshes in place when expired; no-op when still valid.
    if not _creds.valid:
        _creds.refresh(Request())
    return _creds.token
```

Then per request: read the incoming OpenAI-shaped JSON, decide the target
location from the model name, rewrite the path to
`/v1/projects/{project}/locations/{loc}/endpoints/openapi/chat/completions`,
replace the `Authorization` header with `Bearer {bearer()}`, forward, and
stream the response back unmodified. Guard the refresh with a lock if the
server is threaded.

Consumers then need only:

```yaml
llm:
  api_base: "http://<gateway-host>:<port>/v1"
  api_key: ${P2P_GATEWAY_TOKEN}      # the shared secret, not a Google credential
  models:
    - name: google/gemini-3.8-flash   # keep the google/ prefix unless the gateway normalises
      weight: 1.0
```

Consider emitting per-request token counts — `adopt_a_paper_loop.main()`
already calls `start_collector()` for "token + compute cost per accepted
change (chia viz-profile)", and a gateway is the natural single choke point
for that accounting.

## Test recipe

Confirm the gateway is actually reaching Vertex, and re-confirm the premises:

```bash
# 1. Vertex works and bills the GCP project (expect 200 + ON_DEMAND)
T=$(gcloud auth application-default print-access-token)
BASE="https://aiplatform.googleapis.com/v1/projects/$GCP_PROJECT/locations/global/endpoints/openapi"
curl -s -X POST "$BASE/chat/completions" \
  -H "Authorization: Bearer $T" -H "Content-Type: application/json" \
  -d '{"model":"google/gemini-3.8-flash","messages":[{"role":"user","content":"reply with OK"}],"max_tokens":2000}'

# 2. Token lifetime (expect ~3598)
curl -s "https://oauth2.googleapis.com/tokeninfo?access_token=$T" | python -m json.tool | grep expires_in

# 3. Stale tokens fail hard (expect 401 UNAUTHENTICATED)
curl -s -o /dev/null -w '%{http_code}\n' -X POST "$BASE/chat/completions" \
  -H "Authorization: Bearer ya29.bogus" -H "Content-Type: application/json" \
  -d '{"model":"google/gemini-3.8-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":800}'

# 4. Which Vertex models/regions serve (availability is project-specific)
for LOC in global us-central1; do for M in google/gemini-3.8-flash google/gemini-2.5-flash; do
  echo -n "$LOC $M -> "
  curl -s -o /dev/null -w '%{http_code}\n' -X POST \
    "https://aiplatform.googleapis.com/v1/projects/$GCP_PROJECT/locations/$LOC/endpoints/openapi/chat/completions" \
    -H "Authorization: Bearer $T" -H "Content-Type: application/json" \
    -d "{\"model\":\"$M\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":800}"
done; done
```

The real end-to-end test is a DSE run that outlives 60 minutes. Until the
gateway exists, `experiments/config_adaevolve_smoke_vertex.yaml` with
`max_iterations: 3` finishes well inside one token lifetime and is the right
smoke test.

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
  (`/tmp/ray/session_*/logs/runtime_env*.log`) on the head. Tolerable for a
  60-minute token; a consideration for any long-lived shared secret.

## Handy commands

```bash
# credentials
gcloud auth application-default print-access-token
python -c "import json,os;print(json.load(open(os.path.expanduser('~/.config/gcloud/application_default_credentials.json')))['type'])"

# billing / service state
gcloud billing projects describe "$GCP_PROJECT"
gcloud services list --enabled --project="$GCP_PROJECT" | grep -iE "aiplatform|generativelanguage"

# what the evolver actor is actually doing when it looks stuck
sudo env "PATH=$PATH" py-spy dump --pid $(pgrep -f "ray::EvolverNode" | head -1)
python -c "
import ray; ray.init(address='auto', log_to_driver=False)
from ray.util.state import list_tasks
print([(t['name'], t['state']) for t in list_tasks(limit=300) if t['state'] not in ('FINISHED','FAILED')])"
```
