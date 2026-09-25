---
name: llm-auth-via-vertex-adc
description: "This project's GCP credits are reachable only through Vertex AI; a Gemini API key bills a separate AI Studio credit pool that is empty"
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 469286b6-3b2a-4eed-87cd-c7a8d77ab06e
  modified: 2026-09-21T06:19:28.638Z
---

# Gemini access must go through Vertex AI, not a Gemini API key

The user's requirement is about billing: the money for this project lives in
the GCP project `chia-hackathon-paper2pipeline` (billing account
`01F777-A9E3C2-968C04`), and model usage has to draw on it. They chose the
Vertex AI route with application-default credentials for that reason, saying
they expected a `GEMINI_API_KEY` to be awkward to associate with GCP billing.

**They were right, and this was tested.** Do not repeat the mistake of
assuming that because a GCP project has `billingEnabled: true`, a Gemini API
key created in that project will bill against it. It does not. The public
Gemini endpoint (`generativelanguage.googleapis.com`) draws on a separate AI
Studio *prepayment credit* pool, and on this project that pool is empty: a
freshly created, correctly restricted project-scoped key authenticates fine
but every request returns `HTTP 402 "Your prepayment credits are depleted"`.
Meanwhile the same models over Vertex (`aiplatform.googleapis.com`) return
`HTTP 200` with `traffic_type: ON_DEMAND`, i.e. genuinely billing the GCP
account. Enabling `generativelanguage.googleapis.com` and creating the key
changes nothing about this. Resolving the 402 would require a billing setup
step inside AI Studio, which was never verified to work.

So the practical consequence: the Vertex route is the only one with money
behind it, and its one real limitation has to be engineered around rather
than avoided. ADC access tokens live 60 minutes (measured: 3598s),
skydiscover freezes the token string into `openai.OpenAI(api_key=...)` at
startup and has no refresh path anywhere, and Vertex returns 401 per request
once the token is stale. A full 250-iteration search runs far longer than an
hour, so the token must be refreshed by something outside skydiscover --
a local token-injecting proxy in front of Vertex, or
`LLMModelConfig.init_client` supplying an `openai.OpenAI(http_client=...)`
whose httpx auth hook refreshes via `google.auth`. Note a service account
does not avoid this; service accounts also mint 1-hour tokens.

Mechanical details for the Vertex route:

- Name the model `google/<model>` (for example `google/gemini-3.8-flash`),
  never `gemini-<model>`. Anything starting with `gemini-` matches
  skydiscover's provider prefix map, whose config post-init then overwrites
  that model's `api_base` with the public endpoint, silently discarding the
  Vertex `api_base`.
- `${VAR}` placeholders in these configs are expanded inside the Ray actor
  process, not the submitting shell, so credentials must be passed via the
  driver's `ray.init(runtime_env={"env_vars": ...})`.
- Model availability is per-project and per-region, must be probed, and
  **drifts**. An earlier note here said `google/gemini-3.8-flash` served only
  on `global` and 404ed on `us-central1`; on re-probe it returned 200 on
  both. Treat any recorded availability list as a stale snapshot.

Separately, the `antigravity` backend used by the distill, spec-review and
integrate stages authenticates through an OAuth sign-in stored in `~/.gemini`
rather than through ADC. It is an agentic CLI (`agy`) driven by subprocess,
not an HTTP endpoint, which is why it cannot be plugged into skydiscover or
pointed at a proxy.

**But do not conclude from that it is unrelated to GCP billing — it is not,
and an earlier version of this memory said so and was wrong.** Its traffic
shows up in this project's Vertex metrics and bills the same GCP account: a
single day of distill/spec-review/integrate work drew ~98M input and ~7.7M
output tokens on `gemini-3.8-flash` (the `ANTIGRAVITY_MODEL`), roughly $205 at
list price, while everything routed deliberately through the gateway was
cents. A separate auth mechanism does not imply a separate bill.

## Measuring spend, rather than estimating it

When asked how much has been spent, measure it. Do not extrapolate from the
calls made in the current session — that is exactly the error that produced
the wrong "LLM cost is a rounding error" claim above, because the expensive
consumer was an agent loop running in another session.

There is no cost API in `gcloud` and no BigQuery billing export on this
project, so the two authoritative sources reachable from the CLI are:

- **Token usage:** the Cloud Monitoring metric
  `aiplatform.googleapis.com/publisher/online_serving/token_count`, a DELTA
  metric labelled by `type` (input/output) with `model_user_id` on the
  resource. Query it over the desired window with `ALIGN_SUM`; empty buckets
  are omitted, so a single returned bucket means usage was confined to it.
- **Unit prices:** the Cloud Billing Catalog API. Compute Engine is service
  `6F81-5844-456A`, Vertex AI is `C7E2-9256-1C43`. Both are heavily
  paginated (Vertex alone has ~8.8k SKUs), so page through rather than
  reading the first response.

Match SKUs to the metric's own labels, and in particular **read the `source`
label before picking Global vs Regional.** `source: global` maps to the
"... Global Text Input/Output - Predictions" SKUs, while `source: us` and
`source: us-central1` map to the **Regional** ones, which cost 10% more.
Getting this wrong understated a bill by ~$21: almost all antigravity
traffic carries `source: us`, not `global`, even though the gateway's own
calls are `global`. Within either scope, pick the plain "- Predictions"
variant, not Batch, Priority, Off-Peak, Flex or Caching.

Two other parsing traps in that catalog: some SKUs have an empty
`pricingInfo` or `tieredRates`, so guard the lookup rather than indexing
blindly; and the Gemini text SKUs are single-tier, so `tieredRates[-1]` is
safe here but would silently pick the cheapest volume tier on a SKU that is
genuinely tiered.

### Always discount for implicit caching, or the estimate runs ~2.4x high

This is the single biggest correction the user has made to a cost estimate,
and it is easy to repeat. Pricing every input token at the list rate gave
$227 when the real bill was $90-100.

The cause: Gemini 2.5+ applies **implicit** context caching by default, and
cached prefix tokens bill at about a tenth of the list input rate (for
3.8 Flash Regional: $0.165/M against $1.65/M). Cloud Monitoring's
`token_count` does **not** reveal this — it counts every input token the
same way, and its `explicit_caching` label tracks only the *explicit*
caching API, which is a different feature. So the metric is a correct token
count and a badly misleading cost proxy.

This project's workload is close to the best case for implicit caching. The
antigravity agent loop resent an average of ~62,500 input tokens per request
over ~1,900 requests, because each turn replays the whole conversation, so
consecutive requests share nearly all of their prefix. Back-solving from the
real bill implies roughly a **90% cache-hit rate**, which is the figure to
assume for agent-loop traffic here unless something better is available.

Two practical rules:

- Treat a list-price input estimate as an **upper bound**, and present a
  range across plausible hit rates rather than a single number.
- **Output tokens are never cached or discounted**, so output cost is a
  hard floor and the trustworthy part of any estimate. Here output alone was
  $63 of the real $90-100 — about two thirds. If the output figure is a
  large fraction of the actual bill, that confirms the token counts are
  right and localises the error to input pricing.
