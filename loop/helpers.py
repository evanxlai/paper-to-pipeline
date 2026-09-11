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


def validate_spec(spec_text: str) -> tuple[dict | None, list[str]]:
    """Parse + schema-check a distilled feature spec. Uses jsonschema when
    installed; falls back to a required-keys check so the loop still runs
    in a bare env."""
    try:
        spec = json.loads(spec_text)
    except json.JSONDecodeError as e:
        return None, [f"not valid JSON: {e}"]
    schema = json.loads(Path(C.SPEC_SCHEMA_PATH).read_text())
    try:
        import jsonschema

        v = jsonschema.Draft202012Validator(schema)
        errs = [f"{'/'.join(map(str, e.path))}: {e.message}" for e in v.iter_errors(spec)]
        return (spec, errs) if errs else (spec, [])
    except ImportError:
        missing = [k for k in schema["required"] if k not in spec]
        return spec, [f"missing required field: {k}" for k in missing]


def extract_json_block(text: str) -> str:
    """Pull the last fenced JSON block from an LLM reply, else the whole text."""
    import re

    blocks = re.findall(r"```(?:json)?\s*\n(.*?)```", text, re.S)
    return blocks[-1] if blocks else text


def baseline_path(host: str, budget: str) -> Path:
    return C.REPO_ROOT / "hosts" / host / "baselines" / f"{budget}.json"


def record_baseline(host: str, budget: str, metrics: dict) -> None:
    p = baseline_path(host, budget)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(metrics, indent=2))


def load_baseline(host: str, budget: str) -> dict | None:
    p = baseline_path(host, budget)
    return json.loads(p.read_text()) if p.exists() else None
