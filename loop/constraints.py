"""Stage 4's constraints: what a DSE candidate must satisfy before it is scored.

A constraint is `{metric, comparison, allowance}` (docs/stages.md, stage 4).
Storage is the first one, and the only one the demonstration uses today. It
is not meant to be the only one. Nothing in the evaluator is specific to
storage: it is handed a list of constraints and applies whichever it gets.
Latency, logic cost, a port count, an IPC floor or a CycWPPKI ceiling are all
the same shape, and adding one is a metric plus an entry in the set.

Metrics come in two phases, because some bounds can be decided from the
candidate's knob values alone and some only by running it.

  static    computed from the header values before anything is built.
            `storage_bits` is one: the spec's `state[].size_formula` and the
            port plan's `host_storage.terms` give every structure's size at
            any knob setting, so an over-budget candidate is refused without
            spending a build or a trace. New static metrics go in
            STATIC_METRICS.
  measured  read off the screening run's aggregate after the traces ran. Any
            aggregate key (`ipc_50perc_amean`, ...) is a measured metric, so
            a measured constraint needs no code here at all.

Only stage 4 builds a constraint set (the one rule in docs/stages.md). The
formula helpers are also used by spec_checks and plan_checks, but there they
only check self-consistency -- a formula evaluated at the defaults equals the
declared size. That is accounting, a fact about the paper or the host, and
never a comparison against an allowance.

A candidate cannot misreport its own cost. The evaluator parses the values
out of the header it is about to build and re-derives every metric from
those, so the only way to change the accounted storage is to change a value
the build then compiles in.
"""

from __future__ import annotations

import ast
import math
import operator
import re
from dataclasses import dataclass, field

FEATURE_PREFIX = "SR_"
HOST_PREFIX = "HOST_"


# ------------------------------------------------------------------ formulas


class FormulaError(ValueError):
    """A formula that cannot be parsed or evaluated."""


def _log2(x):
    if x <= 0:
        raise FormulaError(f"log2 of {x}")
    r = math.log2(x)
    return int(r) if float(r).is_integer() else r


_FUNCS = {
    "min": min, "max": max, "abs": abs, "int": int,
    "log2": _log2, "ceil": math.ceil, "floor": math.floor,
}

# `^`, `&` and `|` are deliberately absent. A planner or distiller writing
# `2^LOGG` means a power, and Python would evaluate it as XOR without a word:
# 2^10 is 8, not 1024. Refusing the operator turns that into a finding.
_BINOPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
    ast.LShift: operator.lshift, ast.RShift: operator.rshift,
}
_UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos}


def _as_int(value, what: str) -> int:
    if isinstance(value, float):
        if not value.is_integer():
            raise FormulaError(f"{what} needs an integer, got {value}")
        return int(value)
    return value


def _parse(expr: str) -> ast.Expression:
    if not isinstance(expr, str) or not expr.strip():
        raise FormulaError("empty formula")
    try:
        return ast.parse(expr.strip(), mode="eval")
    except SyntaxError as e:
        raise FormulaError(f"does not parse: {e.msg}") from None


def names_in(expr: str) -> set[str]:
    """Every variable a formula reads, not counting the functions it calls."""
    tree = _parse(expr)
    called = {
        n.func.id for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    return {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} - called


def evaluate(expr: str, env: dict):
    """Arithmetic over `env`, and nothing else. No attribute access, no
    subscripts, no comparisons: a storage formula is a sum of products."""

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
                and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in env:
                raise FormulaError(f"unknown name '{node.id}'")
            value = env[node.id]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise FormulaError(f"'{node.id}' is {value!r}, not a number")
            return value
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            return _UNARY[type(node.op)](ev(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
            left, right = ev(node.left), ev(node.right)
            if isinstance(node.op, (ast.LShift, ast.RShift)):
                left, right = _as_int(left, "a shift"), _as_int(right, "a shift")
                if not 0 <= right <= 64:
                    raise FormulaError(f"shift by {right}")
            if isinstance(node.op, ast.Pow) and abs(right) > 64:
                raise FormulaError(f"exponent {right}")
            try:
                return _BINOPS[type(node.op)](left, right)
            except ZeroDivisionError:
                raise FormulaError("division by zero") from None
        if isinstance(node, ast.BinOp):
            raise FormulaError(
                f"operator {type(node.op).__name__} is not allowed; write a power "
                f"as ** or <<, never ^")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in _FUNCS and not node.keywords:
            return _FUNCS[node.func.id](*[ev(a) for a in node.args])
        raise FormulaError(f"'{ast.unparse(node)}' is not plain arithmetic")

    return ev(_parse(expr))


# ------------------------------------------------------------------ knobs


@dataclass(frozen=True)
class Knob:
    """One #define in the params header, feature or host alike."""

    macro: str
    name: str
    type: str
    default: object
    range: str
    origin: str  # "feature" (spec parameters[]) or "host" (plan host_knobs[])


def feature_knobs(spec: dict) -> list[Knob]:
    return [
        Knob(FEATURE_PREFIX + str(p["name"]).upper(), p["name"], p.get("type", "int"),
             p.get("default"), p.get("range", ""), "feature")
        for p in (spec or {}).get("parameters") or []
    ]


def host_knobs(port_plan: dict | None) -> list[Knob]:
    return [
        Knob(k.get("macro") or HOST_PREFIX + str(k["name"]).upper(), k["name"],
             k.get("type", "int"), k.get("default"), k.get("range", ""), "host")
        for k in (port_plan or {}).get("host_knobs") or []
    ]


def all_knobs(spec: dict, port_plan: dict | None) -> list[Knob]:
    return feature_knobs(spec) + host_knobs(port_plan)


def range_error(knob: Knob, value) -> str | None:
    """Why `value` is not a legal value of `knob`, or None if it is."""
    from spec_checks import parse_range

    if knob.type == "bool":
        # C spells a flag either way, and specs do too: 0/1 is as legal as
        # true/false.
        ok = isinstance(value, bool) or (isinstance(value, int) and value in (0, 1))
        return None if ok else f"{value!r} is not true, false, 0 or 1"
    parsed = parse_range(knob.range)
    if parsed is None:
        return None  # an unparsable range is spec_checks' finding, not a veto here
    if parsed[0] == "choices":
        if knob.type == "enum":
            if not isinstance(value, int) or not 0 <= value < len(parsed[1]):
                return f"{value!r} is not an index in 0..{len(parsed[1]) - 1}"
            return None
        return None if str(value) in parsed[1] else f"{value!r} is not one of {parsed[1]}"
    _, lo, hi, mods = parsed
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return f"{value!r} is not a number"
    if knob.type == "int" and not float(value).is_integer():
        return f"{value!r} is not an integer"
    if not lo <= value <= hi:
        return f"{value} is outside [{lo:g}, {hi:g}]"
    if "pow2" in mods and not (float(value).is_integer() and int(value) > 0
                               and int(value) & (int(value) - 1) == 0):
        return f"{value} is not a power of two"
    return None


# ------------------------------------------------------------------ header

_DEFINE_RE = re.compile(r"^\s*#\s*define\s+([A-Za-z_][A-Za-z0-9_]*)\s*(.*?)\s*(?://.*)?$")
_INT_RE = re.compile(r"^-?(?:0[xX][0-9a-fA-F]+|\d+)$")
_FLOAT_RE = re.compile(r"^-?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?[fF]?$")


def _literal(text: str):
    text = text.strip()
    if text in ("true", "false"):
        return text == "true"
    if _INT_RE.match(text):
        return int(text, 16) if "x" in text.lower() else int(text, 10)
    if _FLOAT_RE.match(text):
        return float(text.rstrip("fF"))
    raise ValueError(text)


def parse_header(text: str) -> tuple[dict, list[str]]:
    """{macro: value} for every #define with a plain literal value."""
    values: dict = {}
    errors: list[str] = []
    for line in (text or "").splitlines():
        m = _DEFINE_RE.match(line)
        if not m:
            continue
        macro, body = m.group(1), m.group(2)
        if not (macro.startswith(FEATURE_PREFIX) or macro.startswith(HOST_PREFIX)):
            continue
        if macro in values:
            errors.append(f"{macro} is defined twice")
            continue
        try:
            values[macro] = _literal(body)
        except ValueError:
            errors.append(
                f"{macro} is '{body}', which is not a plain literal. Write the value "
                f"itself (for example 256, 2.5 or true), not an expression.")
    return values, errors


def knob_values(header: str, knobs: list[Knob]) -> tuple[dict, dict, list[str]]:
    """(feature values by name, host values by name, errors) from a header.

    Every knob must be present exactly once with a legal value, and no other
    SR_/HOST_ macro may appear: the port reads only the macros the plan names,
    so an extra one is a mutation that changes nothing and a missing one does
    not compile."""
    values, errors = parse_header(header)
    by_macro = {k.macro: k for k in knobs}
    feature, host = {}, {}
    for macro in values:
        if macro not in by_macro:
            errors.append(f"{macro} is not a knob of this port; mutate values only")
    for k in knobs:
        if k.macro not in values:
            errors.append(f"{k.macro} is missing from the header")
            continue
        value = values[k.macro]
        problem = range_error(k, value)
        if problem:
            errors.append(f"{k.macro} = {problem} (range: {k.range})")
        (feature if k.origin == "feature" else host)[k.name] = value
    return feature, host, errors


def default_values(knobs: list[Knob]) -> tuple[dict, dict]:
    feature = {k.name: k.default for k in knobs if k.origin == "feature"}
    host = {k.name: k.default for k in knobs if k.origin == "host"}
    return feature, host


# ------------------------------------------------------------------ storage


def feature_storage(spec: dict, values: dict) -> dict:
    """Bits per spec `state[]` entry at these parameter values.

    An entry without a `size_formula` costs its declared `size_bits` whatever
    the knobs say. That is the right reading for a structure no parameter
    sizes, and the wrong one for a structure a parameter does size, which is
    why spec_checks warns about a storage-bearing parameter no formula reads."""
    out = {}
    for s in (spec or {}).get("state") or []:
        formula = s.get("size_formula")
        out[f"feature:{s.get('name')}"] = (
            evaluate(formula, values) if formula else s.get("size_bits") or 0)
    return out


def host_storage(port_plan: dict | None, values: dict) -> dict:
    """Bits per port-plan `host_storage.terms[]` entry at these host values."""
    out = {}
    for t in ((port_plan or {}).get("host_storage") or {}).get("terms") or []:
        out[f"host:{t.get('structure')}"] = evaluate(t.get("formula", "0"), values)
    return out


# State that exists only to carry a prediction to its update. The CBP2025
# kit's README: "The amount of state needed to checkpoint histories will NOT
# be counted towards the predictor budget", and the host's own checkpoint map
# (pred_time_histories) is not in its predictorsize(). A spec says so in its
# own words: one entry per in-flight branch, or indexed by one. Which hosts
# exempt it is theirs to say (a host adapter's BUDGET_EXEMPT); what it is,
# is read off the spec here.
_CHECKPOINT_RE = re.compile(
    r"\bper\s+in[\s-]?flight\s+branch\b|\bin[\s-]?flight\s+branch\s+(?:id|index)\b", re.I)
EXEMPT_PREFIX = "exempt:"


# The structural signal, which does not depend on wording: the entry's
# size_formula is multiplied by a count of predictions in flight. The 23:05
# draft wrote "metadata for each in-flight branch", indexed by "Branch ID /
# ROB index", which the wording pattern alone missed, and its 27,776 bits
# would have been charged.
_INFLIGHT_FACTOR_RE = re.compile(r"in_?flight", re.I)


def _formula_factors(formula: str) -> set[str]:
    """Identifiers a size_formula multiplies by, outside any log2(...)."""
    while True:
        stripped = re.sub(r"log2\s*\([^()]*\)", "0", formula)
        if stripped == formula:
            break
        formula = stripped
    return set(re.findall(r"[A-Za-z_]\w*", formula))


def is_checkpoint_state(entry: dict) -> bool:
    """Whether a spec `state[]` entry is per-in-flight-branch checkpoint state:
    its own words say one entry per in-flight branch, or its size is a count
    of in-flight predictions times something."""
    entry = entry or {}
    text = " ".join(str(entry.get(k, "")) for k in ("organization", "indexing"))
    if _CHECKPOINT_RE.search(text):
        return True
    return any(_INFLIGHT_FACTOR_RE.search(n)
               for n in _formula_factors(str(entry.get("size_formula") or "")))


def storage_bits(spec: dict, port_plan: dict | None, feature: dict, host: dict,
                 exempt: tuple = ()):
    """(total bits, breakdown) for one candidate: the feature's structures plus
    the host's, so shrinking a host structure is what pays for the feature.

    `exempt` names the kinds of state the host's budget does not count;
    "checkpoint" is the only kind so far. An exempt structure stays in the
    breakdown under EXEMPT_PREFIX, so a report still shows its size, and is
    left out of the total. Before this, run 20260924_181851 charged sR 16,640
    bits of in-flight state the kit's rules exempt, which alone put every
    candidate 18,403 bits over the iso-64KiB allowance with sR at its minimum."""
    breakdown = {**feature_storage(spec, feature), **host_storage(port_plan, host)}
    if "checkpoint" in exempt:
        for entry in (spec or {}).get("state") or []:
            key = f"feature:{entry.get('name')}"
            if key in breakdown and is_checkpoint_state(entry):
                breakdown[EXEMPT_PREFIX + key] = breakdown.pop(key)
    total = sum(v for k, v in breakdown.items() if not k.startswith(EXEMPT_PREFIX))
    return total, breakdown


# A static metric is f(spec, port_plan, feature_values, host_values, exempt)
# -> (value, breakdown). Add new pre-build metrics here.
STATIC_METRICS = {
    "storage_bits": storage_bits,
}


# ------------------------------------------------------------------ the set

_COMPARE = {
    "<=": operator.le, "<": operator.lt, ">=": operator.ge, ">": operator.gt,
    "==": operator.eq,
}


@dataclass(frozen=True)
class Constraint:
    metric: str
    comparison: str
    allowance: float
    name: str = ""
    # Kinds of state the host's budget does not count (see storage_bits).
    exempt: tuple = ()

    @property
    def phase(self) -> str:
        return "static" if self.metric in STATIC_METRICS else "measured"

    def holds(self, value) -> bool:
        return value is not None and _COMPARE[self.comparison](value, self.allowance)

    def describe(self) -> str:
        label = f" ({self.name})" if self.name else ""
        uncounted = f", {' and '.join(self.exempt)} state not counted" if self.exempt else ""
        return f"{self.metric} {self.comparison} {self.allowance:g}{label}{uncounted}"

    def as_dict(self) -> dict:
        return {"metric": self.metric, "comparison": self.comparison,
                "allowance": self.allowance, "name": self.name, "phase": self.phase,
                "exempt": list(self.exempt)}


def storage_constraint(track: str, allowance_bits: int, exempt: tuple = ()) -> Constraint:
    return Constraint("storage_bits", "<=", allowance_bits, track, tuple(exempt))


@dataclass
class CandidateReport:
    ok: bool
    errors: list = field(default_factory=list)       # malformed or out-of-range values
    violations: list = field(default_factory=list)   # constraints that do not hold
    metrics: dict = field(default_factory=dict)
    breakdown: dict = field(default_factory=dict)
    feature: dict = field(default_factory=dict)
    host: dict = field(default_factory=dict)

    def message(self) -> str:
        lines = []
        if self.errors:
            lines.append("The header is not a legal candidate:")
            lines += [f"  - {e}" for e in self.errors]
        if self.violations:
            lines.append("The candidate breaks a constraint, so it was not built:")
            lines += [f"  - {v}" for v in self.violations]
        if self.breakdown:
            lines.append("Accounted storage by structure, in bits:")
            lines += [f"  {k}: {v:g}" for k, v in
                      sorted(self.breakdown.items(), key=lambda kv: -kv[1])]
        return "\n".join(lines)


def check_static(header: str, spec: dict, port_plan: dict | None,
                 constraints: list[Constraint]) -> CandidateReport:
    """Everything decidable before the build: legal values, then every static
    constraint. A candidate that fails here costs no build and no trace."""
    knobs = all_knobs(spec, port_plan)
    feature, host, errors = knob_values(header, knobs)
    report = CandidateReport(ok=False, errors=errors, feature=feature, host=host)
    if errors:
        return report
    for c in constraints:
        if c.phase != "static":
            continue
        try:
            value, breakdown = STATIC_METRICS[c.metric](spec, port_plan, feature, host,
                                                        exempt=c.exempt)
        except FormulaError as e:
            report.errors.append(f"{c.metric} could not be computed: {e}")
            continue
        report.metrics[c.metric] = value
        report.breakdown.update(breakdown)
        if not c.holds(value):
            report.violations.append(
                f"{c.metric} = {value:g} breaks {c.describe()} by "
                f"{abs(value - c.allowance):g}")
    report.ok = not report.errors and not report.violations
    return report


def check_measured(aggregate: dict, constraints: list[Constraint]) -> list[str]:
    """Violations among the measured constraints, from a screening aggregate."""
    out = []
    for c in constraints:
        if c.phase != "measured":
            continue
        value = (aggregate or {}).get(c.metric)
        if not c.holds(value):
            out.append(f"{c.metric} = {value} breaks {c.describe()}")
    return out


# ------------------------------------------------------------------ preflight


def is_pinned(knob: Knob) -> bool:
    """Does `knob`'s range admit exactly one legal value?

    A structural constant is not a broken knob. sR's register file is 65
    entries and its figure draws eight banks, so `num_logical_registers` has
    range `[65, 65]` and `num_banks` has `[8, 8]`, and both are honest. The
    alternative -- moving them out of `parameters` -- would leave three
    `size_formula` strings referencing a name nothing declares.

    Declaring them tells the integrator both the value *and* that it is not
    free, which is more than burying either in prose. So stage 4's preflight
    reports them as `pinned` and does not warn: there is no second value to
    build, and nothing is wrong. `_check_pinned_defaults` in `spec_checks`
    owns the other half, that the default is the value the range pins.

    Distinguished from the other reasons `alternate_value` returns None --
    an unparsable range, a non-numeric default -- which stay warnings,
    because those are knobs the DSE cannot search *and* nobody declared so.
    """
    from spec_checks import parse_range

    if knob.type == "bool":
        return False  # a flag always has a second value
    parsed = parse_range(knob.range)
    if parsed is None:
        return False
    if parsed[0] == "choices":
        return len(parsed[1]) == 1
    _, lo, hi, _mods = parsed
    return lo == hi


def alternate_value(knob: Knob):
    """A second legal value for `knob`, preferring the smaller direction.

    Used by stage 4's preflight to prove that a knob reaches the build: the
    header is rebuilt with this one value changed, and a binary identical to
    the default build means the knob is wired to nothing. Smaller first,
    because shrinking is what a tight budget explores."""
    from spec_checks import parse_range

    d = knob.default
    if knob.type == "bool":
        return not d
    parsed = parse_range(knob.range)
    if parsed and parsed[0] == "choices":
        n = len(parsed[1])
        return None if n < 2 else (1 if knob.type == "enum" else parsed[1][1])
    if not parsed or isinstance(d, bool) or not isinstance(d, (int, float)):
        return None
    _, lo, hi, mods = parsed
    if "pow2" in mods:
        candidates = [d // 2 if isinstance(d, int) else d / 2, d * 2]
    elif knob.type == "int":
        candidates = [d - 1, d + 1]
    else:
        step = (hi - lo) / 4 or 1.0
        candidates = [d - step, d + step]
    for c in candidates:
        if isinstance(d, int) and not isinstance(c, int):
            c = int(c)
        if c != d and range_error(knob, c) is None:
            return c
    return None
