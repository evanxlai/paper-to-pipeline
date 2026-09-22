"""Deterministic feature-spec checks (stage-1 analogue of gate.py).

Same philosophy as the verify gate: no LLM opinion decides whether a spec is
self-consistent. Everything here is plain code reading the spec's own
declarations, so the rules generalize to whatever paper the loop adopts next --
nothing below is keyed to a feature, a predictor, or a particular table.

These run BEFORE the reviewer agents, not beside them. Anything code can settle
(arithmetic closure, a default that does not fit its own field, a knob nothing
references) is settled here for free, and the reviewers spend their tokens only
on what needs judgement.

Severities:
  error  the spec contradicts itself or its budget. Always worth a patch.
  warn   a heuristic fired. Feeds the reviewer prompt as "verify or refute",
         never a hard rejection -- the parsers here are deliberately loose so
         that they generalize, and loose parsers misfire.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Finding:
    """One deterministic observation, anchored to an RFC 6901 JSON Pointer."""

    pointer: str
    code: str
    severity: str  # "error" | "warn"
    message: str

    def as_dict(self) -> dict:
        return {
            "pointer": self.pointer,
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }


# --------------------------------------------------------------- tokenizing

# Spelled-out numerals appear constantly in organization prose ("three tables
# of 8 entries"). Without this mapping the factor check below flags every
# spelled number as unsupported, which buries the real findings.
NUM_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
}

# Tokens too common to identify anything. Used when matching a parameter to a
# field, and when matching a state entry to the algorithms that touch it: a
# shared "table" or "counter" means nothing, a shared "decay" or "wt0" does.
GENERIC_TOKENS = {
    "a", "an", "and", "bit", "bits", "count", "counter", "ctr", "data",
    "entries", "entry", "field", "fields", "for", "in", "num", "of", "or",
    "per", "predictor", "reg", "regs", "register", "registers", "size",
    "state", "structure", "table", "tables", "the", "to", "total", "value",
    "values", "weight", "weights", "width",
}


def stem(token: str) -> str:
    """Crude suffix strip so 'tracking' and 'tracker' collide.

    Specs routinely name a structure one way ("Register tracking table") and
    index it another ("tracker[rd]"). Exact matching misses that and drops the
    state entry into the orphan unit. Over-stemming only costs a redundant
    review, so the trade favours recall.
    """
    t = re.sub(r"[^a-z0-9]", "", token.lower())
    for suffix in ("ings", "ing", "ers", "er", "es", "s"):
        if t.endswith(suffix) and len(t) - len(suffix) >= 3:
            return t[: -len(suffix)]
    return t


def tokens(text: str, drop_generic: bool = True) -> set[str]:
    """Stemmed identifier tokens from a name or a blob of prose."""
    raw = re.findall(r"[A-Za-z][A-Za-z0-9_]*|\d+", text or "")
    out, kept_all = set(), set()
    for tok in raw:
        # Split snake_case and camelCase so decay_ctr yields {decay, ctr}.
        for part in re.split(r"_|(?<=[a-z0-9])(?=[A-Z])", tok):
            if not part:
                continue
            s = stem(part)
            if len(s) < 2:
                continue
            kept_all.add(s)
            if drop_generic and s in GENERIC_TOKENS:
                continue
            out.add(s)
    # A name built entirely from generic words ("Prediction Table") would
    # otherwise tokenize to nothing and match no algorithm, silently landing in
    # the orphan unit. Fall back to the unfiltered set rather than vanishing.
    return out or kept_all


def numerals(text: str) -> set[int]:
    """Every integer in a string, including spelled-out and 2^n forms."""
    out: set[int] = set()
    for m in re.finditer(r"\b(\d+)\s*\^\s*(\d+)\b", text or ""):
        base, exp = int(m.group(1)), int(m.group(2))
        if exp <= 64:
            out.add(base ** exp)
    for m in re.finditer(r"\b\d+\b", text or ""):
        out.add(int(m.group()))
    for word, val in NUM_WORDS.items():
        if re.search(rf"\b{word}\b", (text or "").lower()):
            out.add(val)
    return out


# ------------------------------------------------------------ range parsing


def parse_range(spec_range: str):
    """Parse the range forms the schema itself documents.

    Returns ("interval", lo, hi, modifiers) | ("choices", [...]) | None.
    Returning None is a finding, not an exception: a range nobody can parse is
    a range the DSE cannot search.
    """
    if not isinstance(spec_range, str):
        return None
    text = spec_range.strip()
    m = re.match(r"^choices\s*:\s*(.+)$", text, re.I)
    if m:
        return ("choices", [c.strip() for c in m.group(1).split("|") if c.strip()])
    m = re.match(
        r"^[\[(]\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*[\])]\s*(.*)$", text
    )
    if m:
        try:
            lo, hi = float(m.group(1)), float(m.group(2))
        except ValueError:
            return None
        return ("interval", lo, hi, m.group(3).strip().lower())
    return None


def _is_pow2(n) -> bool:
    return isinstance(n, int) and n > 0 and n & (n - 1) == 0


# ------------------------------------------------------------- field widths


# Field widths are written four different ways across the literature, and the
# representability check is worthless on a spec whose notation it cannot read.
# Supporting only one form does not fail loudly -- it silently finds nothing,
# which is the worse failure, so all four are parsed.
_FIELD_PATTERNS = (
    # valid (1), payload (14 bits), decay_ctr (8-bit)
    re.compile(r"([A-Za-z][A-Za-z0-9_ /-]*?)\s*\(\s*(\d+)\s*(?:-?\s*bits?)?\s*\)"),
    # decay_ctr (8-bit down-counter initialized to 256)
    #   -- the same form, but with the field's prose description trailing
    #   inside the parens. An explicit bit marker is REQUIRED here: without it
    #   `banks (4 arrays of 12)` would be read as a 4-bit field. Omitting this
    #   form does not fail loudly, it just silently finds no width, and every
    #   representability check downstream then passes by default.
    re.compile(r"([A-Za-z][A-Za-z0-9_ /-]*?)\s*\(\s*(\d+)\s*-?\s*bits?\b[^)]*\)"),
    # rrpv: 2 bits        age = 12 bits
    re.compile(r"([A-Za-z][A-Za-z0-9_ /-]*?)\s*[:=]\s*(\d+)\s*-?\s*bits?\b"),
    # 16-bit tag, 12-bit stride
    re.compile(r"\b(\d+)\s*-?\s*bits?\s+([A-Za-z][A-Za-z0-9_]*)", re.I),
    # payload [13:0]
    re.compile(r"([A-Za-z][A-Za-z0-9_ /-]*?)\s*\[\s*(\d+)\s*:\s*(\d+)\s*\]"),
)


def field_widths(entry_format: str) -> dict[str, int]:
    """Pull `name (N)`, `name: N bits`, `N-bit name` and `name [hi:lo]` widths.

    Deliberately refuses fractional widths like `hysteresis (1/4)`: every
    pattern requires the digits to terminate the width, so shared-bit notations
    are skipped rather than misread.
    """
    text = entry_format or ""
    out: dict[str, int] = {}

    def put(name: str, bits: int) -> None:
        name = re.sub(r"^(and|or|with|plus|the)\s+", "", name.strip().lower())
        if name and name not in out:
            out[name] = bits

    for m in _FIELD_PATTERNS[0].finditer(text):
        put(m.group(1), int(m.group(2)))
    for m in _FIELD_PATTERNS[1].finditer(text):
        put(m.group(1), int(m.group(2)))
    for m in _FIELD_PATTERNS[2].finditer(text):
        put(m.group(1), int(m.group(2)))
    for m in _FIELD_PATTERNS[3].finditer(text):
        put(m.group(2), int(m.group(1)))
    for m in _FIELD_PATTERNS[4].finditer(text):
        hi, lo = int(m.group(2)), int(m.group(3))
        if hi >= lo:
            put(m.group(1), hi - lo + 1)
    return out


def _shares_identifying_token(a: str, b: str) -> bool:
    ta, tb = tokens(a), tokens(b)
    return bool(ta & tb)


def _contains_name(a: str, b: str) -> bool:
    """Are these two spellings of one name, rather than neighbours?

    Subset, not intersection: `WT0_bank` is the declared `WT0` under a local
    alias, while `recorded_digest` and `selected_reg_digest` merely both end
    in "digest" and denote different things.
    """
    ta, tb = tokens(a), tokens(b)
    return bool(ta and tb and (ta <= tb or tb <= ta))


# ------------------------------------------------------------------ checks


def _check_storage(spec: dict, budget_bits: int | None) -> list[Finding]:
    out: list[Finding] = []
    state = spec.get("state") or []
    acct = spec.get("resource_accounting") or {}
    total = acct.get("total_storage_bits")

    sizes = [s.get("size_bits") for s in state]
    if state and all(isinstance(v, int) for v in sizes) and isinstance(total, int):
        summed = sum(sizes)
        if summed != total:
            out.append(Finding(
                "/resource_accounting/total_storage_bits",
                "storage_sum",
                "error",
                f"state sizes sum to {summed} bits but total_storage_bits is "
                f"{total} (difference {total - summed}). Either a state entry "
                f"is missing or the total is wrong.",
            ))

    if isinstance(total, int) and budget_bits is not None and total > budget_bits:
        out.append(Finding(
            "/resource_accounting/total_storage_bits",
            "budget_fit",
            "error",
            f"total_storage_bits {total} exceeds the budget track "
            f"({budget_bits} bits).",
        ))
    return out


def _check_parameters(spec: dict) -> list[Finding]:
    out: list[Finding] = []
    params = spec.get("parameters") or []
    state = spec.get("state") or []

    # Every declared field width in the spec, with the state entry it came from.
    widths: list[tuple[str, int, int]] = []  # (field_name, bits, state_index)
    for si, s in enumerate(state):
        for fname, bits in field_widths(s.get("entry_format", "")).items():
            widths.append((fname, bits, si))

    for pi, p in enumerate(params):
        base = f"/parameters/{pi}"
        default, rng = p.get("default"), p.get("range")

        parsed = parse_range(rng)
        if parsed is None:
            out.append(Finding(
                f"{base}/range", "range_unparsed", "warn",
                f"range {rng!r} does not match a documented form "
                f"('[lo, hi]', '[lo, hi] pow2', 'choices: a|b|c'); the DSE "
                f"cannot enumerate it.",
            ))
        elif parsed[0] == "choices":
            if str(default) not in parsed[1]:
                out.append(Finding(
                    f"{base}/default", "param_range", "error",
                    f"default {default!r} is not among choices {parsed[1]}.",
                ))
        else:
            _, lo, hi, mods = parsed
            if isinstance(default, bool) or not isinstance(default, (int, float)):
                out.append(Finding(
                    f"{base}/default", "param_range", "error",
                    f"default {default!r} is not numeric but range {rng!r} is "
                    f"an interval.",
                ))
            else:
                if not (lo <= default <= hi):
                    out.append(Finding(
                        f"{base}/default", "param_range", "error",
                        f"default {default} lies outside range [{lo}, {hi}].",
                    ))
                if "pow2" in mods and not _is_pow2(default):
                    out.append(Finding(
                        f"{base}/default", "param_range", "error",
                        f"range declares pow2 but default {default} is not a "
                        f"power of two.",
                    ))

        # Representability: a knob whose value lives in a declared field must
        # fit in that field. This is the check that catches a 256-cycle timeout
        # stored in an 8-bit counter, which no amount of prose review finds.
        if isinstance(default, int) and not isinstance(default, bool):
            for fname, bits, si in widths:
                if not _shares_identifying_token(p.get("name", ""), fname):
                    continue
                # A B-bit field holds 2^B distinct states, so it can COUNT
                # 2^B steps (N-1 down to 0) even though the largest value it
                # can STORE is 2^B - 1. A duration parameter is the span, not
                # the stored value, so rejecting span == 2^B drives reviewers
                # to "fix" 256 to 255 -- which then breaks a pow2 range and
                # leaves the round oscillating between two errors. A literal
                # actually assigned into the field is still bounded by
                # 2^B - 1; that is _check_literal_widths' job, not this one.
                if default > (1 << bits):
                    out.append(Finding(
                        f"{base}/default", "unrepresentable_default", "error",
                        f"default {default} does not fit the {bits}-bit field "
                        f"'{fname}' declared in "
                        f"/state/{si}/entry_format (at most {1 << bits} steps, "
                        f"max stored value {(1 << bits) - 1}). "
                        f"Either widen the field or lower the default.",
                    ))
                break

        # A knob no pseudocode reads cannot be explored by the DSE -- unless
        # the review stage minted it to stand in for an unresolved ambiguity,
        # which is exactly a knob the prose has no name for yet.
        if str(p.get("origin", "")).startswith("review:"):
            continue
        pname_tokens = tokens(p.get("name", ""))
        body = " ".join(
            f"{a.get('pseudocode','')} {a.get('notes','')}"
            for a in (spec.get("algorithms") or [])
        )
        if pname_tokens and not (pname_tokens & tokens(body)):
            out.append(Finding(
                f"{base}/name", "unreferenced_param", "warn",
                f"parameter '{p.get('name')}' appears in no algorithm "
                f"pseudocode; the DSE would tune a knob nothing reads.",
            ))
    return out


def _best_state_match(label: str, state: list) -> int | None:
    """Index of the state entry a breakdown label most likely refers to."""
    lab = tokens(label)
    if not lab:
        return None

    def score_exact(name: str) -> int:
        return len(lab & tokens(name))

    def score_prefix(name: str) -> int:
        st = tokens(name)
        return sum(
            1 for a in lab for b in st
            if len(a) >= 2 and len(b) >= 2 and (b.startswith(a) or a.startswith(b))
        )

    for scorer in (score_exact, score_prefix):
        best_i, best = None, 0
        for si, s in enumerate(state):
            sc = scorer(s.get("name", ""))
            if sc > best:
                best_i, best = si, sc
        if best_i is not None:
            return best_i
    return None


def _check_breakdown(spec: dict) -> list[Finding]:
    """Validate storage_breakdown factor-by-factor, not just by product.

    A breakdown can reach the right total through the wrong factors -- e.g.
    naming a bank count where the table's entry count belongs, when the two
    happen to be equal. Comparing only the product waves that through, so this
    check requires each factor to be a number the state entry actually
    declares.
    """
    out: list[Finding] = []
    acct = spec.get("resource_accounting") or {}
    breakdown = acct.get("storage_breakdown")
    state = spec.get("state") or []
    if not isinstance(breakdown, str) or not state:
        return out

    # Split on separators that are not inside parentheses.
    segments = re.split(r"[;,](?![^()]*\))", breakdown)
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        product = re.search(r"\(([^)]*[*x×][^)]*)\)", seg)
        claimed = re.search(r"(\d+)\s*bits?\b", seg)
        if not product or not claimed:
            continue

        factors = [int(n) for n in re.findall(r"\b\d+\b", product.group(1))]
        if not factors:
            continue

        # Attach the segment to the state entry whose name it overlaps most.
        # Breakdown labels are routinely abbreviations of the state name
        # ("UT:" for "Usefulness Weight Tables (UT0, UT1, UT2)"), so fall back
        # to prefix matching when no token matches outright.
        label = seg.split("(")[0]
        best_i = _best_state_match(label, state)
        if best_i is None:
            out.append(Finding(
                "/resource_accounting/storage_breakdown", "breakdown_unmatched",
                "warn",
                f"breakdown segment {seg!r} does not name any state entry, so "
                f"its factors cannot be checked.",
            ))
            continue

        entry = state[best_i]
        declared = numerals(entry.get("organization", "")) | numerals(
            entry.get("entry_format", "")
        )
        # Breakdowns almost always multiply by the total entry width, which is
        # declared only implicitly as the sum of the field widths.
        widths = field_widths(entry.get("entry_format", ""))
        if widths:
            declared.add(sum(widths.values()))
        prod = 1
        for f in factors:
            prod *= f
        if prod != int(claimed.group(1)):
            out.append(Finding(
                "/resource_accounting/storage_breakdown", "breakdown_product",
                "warn",
                f"segment {seg!r}: factors multiply to {prod} but the segment "
                f"claims {claimed.group(1)} bits.",
            ))
        unsupported = [f for f in factors if f not in declared and f != 1]
        if unsupported:
            out.append(Finding(
                f"/state/{best_i}/organization", "breakdown_factors", "warn",
                f"breakdown segment {seg!r} uses factor(s) {unsupported} that "
                f"'{entry.get('name')}' never declares in its organization or "
                f"entry_format. The product may be right for the wrong reason.",
            ))
    return out


# Names a coding agent can be expected to supply itself. Anything outside this
# set that a pseudocode body calls is a hole in the spec, not a primitive.
_PRIMITIVE_CALLS = {
    "abs", "all", "any", "ceil", "clz", "ctz", "enumerate", "filter", "float",
    "floor", "int", "len", "log2", "map", "max", "min", "pow", "popcount",
    "print", "rand", "randint", "random", "random_choice", "range", "round",
    "saturate", "set", "sign", "sorted", "sum", "zip",
    "increment_sat", "decrement_sat", "leading_count", "trailing_count",
    "leading_zeros", "trailing_zeros",
}
_PRIMITIVE_PREFIXES = ("is_", "hash", "get_", "read_", "to_", "as_")

# An allowlist of primitives can only ever contain names someone has already
# seen, so it silently mis-scores whatever the next paper happens to call
# things. The severity split below does the real work instead: a call whose
# name carries a *policy verb* would hide a learning, allocation or replacement
# rule, and that is the omission worth a reviewer's attention regardless of
# domain. Everything else is recorded at info severity -- visible, but it does
# not count against the round.
_POLICY_VERBS = (
    "update", "train", "learn", "allocate", "alloc", "insert", "evict",
    "replace", "promote", "demote", "age", "adjust", "recalibrate", "retire",
    "commit", "reset", "init", "select", "victim", "throttle", "decay",
)


def _is_policy_call(name: str) -> bool:
    low = name.lower()
    return any(v in low for v in _POLICY_VERBS)


def _check_algorithms(spec: dict) -> list[Finding]:
    out: list[Finding] = []
    algos = spec.get("algorithms") or []
    defined = {stem(a.get("name", "")) for a in algos}
    # A pseudocode block routinely declares its own small helpers above the
    # entry point (`function sat_update_6bit(ctr, step):`). Those are defined
    # by the spec, just not as algorithms of their own, and reporting them as
    # holes trains a reader to ignore the check.
    for a in algos:
        for m in re.finditer(r"^\s*(?:function|def)\s+([A-Za-z_][A-Za-z0-9_]*)",
                             a.get("pseudocode", "") or "", re.M):
            defined.add(stem(m.group(1)))

    for ai, a in enumerate(algos):
        body = a.get("pseudocode", "") or ""
        # `function foo(...)` / `def foo(...)` declares foo; it does not call
        # it. Counting the declaration as a call reports every algorithm whose
        # function name differs from its spec name as an undefined helper.
        callable_text = re.sub(r"^\s*(?:function|def)\s+[A-Za-z_][A-Za-z0-9_]*",
                               "", body, flags=re.M)
        called = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", callable_text))
        for name in sorted(called):
            low = name.lower()
            if low in _PRIMITIVE_CALLS or low.startswith(_PRIMITIVE_PREFIXES):
                continue
            if stem(name) in defined:
                continue
            policy = _is_policy_call(name)
            out.append(Finding(
                f"/algorithms/{ai}/pseudocode",
                "undefined_policy_call" if policy else "undefined_helper",
                "warn" if policy else "info",
                f"pseudocode calls '{name}(...)' but no algorithm defines it."
                + (" The name suggests it holds a learning, allocation or "
                   "replacement rule, so an implementer would have to invent "
                   "the policy itself." if policy else
                   " It may be a primitive the host supplies; confirm or "
                   "define it."),
            ))

    # State nothing touches is either dead or unimplementable.
    all_algo_text = " ".join(
        f"{a.get('trigger','')} {a.get('pseudocode','')} {a.get('notes','')}"
        for a in algos
    )
    algo_tokens = tokens(all_algo_text)
    for si, s in enumerate(spec.get("state") or []):
        st = tokens(s.get("name", ""))
        if st and not (st & algo_tokens):
            out.append(Finding(
                f"/state/{si}/name", "orphan_state", "warn",
                f"state entry '{s.get('name')}' is referenced by no algorithm; "
                f"it is either dead storage or an operation is missing.",
            ))
    return out


_HEDGE_RE = re.compile(
    r"\b(correct(ly)?|appropriate(ly)?|proper(ly)?|as expected|reasonable|"
    r"sensible|valid output|expected value)\b",
    re.I,
)


def _check_unit_tests(spec: dict) -> list[Finding]:
    out: list[Finding] = []
    for ti, t in enumerate(spec.get("unit_tests") or []):
        expect = t.get("expect", "") or ""
        concrete = bool(re.search(r"\d", expect)) or bool(
            re.search(r"[=<>]=?|\bequals\b", expect)
        )
        if _HEDGE_RE.search(expect):
            out.append(Finding(
                f"/unit_tests/{ti}/expect", "vacuous_test", "warn",
                f"expectation leans on a hedge word ('{_HEDGE_RE.search(expect).group()}') "
                f"instead of naming the value. The gate cannot fail this test "
                f"closed; state the expected result explicitly.",
            ))
        elif not concrete:
            out.append(Finding(
                f"/unit_tests/{ti}/expect", "vacuous_test", "warn",
                "expectation contains no value or comparison, so the gate "
                "cannot decide whether it passed.",
            ))
    return out



# ------------------------------------------ bare identifiers across algorithms

# `_check_context_writes` reads dotted fields (`inst.rob_idx`). The other half
# of the same failure is a bare name: a table an algorithm subscripts that
# nothing fills, or a scalar it reads that only some *other* algorithm ever
# computed. Both are invisible to a dotted-name scan, and both reached the sR
# spec at once -- `update` read `recorded_digest[bank][chosen_r]`, which no
# algorithm writes, and `w0 + w1 + w2`, which are `predict`'s loop locals and
# hold whatever its last iteration left behind.
_SIGNATURE_RE = re.compile(
    r"^\s*(?:function|def|on|procedure)\s+[A-Za-z_]\w*\s*\(([^)]*)\)"
)
_ASSIGN_TARGET_RE = re.compile(
    r"^\s*([A-Za-z_]\w*)\s*((?:\[[^\[\]]*\])*)\s*(?:[-+*/|&^]|<<|>>)?=(?!=)"
)
# Pseudocode dialects vary: `for r in`, `for each r in`, `foreach r in`,
# and set-builder or argmax binders all introduce a name the body then uses.
_FOR_VAR_RE = re.compile(
    r"^\s*for(?:each)?\s+(?:each\s+|all\s+)?([A-Za-z_]\w*)\b"
)
_BINDER_RE = re.compile(r"[{\[]\s*([A-Za-z_]\w*)\s*[|]|\b([A-Za-z_]\w*)\s+in\s")
_SUBSCRIPT_READ_RE = re.compile(r"(?<![.\w])([A-Za-z_]\w*)\s*\[")
# An operand of an operator is being used as a value, which is what separates
# a variable from the English that pseudocode is half made of. Without this,
# "list of logical registers assigned to bank" reports six free identifiers.
_OPERAND_RE = re.compile(
    r"(?<![.\w])([A-Za-z_]\w*)\s*(?:[-+*/%&|^]|<<|>>|[<>]=?|[=!]=)"
    r"|(?:[-+*/%&|^]|<<|>>|[<>]=?|[=!]=)\s*(?<![.\w])([A-Za-z_]\w*)"
)
_CALLEE_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
# Control flow and type names are not dataflow. `return x` puts `return`
# next to an operand; `x: uint64` puts a type where a value would be.
_PSEUDOCODE_KEYWORDS = frozenset({
    "and", "assert", "bool", "break", "byte", "case", "const", "continue",
    "def", "do", "elif", "else", "end", "endif", "false", "float", "for",
    "foreach", "function", "if", "in", "int", "is", "let", "match", "new",
    "none", "not", "null", "on", "or", "pass", "procedure", "return",
    "signed", "switch", "then", "true", "uint", "unsigned", "var", "void",
    "while", "with", "xor", "yield",
    # Sentinels an argmax or a saturating bound is seeded with. They are
    # literals of the pseudocode dialect, not state some other stage fills.
    "infinity", "inf", "nan", "maxint", "minint", "int_max", "int_min",
    "max_int", "min_int", "undefined",
})


def _is_keyword(name: str) -> bool:
    low = name.lower()
    return low in _PSEUDOCODE_KEYWORDS or bool(
        re.fullmatch(r"u?int\d*|float\d*|bits?\d*|uint\d+_t", low)
    )


def _statements(body: str):
    """Comment-stripped statements. `a = f(x); b = g(y)` is two, not one."""
    for raw in (body or "").splitlines():
        line = re.sub(r"//.*$", "", raw)
        for part in line.split(";"):
            if part.strip():
                yield part


def _name_flow(body: str) -> dict[str, set[str]]:
    """Which bare names this body binds, and how it reads the rest.

    'keyed' vs 'scalar' writes matter downstream: `selected[bank] = x` is a
    deliberate store into a structure another stage can read, while `w0 = ...`
    inside a loop is a local whose value has no meaning outside this body.
    """
    out = {"keyed": set(), "scalar": set(), "subscripted": set(),
           "operand": set(), "callee": set()}
    for raw in (body or "").splitlines():
        if m := _SIGNATURE_RE.match(raw):
            for part in m.group(1).split(","):
                name = part.split(":")[0].strip()
                if re.fullmatch(r"[A-Za-z_]\w*", name):
                    out["scalar"].add(name)
    out["callee"].update(_CALLEE_RE.findall(body or ""))
    for st in _statements(body):
        # A signature contributes its parameters, above, and nothing else:
        # its type annotations (`val: uint64`) and return arrow (`-> int`)
        # otherwise read as free variables being operated on.
        if _SIGNATURE_RE.match(st):
            continue
        rhs = st
        if m := _ASSIGN_TARGET_RE.match(st):
            out["keyed" if m.group(2) else "scalar"].add(m.group(1))
            rhs = st.split("=", 1)[1]
        if m := _FOR_VAR_RE.match(st):
            out["scalar"].add(m.group(1))
        for a, b in _BINDER_RE.findall(st):
            out["scalar"].add(a or b)
        out["subscripted"].update(_SUBSCRIPT_READ_RE.findall(rhs))
        for a, b in _OPERAND_RE.findall(rhs):
            out["operand"].add(a or b)
    out["scalar"].discard("")
    out["operand"].discard("")
    return out


def _check_carried_state(spec: dict) -> list[Finding]:
    """Bare names an algorithm reads that no algorithm can have filled."""
    out: list[Finding] = []
    algos = spec.get("algorithms") or []
    flows = [_name_flow(a.get("pseudocode", "")) for a in algos]

    # Names the spec declares elsewhere are furniture, not dataflow: state
    # entries and the sub-tables named only in their prose, tunable
    # parameters, and the algorithms themselves.
    declared: set[str] = {str(p.get("name", "")) for p in (spec.get("parameters") or [])}
    declared |= {str(a.get("name", "")) for a in algos}
    structures: set[str] = set()
    for entry in spec.get("state") or []:
        structures.add(str(entry.get("name", "")))
        blob = " ".join(str(entry.get(k, "")) for k in
                        ("organization", "entry_format", "indexing"))
        for word in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", blob):
            # Sub-tables (UT0, way_1) are named only in a parent entry's
            # prose. Ordinary English from the same prose is not a
            # declaration, and treating it as one would suppress real
            # findings: "12-bit digest" would excuse a stray `digest_cache`.
            if re.search(r"[0-9_]", word) or word.isupper():
                structures.add(word)
    declared |= structures

    writers: dict[str, dict[str, set[str]]] = {}
    for ai, a in enumerate(algos):
        for kind in ("keyed", "scalar"):
            for name in flows[ai][kind]:
                writers.setdefault(name, {"keyed": set(), "scalar": set()})[kind] \
                    .add(a.get("name", "?"))

    for ai, a in enumerate(algos):
        me = a.get("name", "?")
        flow = flows[ai]
        bound = flow["keyed"] | flow["scalar"] | flow["callee"]
        # The schema gives each algorithm declared inputs and outputs. A name
        # arriving that way has a stated producer even though no pseudocode
        # line assigns it.
        for field in ("inputs", "outputs"):
            val = a.get(field)
            for item in (val if isinstance(val, list) else [val]):
                bound.update(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b",
                                        str(item or "")))
        for name in sorted(flow["subscripted"] | flow["operand"]):
            if name in bound or name in declared:
                continue
            if _is_keyword(name):
                continue
            # A structure the spec declares under a different spelling --
            # `RegisterDigestTable` for "Register Digest Table" -- is
            # declared, not missing. One shared token is too weak a test:
            # `recorded_digest` and `selected_reg_digest` share "digest" and
            # are different things, so require one name's tokens to contain
            # the other's outright.
            if any(_contains_name(name, d) for d in structures):
                continue
            w = writers.get(name, {"keyed": set(), "scalar": set()})
            elsewhere_keyed = w["keyed"] - {me}
            elsewhere_scalar = w["scalar"] - {me}
            if elsewhere_keyed:
                continue  # a real handshake: some stage stores it by key
            if elsewhere_scalar:
                out.append(Finding(
                    f"/algorithms/{ai}/pseudocode", "cross_algorithm_local",
                    "warn",
                    f"'{me}' reads '{name}', which is a plain local of "
                    f"{'/'.join(sorted(elsewhere_scalar))} and not state the "
                    f"spec declares. By the time '{me}' runs, that local holds "
                    f"whatever the last iteration of the other algorithm left "
                    f"in it, if anything. Either recompute it here or make it "
                    f"a declared, keyed carry.",
                ))
                continue
            out.append(Finding(
                f"/algorithms/{ai}/pseudocode", "unproduced_context", "warn",
                f"'{me}' reads '{name}', but no algorithm in the spec ever "
                f"writes it and no state entry declares it. The producing side "
                f"of that handshake is missing, so an implementer must invent "
                f"both what it holds and which stage fills it.",
            ))
    return out


def _costs_storage(parameter: dict) -> bool:
    """Does the spec say this parameter changes the storage total?"""
    impact = str(parameter.get("storage_impact") or "").strip().lower()
    return bool(impact) and not impact.startswith(("none", "no storage", "0 "))


def _check_size_formulas(spec: dict) -> list[Finding]:
    """Each `size_formula` is arithmetic over declared parameters and, at the
    defaults, equals the `size_bits` beside it.

    Accounting, not a budget: nothing here compares a size with an allowance.
    It exists because stage 4 re-derives every candidate's storage from these
    formulas, so a formula that disagrees with its own entry at the defaults
    would put every candidate's cost off by the same silent amount."""
    import constraints

    out: list[Finding] = []
    params = spec.get("parameters") or []
    defaults = {p.get("name"): p.get("default") for p in params}
    read: set[str] = set()
    for si, s in enumerate(spec.get("state") or []):
        formula = s.get("size_formula")
        if formula is None:
            continue
        at = f"/state/{si}/size_formula"
        try:
            names = constraints.names_in(formula)
        except constraints.FormulaError as e:
            out.append(Finding(at, "formula_invalid", "error", f"{formula!r} {e}."))
            continue
        read |= names
        unknown = sorted(n for n in names if n not in defaults)
        if unknown:
            out.append(Finding(
                at, "formula_unknown_name", "error",
                f"{formula!r} reads {', '.join(unknown)}, which no parameter declares. "
                f"A formula may read only parameters[].name.",
            ))
            continue
        try:
            value = constraints.evaluate(formula, defaults)
        except constraints.FormulaError as e:
            out.append(Finding(at, "formula_invalid", "error",
                               f"{formula!r} fails at the defaults: {e}."))
            continue
        declared = s.get("size_bits")
        if isinstance(declared, (int, float)) and abs(value - declared) >= 0.5:
            out.append(Finding(
                at, "formula_disagrees", "error",
                f"{formula!r} gives {value:g} bits at the defaults, but size_bits says "
                f"{declared}. Stage 4 costs every candidate with the formula, so one of "
                f"the two is wrong.",
            ))

    for pi, p in enumerate(params):
        if _costs_storage(p) and p.get("name") not in read:
            out.append(Finding(
                f"/parameters/{pi}", "storage_param_unaccounted", "warn",
                f"'{p.get('name')}' says it changes storage "
                f"({str(p.get('storage_impact'))[:80]!r}), but no state[].size_formula "
                f"reads it. Stage 4 would move this knob without its cost moving.",
            ))
    return out


def run_checks(spec: dict, budget_bits: int | None = None) -> list[Finding]:
    """All deterministic checks, in a stable order."""
    findings: list[Finding] = []
    findings += _check_storage(spec, budget_bits)
    findings += _check_size_formulas(spec)
    findings += _check_parameters(spec)
    findings += _check_breakdown(spec)
    findings += _check_algorithms(spec)
    findings += _check_unit_tests(spec)
    findings += _check_literal_widths(spec)
    findings += _check_index_consistency(spec)
    findings += _check_context_writes(spec)
    findings += _check_carried_state(spec)
    findings += _check_declared_bounds(spec)
    return findings


def severity_counts(findings: list[Finding]) -> dict[str, int]:
    out = {"error": 0, "warn": 0, "info": 0}
    for f in findings:
        out[f.severity] = out.get(f.severity, 0) + 1
    return out


def is_worse(before: list[Finding], after: list[Finding]) -> bool:
    """Did a review round make the spec less self-consistent?

    Errors dominate: a round may trade warnings for a fix, but it may never
    introduce a new contradiction. Info findings are excluded -- they exist to
    inform a reviewer, and letting a heuristic note roll back a round would put
    the loosest parser in charge of the tightest decision.
    """
    b, a = severity_counts(before), severity_counts(after)
    if a["error"] > b["error"]:
        return True
    return a["error"] == b["error"] and a["warn"] > b["warn"]


# ------------------------------------------------ pseudocode surface reading

# Pseudocode in a spec is prose-adjacent: it is never compiled, only read by an
# implementer, so the three checks below read it with regexes and indentation
# rather than a grammar. That is also why only the first is an `error` -- a
# literal that does not fit its own declared field is arithmetic, not opinion.
# The other two are heuristics, and `warn` is the severity that asks a reviewer
# to verify or refute rather than forcing a patch.

# `name = 123`, rejecting ==, !=, <=, >= and += by requiring an identifier
# immediately left of a lone '='. A subscripted target (`t[i] = 3`) is
# deliberately not matched: the width being checked belongs to a named field,
# and `t[i]` names an element, not a field.
_LITERAL_ASSIGN_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)\s*(\d+)\b")

# Block openers, and which of them make their body conditional. A `for`/`while`
# body runs whenever the loop runs, so only the if-family gates a write.
_BLOCK_RE = re.compile(r"^\s*(if|elif|else|for|while|function|def)\b")
_CONDITIONAL_KEYWORDS = {"if", "elif", "else"}

# An assignment of a bare constant (or a container of them) is an
# initialisation to a sentinel, not a real value. The distinction matters in
# _check_context_writes: initialising to a sentinel and then filling the slot
# only on some paths is exactly the shape that obliges the reader to test the
# sentinel before trusting it.
_SENTINEL_RHS_RE = re.compile(
    r"^(-?\d+|none|null|\[\s*\]|\[\s*-?\d+\s*\]\s*\*.*|\[\s*\[\s*\]\s*for\b.*"
    r"|\[\s*none\s*\]\s*\*.*)$",
    re.I,
)

# `obj.field`, with any trailing subscript dropped so that
# `ctx.bank_sum[b]` and `ctx.bank_sum` are one name.
_ATTR_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)")

# `name[idx]` / `name[i][j]`, capturing the whole subscript chain.
_SUBSCRIPT_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)((?:\s*\[[^\[\]]*\])+)")


def _walk_pseudocode(body: str):
    """Yield (stripped_line, under_conditional) for each non-blank line.

    Indentation is the only block structure pseudocode reliably carries, so
    that is what is tracked. A line is "under a conditional" when any enclosing
    block on the indent stack was opened by if/elif/else.
    """
    stack: list[tuple[int, bool]] = []
    for raw in (body or "").splitlines():
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip())
        while stack and indent <= stack[-1][0]:
            stack.pop()
        yield raw.strip(), any(cond for _, cond in stack)
        m = _BLOCK_RE.match(raw)
        if m:
            stack.append((indent, m.group(1) in _CONDITIONAL_KEYWORDS))


def _locally_bound(body: str) -> set[str]:
    """Bare identifiers this pseudocode assigns to, or binds as a loop variable.

    Anything else a body dereferences arrived from outside it.
    """
    out: set[str] = set()
    for line, _ in _walk_pseudocode(body):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)", line)
        if m:
            out.add(m.group(1))
        m = re.match(r"^for\s+([A-Za-z_][A-Za-z0-9_]*)\b", line)
        if m:
            out.add(m.group(1))
    return out


def _normalize_binding(kind: str, locals_: set[str] | None = None) -> str:
    """Collapse a binding description to what it depends on, not its spelling.

    "assigned bank_slot(b, r)" and "assigned bank_slot(b, sampled)"
    derive the same quantity through the same helper; the argument names are
    each algorithm's local business. Comparing the raw strings reports that
    agreement as a disagreement, which is worse than staying quiet -- a check
    that cries wolf on a correct fix trains a reviewer to undo it.
    """
    out = re.sub(r"\(([^()]*)\)", "(...)", kind)
    if locals_:
        # A binding phrased in terms of the algorithm's own locals is the same
        # derivation whichever local it names: "index of r in bank" and "index
        # of chosen_r in bank" both compute a position within the bank, and the
        # register they start from is each algorithm's business.
        out = re.sub(r"\b[A-Za-z_]\w*\b",
                     lambda m: "<local>" if m.group() in locals_ else m.group(),
                     out)
    return out


# Dividing, shifting or modding an index maps it out of the domain it came
# from -- an absolute register id becomes a slot within its bank. A helper
# whose name says the same thing counts too.
_DOMAIN_TRANSFORM_RE = re.compile(
    r"(?://|/|%|>>)\s*\d+|\b\w*(?:sub_?index|subindex|slot|local_?idx|"
    r"bank_?(?:idx|index|offset|slot))\w*\s*\(",
    re.I,
)


def _changes_domain(binding: str) -> bool:
    return bool(_DOMAIN_TRANSFORM_RE.search(binding))


def _binding_kinds(body: str) -> dict[str, set[str]]:
    """How each bare identifier in this body got its value.

    Two algorithms can subscript one structure with the same variable name and
    still disagree about its domain -- `for r in regs_in_bank` walks absolute
    register ids, `r = chosen_reg / 8` walks slots within a bank. Comparing the
    names finds nothing; comparing where the value came from finds it. The
    binding source is recorded verbatim so the finding can quote both sides
    back to the reviewer, who otherwise sees only one of the two algorithms.
    """
    out: dict[str, set[str]] = {}

    def put(name: str, kind: str) -> None:
        out.setdefault(name, set()).add(kind)

    for line, _ in _walk_pseudocode(body):
        # A trailing `// 9-bit index into 512 entries` is annotation, not
        # derivation. Leaving it in makes an identical binding compare unequal
        # to its own commented twin.
        line = re.sub(r"\s*//.*$", "", line).strip()
        m = re.match(r"^for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.+?):?$", line)
        if m:
            put(m.group(1), f"iterated over `{m.group(2).strip()}`")
            continue
        m = re.match(r"^for\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?):?$", line)
        if m:
            put(m.group(1), f"counted over `{m.group(2).strip()}`")
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)\s*(.+?)$", line)
        if m:
            put(m.group(1), f"assigned `{m.group(2).strip()}`")
    return out


def _declared_field_widths(spec: dict) -> list[tuple[str, int, int]]:
    """Every (field_name, bits, state_index) the spec declares."""
    out: list[tuple[str, int, int]] = []
    for si, s in enumerate(spec.get("state") or []):
        for fname, bits in field_widths(s.get("entry_format", "")).items():
            out.append((fname, bits, si))
    return out


def _same_field(a: str, b: str) -> bool:
    """Is `a` in pseudocode the field the spec declares as `b`?

    Exact match first, then equal stemmed token sets, so that a spec declaring
    'decay_ctr (8)' and writing `decay_counter = 256` is still caught. Anything
    looser would match a field to an unrelated local.
    """
    if a.strip().lower() == b.strip().lower():
        return True
    ta, tb = tokens(a), tokens(b)
    return bool(ta) and ta == tb


def _check_literal_widths(spec: dict) -> list[Finding]:
    """A constant stored into a declared field must fit that field.

    The parameter-level analogue (`unrepresentable_default`) only sees
    `parameters[].default`. A spec can satisfy it and still hard-code an
    unrepresentable constant in the pseudocode -- which is the copy an
    implementer actually types in.
    """
    out: list[Finding] = []
    widths = _declared_field_widths(spec)
    if not widths:
        return out

    for ai, a in enumerate(spec.get("algorithms") or []):
        seen: set[tuple[str, int]] = set()
        for line, _ in _walk_pseudocode(a.get("pseudocode", "")):
            for m in _LITERAL_ASSIGN_RE.finditer(line):
                target, value = m.group(1), int(m.group(2))
                for fname, bits, si in widths:
                    if not _same_field(target, fname):
                        continue
                    ceiling = (1 << bits) - 1
                    if value > ceiling and (target, value) not in seen:
                        seen.add((target, value))
                        out.append(Finding(
                            f"/algorithms/{ai}/pseudocode",
                            "unrepresentable_literal",
                            "error",
                            f"'{a.get('name')}' assigns {target} = {value}, but "
                            f"/state/{si}/entry_format declares '{fname}' as "
                            f"{bits} bits (max {ceiling}). Either widen the "
                            f"field or store a value that fits -- a counter "
                            f"that must span {value} steps typically starts at "
                            f"{ceiling} and expires at 0.",
                        ))
                    break
    return out


def _check_index_consistency(spec: dict) -> list[Finding]:
    """The same structure, subscripted the same depth, should use one index.

    Two algorithms that disagree about what indexes a table disagree about its
    shape. The usual form is a producer walking absolute ids while a consumer
    walks slots within a bank -- one of the two is out of bounds, and nothing
    in the prose says which.
    """
    out: list[Finding] = []
    algos = spec.get("algorithms") or []
    state = spec.get("state") or []
    state_names = [s.get("name", "") for s in state]
    # Sub-tables (UT0, way1, ...) are named only inside the parent entry's
    # prose, never as state entries of their own, yet they are exactly where
    # an inner-dimension disagreement hides.
    declared_words = set()
    for s_entry in state:
        blob = " ".join(str(s_entry.get(k, "")) for k in
                        ("organization", "entry_format", "indexing"))
        declared_words.update(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", blob))

    bindings = [_binding_kinds(a.get("pseudocode", "")) for a in algos]
    # structure -> depth -> innermost index expression -> {(algo_index, name)}
    seen: dict[str, dict[int, dict[str, set[tuple[int, str]]]]] = {}
    for ai, a in enumerate(algos):
        who = (ai, a.get("name", "?"))
        for line, _ in _walk_pseudocode(a.get("pseudocode", "")):
            for m in _SUBSCRIPT_RE.finditer(line):
                base, chain = m.group(1), m.group(2)
                subs = re.findall(r"\[([^\[\]]*)\]", chain)
                if not subs:
                    continue
                inner = subs[-1].strip()
                # A call or arithmetic expression is a derivation, not a
                # variable; comparing those across algorithms is noise.
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", inner):
                    continue
                seen.setdefault(base, {}).setdefault(len(subs), {}) \
                    .setdefault(inner, set()).add(who)

    for base, depths in sorted(seen.items()):
        # Only structures the spec actually declares -- as a state entry, or
        # as a sub-table named in one entry's prose. Locals may differ freely.
        if not (any(_shares_identifying_token(base, sn) for sn in state_names)
                or base in declared_words):
            continue
        for depth, idxs in sorted(depths.items()):
            # Depth 1 is the table's own index, which call sites routinely
            # spell differently for the same concept (`dest_reg`, `r`). The
            # confusion worth flagging is about an inner dimension, where an
            # absolute id and a slot-within-a-group look alike and are not.
            if depth < 2:
                continue
            users = set().union(*idxs.values())
            detail = ", ".join(
                f"{i!r} in {'/'.join(sorted(n for _, n in who))}"
                for i, who in sorted(idxs.items())
            )
            if len({name for _, name in users}) < 2:
                # One index name, used by one algorithm: ordinary local naming.
                continue
            if len(idxs) < 2:
                # SAME name in both algorithms. That is not agreement -- the
                # name can be bound from a different source on each side, which
                # is the form this disagreement takes once someone "fixes" it by
                # renaming. Fall through to the binding comparison below.
                (only_idx,) = idxs
                kinds = {}
                for ai, aname in sorted(users):
                    locals_ = _locally_bound(algos[ai].get("pseudocode", ""))
                    for k in bindings[ai].get(only_idx, {"unbound (a parameter)"}):
                        kinds.setdefault(_normalize_binding(k, locals_),
                                         set()).add(aname)
                if len(kinds) < 2:
                    continue
                detail = "; ".join(
                    f"{'/'.join(sorted(v))} {k}" for k, v in sorted(kinds.items())
                )
                for ai, aname in sorted(users):
                    out.append(Finding(
                        f"/algorithms/{ai}/pseudocode", "inconsistent_index",
                        "warn",
                        f"'{base}' is subscripted at depth {depth} by "
                        f"{only_idx!r} in every algorithm, but {only_idx!r} is "
                        f"bound from a different source in each: {detail}. "
                        f"Matching names do not make matching domains; one of "
                        f"these indexes out of bounds.",
                    ))
                continue
            # Differing index NAMES on their own turned out to be weak
            # evidence -- right once, wrong twice, because two algorithms
            # legitimately spell one register id `r` and `chosen_reg`. What
            # actually distinguishes the real defect is a domain CHANGE: one
            # side divides an absolute id down to a slot within a group and
            # the other does not, so the two indices count different things.
            # Flag only that.
            transforms = {
                any(_changes_domain(k) for k in bindings[ai].get(idx_name, ()))
                for idx_name, who in idxs.items() for ai, _ in who
            }
            if len(transforms) < 2:
                continue
            # One finding per algorithm involved, anchored at that algorithm's
            # pseudocode. A single finding on the container would be routed to
            # whichever unit owns the container -- in practice none of them --
            # and so would never reach a reviewer who could act on it.
            for ai, aname in sorted(users):
                out.append(Finding(
                    f"/algorithms/{ai}/pseudocode", "inconsistent_index", "warn",
                    f"'{base}' is subscripted at depth {depth} by different "
                    f"variables across algorithms: {detail}. If these range "
                    f"over different domains, one of them is out of bounds.",
                ))
    return out


def _check_context_writes(spec: dict) -> list[Finding]:
    """Context a consumer trusts unconditionally must be written the same way.

    A producer that initialises a field to a sentinel and then overwrites it
    only on some paths is telling the consumer to test the sentinel. A consumer
    that reads it straight is silently treating "never computed" as data.
    """
    out: list[Finding] = []
    algos = spec.get("algorithms") or []

    # name -> {"real": {(idx, algo)}, "cond": {(idx, algo)}}; reads likewise
    writes: dict[str, dict[str, set]] = {}
    reads: dict[str, set[tuple[int, str]]] = {}

    for ai, a in enumerate(algos):
        who = (ai, a.get("name", "?"))
        for line, under_cond in _walk_pseudocode(a.get("pseudocode", "")):
            # Split assignment target from value so reads on the RHS still count.
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_.\[\]\s]*?)\s*=(?!=)\s*(.+)$", line)
            lhs, rhs = (m.group(1), m.group(2)) if m else ("", line)

            for attr in _ATTR_RE.finditer(lhs):
                name = f"{attr.group(1)}.{attr.group(2)}"
                rec = writes.setdefault(name, {"real": set(), "cond": set()})
                if _SENTINEL_RHS_RE.match(rhs.strip()):
                    continue  # a sentinel init is not a real write
                (rec["cond"] if under_cond else rec["real"]).add(who)

            for attr in _ATTR_RE.finditer(rhs if m else line):
                name = f"{attr.group(1)}.{attr.group(2)}"
                if not under_cond:
                    reads.setdefault(name, set()).add(who)

    # Context a consumer reads that NO algorithm ever writes. The consumer is
    # unimplementable as written: the producer side of the handshake is simply
    # missing, and an implementer has to guess what the field holds and who
    # fills it.
    for name, who in sorted(reads.items()):
        if name in writes and (writes[name]["real"] or writes[name]["cond"]):
            continue
        head = name.split(".")[0]
        # `v = table[i]` then `v.ctr` is a local alias, and its field is the
        # consumer's own business. Carried context is the opposite shape: the
        # object arrives from outside (a parameter) and is never assigned in
        # the body, so nothing in the spec says who filled it.
        who = {(ai, aname) for ai, aname in who
               if head not in _locally_bound(algos[ai].get("pseudocode", ""))}
        if not who:
            continue
        for ai, aname in sorted(who):
            out.append(Finding(
                f"/algorithms/{ai}/pseudocode", "unproduced_context", "warn",
                f"'{aname}' reads '{name}', but no algorithm in the spec ever "
                f"writes it. The producing side of that handshake is missing, "
                f"so an implementer must invent both what the field holds and "
                f"which stage fills it.",
            ))

    for name, rec in sorted(writes.items()):
        if rec["real"] or not rec["cond"]:
            continue  # written unconditionally somewhere, or never written
        consumers = sorted(reads.get(name, set()) - rec["cond"])
        if not consumers:
            continue
        producers = sorted(rec["cond"])
        message = (
            f"'{name}' is only assigned inside a conditional branch of "
            f"{'/'.join(n for _, n in producers)}, but "
            f"{'/'.join(n for _, n in consumers)} reads it on an "
            f"unconditional path. On the paths where the write is skipped the "
            f"consumer sees the initial sentinel and cannot tell it from a "
            f"computed value."
        )
        # Both ends need to hear about it: the producer can write the slot
        # unconditionally, or the consumer can test the sentinel, and only a
        # reviewer holding that algorithm can choose.
        for ai, _ in producers + consumers:
            out.append(Finding(
                f"/algorithms/{ai}/pseudocode",
                "conditional_context_write", "warn", message,
            ))
    return out


# ------------------------------------------- declared bound vs index range

# How many elements a dimension holds, as the spec's own prose states it.
# Only forms that name a COUNT OF ELEMENTS; bit widths and value ranges are
# deliberately excluded, since "6-bit" and "[-32, 31]" are not dimensions.
_DIMENSION_RE = (
    re.compile(r"\b(\d+)\s*x\s*\d+\s*-?\s*bit", re.I),          # 9 x 6-bit weights
    re.compile(r"\bvector of\s+(\d+)\b", re.I),                  # vector of 9
    re.compile(r"\b(\d+)\s+(?:logical\s+)?registers?\b", re.I),  # 65 registers
    re.compile(r"\b(\d+)\s+entries\b", re.I),                    # 8 entries
)

# `0 .. 64`, `0..64`, `0 to 64`
_RANGE_RE = re.compile(r"(\d+)\s*(?:\.\.|to)\s*(\d+)")


# "total 65 registers", "total 7168 entries" -- an aggregate across the whole
# structure, never the width of one dimension. Counting it as a dimension
# raises the bound above every real index and silently disables the check.
_AGGREGATE_RE = re.compile(r"\b(?:total|altogether|combined|across all)\b[^.;]*",
                           re.I)


def _declared_dimensions(entry: dict) -> int | None:
    """Elements in one entry of this structure, as the entry itself declares.

    `entry_format` describes exactly one entry, so an `N x M-bit` there is the
    authoritative per-entry width and wins outright. `organization` is only a
    fallback: it mixes dimensions with aggregates ("total 65 registers") and
    reading an aggregate as a dimension lifts the bound above every possible
    index, which disables the check without failing.

    Among genuine candidates take the largest: over-estimating loses a
    finding, while under-estimating manufactures an error that blocks the
    stage and deadlocks the review loop.
    """
    fmt = _AGGREGATE_RE.sub("", str(entry.get("entry_format", "")))
    per_entry = [int(m.group(1)) for m in _DIMENSION_RE[0].finditer(fmt)]
    if per_entry:
        return max(per_entry)

    blob = _AGGREGATE_RE.sub(
        "", " ".join(str(entry.get(k, "")) for k in
                     ("organization", "entry_format")))
    vals = [int(m.group(1)) for rx in _DIMENSION_RE for m in rx.finditer(blob)]
    return max(vals) if vals else None


def _index_upper_bounds(body: str) -> dict[str, int]:
    """Largest value each bare identifier can take, where the body says so.

    Resolution is transitive but shallow and deliberately incomplete: a name
    whose bound cannot be established simply gets none, and contributes no
    finding. Guessing here would manufacture errors.
    """
    bounds: dict[str, int] = {}
    aliases: dict[str, str] = {}

    def literal_bound(expr: str) -> int | None:
        m = _RANGE_RE.search(expr)
        return int(m.group(2)) if m else None

    for _ in range(3):  # a few passes, so aliases resolve through each other
        for line, _cond in _walk_pseudocode(body):
            line = re.sub(r"\s*//.*$", "", line).strip()

            m = re.match(r"^for\s+([A-Za-z_]\w*)\s*=\s*(.+)$", line)
            if m and (b := literal_bound(m.group(2))) is not None:
                bounds[m.group(1)] = b
                continue

            m = re.match(r"^for\s+([A-Za-z_]\w*)\s+in\s+(.+?):?$", line)
            if m:
                src = m.group(2)
                if (b := literal_bound(src)) is not None:
                    bounds[m.group(1)] = b
                else:
                    inner = re.match(r"^([A-Za-z_]\w*)", src.lstrip("[ "))
                    if inner:
                        aliases[m.group(1)] = inner.group(1)
                continue

            m = re.match(r"^([A-Za-z_]\w*)\s*=(?!=)\s*(.+)$", line)
            if m:
                name, rhs = m.group(1), m.group(2)
                if (b := literal_bound(rhs)) is not None:
                    bounds[name] = b
                    continue
                # `x = pick(coll)`, `x = coll[i]`, `x = [e for e in coll ...]`
                src = re.search(r"\bfor\s+[A-Za-z_]\w*\s+in\s+([A-Za-z_]\w*)", rhs) \
                    or re.search(r"\(\s*([A-Za-z_]\w*)\s*\)", rhs) \
                    or re.match(r"^([A-Za-z_]\w*)\s*\[", rhs)
                if src:
                    aliases[name] = src.group(1)

        for name, src in aliases.items():
            if name not in bounds and src in bounds:
                bounds[name] = bounds[src]
    return bounds


def _check_declared_bounds(spec: dict) -> list[Finding]:
    """An index must fit the dimension the spec declares for it.

    This is the invariant the cross-algorithm index check only approximates.
    Two algorithms can agree perfectly with each other and both disagree with
    the state entry they subscript -- which is precisely the shape that keeps
    coming back: a per-bank vector of 9 weights, subscripted with an absolute
    register id that runs to 64. Comparing the algorithms to each other cannot
    see it; comparing each to the declaration can.
    """
    out: list[Finding] = []
    algos = spec.get("algorithms") or []
    state = spec.get("state") or []

    dims: list[tuple[str, int, int]] = []  # (state_name, max_elements, index)
    # Sub-tables (UT0, WT1, ...) are named only inside the parent entry's
    # prose, and they are what the pseudocode actually subscripts, so the
    # parent's declared dimension has to be reachable from the child's name.
    subtable_owner: dict[str, int] = {}
    for si, s_entry in enumerate(state):
        d = _declared_dimensions(s_entry)
        if d is None:
            continue
        dims.append((s_entry.get("name", ""), d, si))
        blob = " ".join(str(s_entry.get(k, "")) for k in
                        ("organization", "entry_format", "indexing"))
        for word in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", blob):
            subtable_owner.setdefault(word, si)
    if not dims:
        return out
    by_index = {si: (n, d) for n, d, si in dims}

    for ai, a in enumerate(algos):
        body = a.get("pseudocode", "") or ""
        bounds = _index_upper_bounds(body)
        if not bounds:
            continue
        reported: set[tuple[str, str]] = set()
        for line, _ in _walk_pseudocode(body):
            for m in _SUBSCRIPT_RE.finditer(line):
                base, chain = m.group(1), m.group(2)
                subs = re.findall(r"\[([^\[\]]*)\]", chain)
                if len(subs) < 2:
                    continue  # the innermost dimension is the one declared
                inner = subs[-1].strip()
                if inner not in bounds:
                    continue
                owners = [si for _, _, si in dims
                          if _shares_identifying_token(base, by_index[si][0])]
                if not owners and base in subtable_owner:
                    owners = [subtable_owner[base]]
                for si in owners:
                    sname, dim = by_index[si]
                    if bounds[inner] < dim:
                        continue
                    if (base, inner) in reported:
                        continue
                    reported.add((base, inner))
                    out.append(Finding(
                        f"/algorithms/{ai}/pseudocode", "index_exceeds_dimension",
                        "error",
                        f"'{a.get('name')}' subscripts {base} with {inner!r}, "
                        f"which reaches {bounds[inner]}, but "
                        f"/state/{si} declares that dimension as {dim} "
                        f"element(s) (valid 0..{dim - 1}). Either index by the "
                        f"position within the group rather than the absolute "
                        f"id, or declare the dimension at its true size.",
                    ))
    return out
