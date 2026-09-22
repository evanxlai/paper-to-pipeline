"""Run artifacts, spec validation, and baseline bookkeeping
(memcpy-example Dumper conventions)."""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import constants as C


class Dumper:
    """Timestamped artifact writer under out/ (never committed)."""

    def __init__(self, out_dir: Path = C.OUT_DIR):
        self.dir = Path(out_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.prefix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_")

    def _p(self, name: str) -> Path:
        return self.dir / (self.prefix + name)

    def text(self, name: str, content: str) -> Path:
        p = self._p(name)
        p.write_text(content)
        return p

    def json(self, name: str, obj) -> Path:
        return self.text(name, json.dumps(obj, indent=2, default=str))

    def llm(self, name: str, resp) -> Path:
        body = (
            f"success: {getattr(resp, 'success', None)}\n"
            f"usage: {getattr(resp, 'usage', None)}\n\n"
            f"## result\n{resp.result}\n\n## stream\n{resp.stream_result}\n"
        )
        return self.text(name + ".md", body)


def validate_json(
    text: str, schema_path, require_jsonschema: bool = False
) -> tuple[dict | None, list[str]]:
    """Parse + schema-check one document against the schema at `schema_path`.
    Uses jsonschema when installed; falls back to a required-keys check so the
    loop still runs in a bare env.

    `require_jsonschema` turns that fallback off. The stage-2 plan schemas put
    almost all of their force in nested `required`, `if`/`then` and
    `additionalProperties: false` -- none of which the fallback sees -- so for
    a plan the degraded path is not a weaker check, it is no check at all: it
    would wave through a port plan with an empty spec_map, or one carrying a
    storage budget under an invented field name. A stage that would rather
    fail than pretend sets this and gets a plain error instead."""
    try:
        document = json.loads(text)
    except json.JSONDecodeError as e:
        return None, [f"not valid JSON: {e}"]
    schema = json.loads(Path(schema_path).read_text())
    try:
        import jsonschema
    except ImportError:
        if require_jsonschema:
            return document, [
                "jsonschema is not installed, and this document cannot be "
                "meaningfully checked without it (its schema relies on nested "
                "required, if/then and additionalProperties)"
            ]
        missing = [k for k in schema.get("required", []) if k not in document]
        return document, [f"missing required field: {k}" for k in missing]

    v = jsonschema.Draft202012Validator(schema)
    errs = [f"{'/'.join(map(str, e.path))}: {e.message}" for e in v.iter_errors(document)]
    return (document, errs) if errs else (document, [])


def validate_spec(spec_text: str) -> tuple[dict | None, list[str]]:
    """Parse + schema-check a distilled feature spec."""
    return validate_json(spec_text, C.SPEC_SCHEMA_PATH)


def truncate(text: str, limit: int = 300) -> str:
    """Cap one validator message. jsonschema inlines the whole offending
    value on a type error, which can be an entire nested array."""
    return text if len(text) <= limit else text[:limit] + " ...[truncated]"


def extract_json_blocks(text: str) -> list[str]:
    """Every fenced JSON block in an LLM reply, in order.

    Stage 2 emits two documents in one reply, which is exactly the case
    `extract_json_block` below gets wrong: it keeps only the last block, so a
    correct two-document reply would silently lose the port plan and the node
    would report schema errors about a test plan missing every port-plan
    field. Callers that expect n documents should check the count themselves
    and say so, rather than indexing into whatever came back."""
    import re

    return re.findall(r"```(?:json)?\s*\n(.*?)```", text, re.S)


def extract_json_block(text: str) -> str:
    """Pull the last fenced JSON block from an LLM reply, else the whole text."""
    blocks = extract_json_blocks(text)
    return blocks[-1] if blocks else text


def load_trace_list(path: Path) -> list[str]:
    """One trace path per line; blank lines and '#'-prefixed comments
    (the TODO(week 1) placeholders these files ship with) are skipped."""
    lines = Path(path).read_text().splitlines()
    return [t.strip() for t in lines if t.strip() and not t.strip().startswith("#")]


def plan_paths(host: str, feature: str | None = None) -> tuple[Path, Path]:
    """Where stage 2's two artifacts land for one host."""
    feature = feature or C.FEATURE_NAME
    return (
        C.PLAN_DIR / f"{feature}.{host}.plan.json",
        C.PLAN_DIR / f"{feature}.{host}.tests.json",
    )


def baseline_path(host: str, budget: str) -> Path:
    return C.REPO_ROOT / "hosts" / host / "baselines" / f"{budget}.json"


def record_baseline(host: str, budget: str, metrics: dict) -> None:
    p = baseline_path(host, budget)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(metrics, indent=2))


def load_baseline(host: str, budget: str) -> dict | None:
    p = baseline_path(host, budget)
    return json.loads(p.read_text()) if p.exists() else None
