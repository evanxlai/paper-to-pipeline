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

import ast
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


def _bound(v):
    """A parsed range bound as the spec wrote it. `parse_range` floats every
    bound so it can accept 2.5; a message that quotes one back reads better
    -- and is easier for a reviewer to copy -- as 255 than as 255.0."""
    return int(v) if float(v).is_integer() else v


def _is_pow2(n) -> bool:
    return isinstance(n, int) and n > 0 and n & (n - 1) == 0


def _matches_choice(default, choices: list[str]) -> bool:
    """Is *default* one of *choices*, allowing for how it is spelled?

    `range` is prose the author typed; `default` is a JSON value. The two
    sides therefore disagree about spelling even when they agree about the
    value, and at this severity that disagreement is expensive: a `bool`
    parameter with `"default": true` against `"choices: true | false"` is
    the spec doing exactly the right thing, and str(True) is "True". The
    sR run of 2026-09-22 20:32 spent all three of its landed patches on
    that one finding, and the patch that "fixed" it retyped the boolean as
    the string "true" -- a correct field made wrong to satisfy a check.

    So a value matches when it matches literally, case-insensitively, or
    numerically. What stays an error is the finding this check is for: a
    default that is not among the options at all.
    """
    if str(default) in choices:
        return True
    folded = str(default).strip().lower()
    if any(folded == c.strip().lower() for c in choices):
        return True
    try:
        # `1` against `choices: 1 | 2 | 4` reads as "1" and matches, but a
        # default of 1.0 reads as "1.0" and does not. The values are equal.
        val = float(default)
    except (TypeError, ValueError):
        return False
    for c in choices:
        try:
            if float(c) == val:
                return True
        except ValueError:
            continue
    return False


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
            if not _matches_choice(default, parsed[1]):
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
                        f"default {default} lies outside range "
                        f"[{_bound(lo)}, {_bound(hi)}].",
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
                               "", strip_comments(body), flags=re.M)
        called = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", callable_text))
        for name in sorted(called):
            low = name.lower()
            # `if (x >> 63) & 1:` puts a paren after a keyword. Reporting
            # `if(...)` and `return(...)` as undefined helpers is pure noise,
            # and it arrives in the same list as the real ones.
            if _is_keyword(name):
                continue
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


# ------------------------------------------- unit-test arithmetic closure

# A test's `given`/`expect` is the only place a spec states a result an
# implementation can be held to, and it is written as prose with the
# arithmetic inlined: "Digest = 0x000 ^ 0x1F8 ^ 0x03F = 0x1C7 (decimal 455)".
# Every term in that claim is a literal, so it is decidable right here -- no
# host, no paper, no judgement -- and when it is wrong the integration agent
# copies it straight into a failing assertion.
#
# The sR spec shipped `(0xB << 8) | (0xB << 4) | 0xB = 0xBBB (decimal 2999)`.
# 0xBBB is 3003. Seven reviewers read that line and returned SUPPORTED, and
# they were not being careless: the half they checked against the paper
# (replicate the four flag bits three times) is exactly what Figure 6(c)
# says. Nobody multiplied it out, because no reviewer is asked to be a
# calculator and no check was doing it either.
#
# Graded `error`, deliberately. It is the spec disagreeing with itself, which
# is the one class a round may rewrite without a quote from the paper
# (reviewer.md's INCONSISTENT verdict, which needs a self-consistency finding
# naming the pointer) and the one class the stage refuses to hand to the
# integrators. That makes a false positive expensive, so every probe below
# gives up unless it can reduce BOTH sides to integers with nothing left over.

_ALLOWED_ARITH_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.FloorDiv, ast.Div, ast.Mod, ast.Pow,
    ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd,
    ast.UAdd, ast.USub, ast.Invert,
)
# Characters a literal-only expression may contain. An identifier survives
# this filter only if it is spelled entirely from hex digits and radix
# letters, and the node whitelist then rejects it as a Name.
_ARITH_CHARS_RE = re.compile(r"[\s0-9a-fA-FxXbBoO_+\-*/%()^|&~<>]+")
# The wordy, digit-free tail of a value -- a unit, or the beginning of the
# next assertion.
_UNIT_TAIL_RE = re.compile(r"\s+[A-Za-z][A-Za-z/%\s]*$")
# A tail carrying one of these is not a unit. "decay_ctr = 255 and valid = 1"
# is two assignments, and reading "and valid" as the unit of 255 leaves that
# 255 to be compared against the 1 of the *other* assignment -- an error
# nobody wrote, at the severity that fails the stage closed. Refusing to
# strip costs no true finding: what is left still holds letters, so the
# reading goes undecided rather than wrong. Splitting the clause on these
# words instead would be worse -- "bitwise AND of 0xF0 and 0x0F = 0x00"
# would become a clause that claims 0x0F = 0x00.
_CONJUNCTION_RE = re.compile(r"\b(?:and|or)\b", re.I)
# `lead_count (57) << 3` states its own operand. Substituting the
# parenthetical turns a claim that mentions a variable into one made of
# literals, which is how the INT digest tests spell two of their three steps.
_NAMED_VALUE_RE = re.compile(r"\b[A-Za-z_]\w*\s*\(\s*([-+]?\d+)\s*\)")
# `0xBBB (decimal 2999)`. The word is mandatory: `0x40 (bit 6)` is a bit
# position, not a restatement, and reading it as one would invent an error.
_HEX_DEC_RE = re.compile(
    r"0x([0-9A-Fa-f]+)\s*\(\s*(?:decimal|dec\b\.?)\s*([0-9]+)\s*\)", re.I
)
# `0b1011 (0xB)` -- one value restated in another radix, parenthesised.
_RESTATEMENT_RE = re.compile(
    r"(?<![\w.])((?:0[xXbBoO])?[0-9A-Fa-f_]+)\s*\(\s*([^()]{1,48}?)\s*\)"
)
# Sentence-ish boundaries. `.` only when it ends a word, so `2.5` survives;
# `:` because a test spells its steps "9 bits: Value[63:55] = ...".
_CLAUSE_SPLIT_RE = re.compile(r"[,;:]|\.(?=\s|$)")
# An `=` asserting the two sides are equal -- not `==`, `<=`, `>=` or `!=`.
_EQ_SPLIT_RE = re.compile(r"(?<![=<>!+\-*/&|^])=(?!=)")
# A parenthetical that only restates the number before it -- `(decimal 455)`,
# `(0x5A4)`, `(binary 1001)`. Removing it is what lets the equality chain read
# the final term: "= 1444 (0x5A4)" parses as two expressions and is otherwise
# undecidable, which silently cost this check two wrong digest tests. The
# restatement itself is not lost; the probe above owns that shape.
#
# Deliberately narrow: the content must be one literal, optionally labelled,
# so a real subexpression like `(15 << 6)` or `min(count, 63)` is untouched.
_DECIMAL_PAREN_RE = re.compile(
    r"\(\s*(?:(?:decimal|dec\b\.?|hex|binary|bin\b\.?)\s*)?"
    r"(?:0[xXbBoO])?[0-9A-Fa-f_]+\s*\)", re.I
)


def _literal_arith(text: str):
    """Integer value of *text* if it is arithmetic over numeric literals.

    None for anything that names, subscripts or calls something: those depend
    on context the sentence does not supply, and an `error` finding must never
    rest on a guess about what they hold.
    """
    s = (text or "").strip().strip(".,;:").strip()
    # A unit trails the value it measures: "= 53863 bits", "= 6.575 KiB".
    # The tail must be wordy and digit-free, so "12-bit digest" and
    # "decimal 455" are left alone -- stripping those would hand the
    # evaluator half a phrase and let it decide a claim nobody made.
    tail = _UNIT_TAIL_RE.search(s)
    if tail and not _CONJUNCTION_RE.search(tail.group(0)):
        s = s[:tail.start()].strip()
    if not s or not re.search(r"\d", s):
        return None
    if not _ARITH_CHARS_RE.fullmatch(s):
        return None
    try:
        tree = ast.parse(s, mode="eval")
    except (SyntaxError, ValueError, MemoryError, RecursionError):
        return None
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_ARITH_NODES):
            return None
        if isinstance(node, ast.Constant) and not isinstance(node.value, int):
            # Floats are excluded rather than compared with a tolerance: the
            # specs that carry them also carry a rounding rule ("floor(w *
            # 2.5)") that this evaluator deliberately does not model.
            return None
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            # `2 ** 400000` is a denial of service, not a digest.
            if not (isinstance(node.right, ast.Constant)
                    and isinstance(node.right.value, int)
                    and abs(node.right.value) <= 64):
                return None
    try:
        val = eval(compile(tree, "<expect>", "eval"), {"__builtins__": {}}, {})
    except Exception:
        return None
    return val if isinstance(val, int) and not isinstance(val, bool) else None


def _signed_readings(token: str, value: int) -> set:
    """Both readings of a fixed-width literal: unsigned, and two's complement.

    `0xFFFFFFFFFFFFFFFE (-2)` is a correct restatement of a 64-bit register
    value, not a slip, and the INT digest tests need exactly that vector. A
    probe blind to the signed reading reports every negative test case as an
    error -- which, at this severity, fails the stage closed on a spec that is
    right. Width comes from the literal's own digits, so it is the spec
    saying how wide the field is, not this check assuming.
    """
    out = {value}
    if m := re.fullmatch(r"0[xX]([0-9A-Fa-f_]+)", token or ""):
        bits = 4 * len(m.group(1).replace("_", ""))
    elif m := re.fullmatch(r"0[bB]([01_]+)", token or ""):
        bits = len(m.group(1).replace("_", ""))
    else:
        bits = 0
    if bits and value >= (1 << (bits - 1)):
        out.add(value - (1 << bits))
    return out


def _arith_readings(text: str) -> list:
    """Every value *text* can take under a plausible reading of `^`.

    `^` is XOR to Python and exponentiation to a paper, and the characters
    alone do not say which: a digest test means `960 ^ 480 ^ 4` bitwise, while
    storage prose means `2^11` as a power. The first version of this check
    guessed from context -- a caret with no `0x` literal beside it was assumed
    to be an exponent -- and that guessed wrong on exactly the claims it
    existed to decide: two digest tests wrote their XOR chains over decimal
    operands and sailed through with expected values that were off by 896 and
    16.

    So do not guess. Evaluate both, and let the claim settle it: a mismatch is
    reported only when it holds under no reading at all. `2^11 = 2048` is 9 as
    XOR and 2048 as a power, so one reading holds and nothing is reported;
    `960 ^ 480 ^ 4 = 1444` is 548 as XOR and undecidable as a power (the Pow
    guard refuses an exponent that large), so every decidable reading
    disagrees and it is reported.

    The direct reading comes first, so a report quotes the value a reader is
    most likely to have meant.
    """
    out = []
    for candidate in (text, text.replace("^", "**") if "^" in (text or "") else None):
        if candidate is None:
            continue
        val = _literal_arith(candidate)
        if val is not None and val not in out:
            out.append(val)
    return out


def _agrees(left: list, right: list) -> bool:
    """Do any two readings of the sides match, signed forms included?"""
    return any(r in _signed_readings("", l) for l in left for r in right)


def _arith_claims(text: str):
    """Yield (shown, stated, computed) for every decidable claim in *text*."""
    raw = text or ""

    for m in _HEX_DEC_RE.finditer(raw):
        computed, stated = int(m.group(1), 16), int(m.group(2), 10)
        if stated not in _signed_readings("0x" + m.group(1), computed):
            yield m.group(0), stated, computed

    for m in _RESTATEMENT_RE.finditer(raw):
        if _HEX_DEC_RE.match(m.group(0)):
            continue  # the probe above already owns this shape
        left = _arith_readings(m.group(1))
        right = _arith_readings(m.group(2))
        if not left or not right:
            continue
        if right[0] in _signed_readings(m.group(1), left[0]):
            continue
        if not _agrees(left, right):
            yield m.group(0), right[0], left[0]

    body = _NAMED_VALUE_RE.sub(r"\1", _DECIMAL_PAREN_RE.sub("", raw))
    for clause in _CLAUSE_SPLIT_RE.split(body):
        parts = _EQ_SPLIT_RE.split(clause)
        if len(parts) < 2:
            continue
        vals = [_arith_readings(p) for p in parts]
        for i in range(len(parts) - 1):
            left, right = vals[i], vals[i + 1]
            if left and right and not _agrees(left, right):
                yield clause.strip(), right[0], left[0]


def _check_unit_test_arithmetic(spec: dict) -> list[Finding]:
    out: list[Finding] = []
    for ti, t in enumerate(spec.get("unit_tests") or []):
        for fld in ("given", "expect"):
            seen: set = set()
            for shown, stated, computed in _arith_claims(t.get(fld, "") or ""):
                if stated in _signed_readings("", computed) or (shown, stated) in seen:
                    continue
                seen.add((shown, stated))
                out.append(Finding(
                    f"/unit_tests/{ti}/{fld}", "arith_mismatch", "error",
                    f"'{shown.strip()}' does not hold: the expression "
                    f"evaluates to {computed} ({hex(computed)}), but the text "
                    f"states {stated} ({hex(stated)}). One of the two is a "
                    f"transcription slip, and an implementer copying this "
                    f"test writes an assertion that can never pass.",
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


# Pseudocode comments are prose, and prose read as dataflow is noise. The sR
# spec commented its own figure transcription -- "# Value[5:0] at [11:6]",
# "# LSUM = sB + sG + sP + ..." -- and the bare-name scan duly reported
# `Value`, `at`, `sB`..`sT`, `MSBs`, `Right`, `sign`, `pre` and `shift` as
# unproduced context: 8 of 26 warnings, against 2 real holes (`fp_format`,
# `checkpointed_digests`). A reviewer who has to sift that ratio learns to
# skip the whole class.
#
# Both conventions are stripped because both dialects show up: `//` from
# C-flavoured pseudocode, `#` from the Python-flavoured kind these specs are
# actually emitted in. Only `#` was missing, which is why the noise appeared.
_COMMENT_RE = re.compile(r"(?://|#).*$")


def strip_comments(body: str) -> str:
    """*body* with every trailing comment removed, line structure preserved.

    Line count and indentation are load-bearing for the block walker, so a
    comment-only line becomes empty rather than disappearing.
    """
    return "\n".join(_COMMENT_RE.sub("", ln) for ln in (body or "").splitlines())


def _statements(body: str):
    """Comment-stripped statements. `a = f(x); b = g(y)` is two, not one."""
    for raw in strip_comments(body).splitlines():
        for part in raw.split(";"):
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
                # `def tick(n=1)` binds `n`. Keeping the default in the name
                # made it fail the identifier match, so the parameter counted
                # as unbound and every read of it was reported as context no
                # algorithm writes.
                name = part.split(":")[0].split("=")[0].strip().lstrip("*")
                if re.fullmatch(r"[A-Za-z_]\w*", name):
                    out["scalar"].add(name)
    out["callee"].update(_CALLEE_RE.findall(strip_comments(body)))
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


# ------------------------------------- carried state nobody budgeted for

# A name an algorithm reads that no stage writes is already reported against
# that algorithm. When the name is a *structure* the pseudocode subscribes
# per branch, it has a second half: it is storage, and the resource accounting
# has to pay for it.
#
# Those two halves live in different review units. `partition` gives
# `/algorithms/5` to the update reviewer and `/resource_accounting` to the
# global one, and neither can see the pair -- so in the sR run the update
# reviewer correctly asked how prediction-time digests reach branch
# resolution, while the global reviewer signed off a 53,863-bit total that
# budgets no checkpoint at all, and nothing connected them. Raising the
# consequence at the accounting pointer is what puts it in front of the one
# reviewer who owns that field.
#
# `warn`, not `error`: a paper may legitimately exclude speculative
# checkpoint state from its budget -- RUNLTS's own Table 3 does -- so whether
# this spec must count it is a judgement call, which is exactly what a
# reviewer is for.
_CARRY_CODES = frozenset({"unproduced_context", "cross_algorithm_local"})
_CARRIED_NAME_RE = re.compile(r"^'([^']+)' reads '([^']+)'")
# What separates a carry from a wire is WHEN it is read, and the spec states
# that in each algorithm's `trigger`. A value an algorithm reads at branch
# resolution cannot have been handed to it -- the branch predicted long
# earlier, so something held the value in between, and at iso-storage that
# something counts. A value read at decode or writeback is a signal available
# right there.
#
# Matching on the spec's prose about the value instead does not work:
# `inst.writes_register` (a decode signal) and `pred_info.bank_wt_sum` (saved
# per in-flight branch) both share the word "register" with a
# host_interfaces entry that talks about saving registers, so word overlap
# cannot tell them apart. The trigger can.
_LATE_STAGE_RE = re.compile(
    r"\b(resolut\w*|resolv\w*|commit\w*|retire\w*|squash\w*|flush\w*|"
    r"mispredict\w*|recover\w*)\b", re.I
)
# `avail_regs_per_bank.get(b, [])` is a container method, not a field of a
# saved record. Reporting it as unbudgeted storage is reporting the dialect.
_CONTAINER_METHODS = frozenset({
    "get", "keys", "values", "items", "append", "add", "insert", "pop",
    "size", "length", "len", "count", "clear", "contains", "has_key", "empty",
})


def _check_carried_state_budget(
    spec: dict, carried: list[Finding] | None = None,
) -> list[Finding]:
    algos = spec.get("algorithms") or []
    subscripted: set[str] = set()
    for a in algos:
        subscripted.update(_SUBSCRIPT_READ_RE.findall(
            strip_comments(a.get("pseudocode", "") or "")))

    acct = spec.get("resource_accounting") or {}
    budget_tok = tokens(" ".join(str(v) for v in acct.values()))
    declared_names = [str(e.get("name", "")) for e in (spec.get("state") or [])]

    # Algorithms that run downstream of prediction. Declaring the carry a host
    # interface does not settle it: something still has to hold the value from
    # prediction to resolution, and under an iso-storage rule that counts.
    # Pushing it across the interface is exactly how a budget gets
    # understated -- one sR spec declared that "the set of available registers
    # in each bank and the computed weight sums must be saved in branch
    # prediction state", then totalled 53,863 bits with no checkpoint in it.
    late_readers = {
        str(a.get("name", "")) for a in algos
        if _LATE_STAGE_RE.search(str(a.get("trigger", "")))
    }

    out: list[Finding] = []
    groups: dict[str, dict] = {}
    for f in carried or []:
        if f.code not in _CARRY_CODES:
            continue
        m = _CARRIED_NAME_RE.search(f.message)
        if not m:
            continue
        reader, raw = m.group(1), m.group(2)
        name = raw.split(".")[0]
        # Coverage is judged on the RECORD, not on each of its fields: a
        # breakdown that sizes "pred_info checkpoint: 780 bits per branch" has
        # accounted for the whole struct, and demanding it also name
        # `saved_digest` would report a spec that did the right thing.
        tok = tokens(name)
        # Two shapes qualify as storage, and a bare scalar is neither:
        # `fp_format` is a decision an algorithm was handed, not a table
        # somebody has to build.
        #   - a structure the pseudocode subscripts per branch;
        #   - a dotted field read off an object no stage fills, where the
        #     spec's own host_interfaces text says the value is saved across
        #     stages. Without that language a dotted read is as likely to be a
        #     per-instruction signal (`inst.writes_register`), which belongs
        #     in host_interfaces and is already reported there.
        field = raw.split(".", 1)[1] if "." in raw else ""
        if field.split(".")[0].lower() in _CONTAINER_METHODS:
            continue
        keyed = name in subscripted
        if not keyed and not ("." in raw and reader in late_readers):
            continue
        # Subset, not intersection. The sR accounting narrates "Digest
        # generation requires 64-bit leading/trailing zero/one counter
        # trees" in its logic notes, so any check that accepted a shared
        # "digest" token would read that sentence as having budgeted
        # `checkpointed_digests` -- the one structure it does not cover.
        if not tok or tok <= budget_tok:
            continue
        if any(_contains_name(name, d) for d in declared_names):
            continue
        # One record, one decision. Three fields of the same saved struct are
        # one thing to size, and three findings about it would crowd out the
        # rest of the round's evidence.
        group = groups.setdefault(name, {"reader": reader, "fields": []})
        if raw not in group["fields"]:
            group["fields"].append(raw)

    for name, g in groups.items():
        shown = ", ".join(f"'{f}'" for f in sorted(g["fields"]))
        plural = len(g["fields"]) > 1
        out.append(Finding(
            "/resource_accounting/storage_breakdown",
            "unbudgeted_carried_state", "warn",
            f"{shown} {'are' if plural else 'is'} carried per-branch into "
            f"'{g['reader']}', which runs after the branch was predicted; no "
            f"algorithm produces {'them' if plural else 'it'} and no state "
            f"entry declares {'them' if plural else 'it'}, yet the breakdown "
            f"never mentions {'them' if plural else 'it'}. Declaring a host "
            f"interface does not settle it: something still has to hold the "
            f"value from prediction to resolution, and at iso-storage that "
            f"counts. Size it as a state entry and add it to the total, or "
            f"say in logic_cost_notes why it is free. As written the total "
            f"omits storage the algorithms require.",
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
    findings += _check_unit_test_arithmetic(spec)
    findings += _check_literal_widths(spec)
    findings += _check_branch_guards(spec)
    findings += _check_index_consistency(spec)
    # Both halves of the unproduced-read scan feed the budget check: dotted
    # fields come from _check_context_writes, bare names from
    # _check_carried_state, and a carry can be either shape.
    context = _check_context_writes(spec)
    carried = _check_carried_state(spec)
    findings += context
    findings += carried
    findings += _check_carried_state_budget(spec, context + carried)
    findings += _check_declared_bounds(spec)
    return findings


def severity_counts(findings: list[Finding]) -> dict[str, int]:
    out = {"error": 0, "warn": 0, "info": 0}
    for f in findings:
        out[f.severity] = out.get(f.severity, 0) + 1
    return out


def new_errors(before: list[Finding], after: list[Finding]) -> list[Finding]:
    """Errors a round introduced: present after, absent before.

    Keyed by (code, pointer), not by message. A round rewrites the very
    numbers a message quotes, so "state sizes sum to 96871 but
    total_storage_bits is 53863" and the same complaint with different
    figures are one defect at one place, and comparing the prose would read
    every patch as having fixed something.
    """
    had = {(f.code, f.pointer) for f in before if f.severity == "error"}
    out: list[Finding] = []
    seen: set = set()
    for f in after:
        key = (f.code, f.pointer)
        if f.severity == "error" and key not in had and key not in seen:
            seen.add(key)
            out.append(f)
    return out


def is_worse(before: list[Finding], after: list[Finding]) -> bool:
    """Did a review round make the spec less self-consistent?

    Errors dominate: a round may trade warnings for a fix, but it may never
    introduce a new contradiction. Info findings are excluded -- they exist to
    inform a reviewer, and letting a heuristic note roll back a round would put
    the loosest parser in charge of the tightest decision.

    "Never introduce a new contradiction" is what this said and not what it
    did: comparing counts alone, one error traded for a different one reads as
    no change at all. A round that cleared `param_range` at /parameters/0 and
    broke `storage_sum` at /resource_accounting went 1 -> 1 and sailed past
    this gate, to be rejected downstream by a rule that blamed the patches
    which had done the fixing.
    """
    b, a = severity_counts(before), severity_counts(after)
    if a["error"] > b["error"] or new_errors(before, after):
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
# The same contradiction reached through a threshold instead of a store:
# `decay_counter >= 256` against a field the spec declares as 8 bits. Nothing
# is ever assigned out of range, so the assignment scan above sees nothing --
# and the condition is simply never true, so the mechanism it guards silently
# does not run. An 8-bit counter incremented from 0 wraps or saturates at 255,
# and the paper's 256-instruction decay never fires.
#
# This is the worse of the two shapes. An over-wide assignment truncates,
# which at least changes behaviour visibly; an unreachable guard removes a
# feature while every test that does not exercise the timeout still passes.
_LITERAL_COMPARE_RE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(>=|>|==)\s*(\d+)\b"
)
# The same store reached through a parameter name instead of a number:
# `decay_ctr = decay_interval`, where the knob defaults to 256 and the field
# is declared 8 bits. Neither scan above sees it -- there is no literal on the
# line, and the parameter's own default is waived as a span (see
# _check_parameters). Anchored at end-of-line on purpose: `= decay_interval - 1`
# is the countdown encoding that makes the span fit, and must not match.
_PARAM_ASSIGN_RE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)\s*([A-Za-z_][A-Za-z0-9_]*)\s*$"
)

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
    for raw in strip_comments(body).splitlines():
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
    """A value stored into a declared field must fit that field.

    The parameter-level analogue (`unrepresentable_default`) only sees
    `parameters[].default`. A spec can satisfy it and still hard-code an
    unrepresentable constant in the pseudocode -- which is the copy an
    implementer actually types in.

    Three shapes, all reading the same declaration: a literal stored into the
    field, a literal compared against it, and a parameter whose default the
    parameter check waived as a span stored into it without the countdown
    encoding that waiver assumed.
    """
    out: list[Finding] = []
    widths = _declared_field_widths(spec)
    if not widths:
        return out
    params = {
        p.get("name"): p.get("default")
        for p in spec.get("parameters") or []
        if isinstance(p.get("default"), int)
        and not isinstance(p.get("default"), bool)
    }

    for ai, a in enumerate(spec.get("algorithms") or []):
        seen: set[tuple] = set()
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

            for m in _LITERAL_COMPARE_RE.finditer(line):
                target, op, value = m.group(1), m.group(2), int(m.group(3))
                for fname, bits, si in widths:
                    if not _same_field(target, fname):
                        continue
                    ceiling = (1 << bits) - 1
                    # Unreachable only. `field < 256` on an 8-bit field is
                    # always true, which is a different (and milder) defect
                    # than a guard that can never fire, and flagging it here
                    # would put a dead-code smell in the same class as a
                    # mechanism that does not run.
                    unreachable = (
                        (op == ">" and value >= ceiling)
                        or (op == ">=" and value > ceiling)
                        or (op == "==" and value > ceiling)
                    )
                    if unreachable and (target, op, value) not in seen:
                        seen.add((target, op, value))
                        out.append(Finding(
                            f"/algorithms/{ai}/pseudocode",
                            "unreachable_literal_compare",
                            "error",
                            f"'{a.get('name')}' tests {target} {op} {value}, "
                            f"but /state/{si}/entry_format declares '{fname}' "
                            f"as {bits} bits, so it never exceeds {ceiling} "
                            f"and this condition can never be true. Whatever "
                            f"it guards never runs. Either widen the field or "
                            f"restate the threshold to fit -- a counter that "
                            f"must span {value} steps typically starts at "
                            f"{ceiling} and expires at 0.",
                        ))
                    break

            # The span the parameter check waived, now that the pseudocode
            # has said how it stores it. `unrepresentable_default` permits
            # `default == 2**bits` because a B-bit counter really can span
            # 2^B steps -- but only as a countdown loaded at 2^B - 1, and
            # nothing verified the body actually does that. Run 4 of the sR
            # spec wrote `decay_ctr = decay_interval` with the knob at 256
            # into a field it declares as 8 bits: the store truncates to 0,
            # the next decode reads the counter as already expired and clears
            # the valid bit, and every digest dies one instruction after it
            # is born. The feature is inert and no test that does not time
            # the decay can tell.
            #
            # The split with the parameter check is exactly at
            # `default == 2**bits`: above that the default is wrong whatever
            # the body does and `unrepresentable_default` owns it, at it the
            # default is fine and only the store is wrong. One defect, one
            # finding, at the pointer whose edit fixes it.
            m = _PARAM_ASSIGN_RE.search(line)
            if not m or m.group(2) not in params:
                continue
            target, pname = m.group(1), m.group(2)
            default = params[pname]
            for fname, bits, si in widths:
                if not _same_field(target, fname):
                    continue
                ceiling = (1 << bits) - 1
                key = ("param", target, pname)
                if default == (1 << bits) and key not in seen:
                    seen.add(key)
                    out.append(Finding(
                        f"/algorithms/{ai}/pseudocode",
                        "span_stored_directly",
                        "error",
                        f"'{a.get('name')}' assigns {target} = {pname}, and "
                        f"'{pname}' defaults to {default}, but "
                        f"/state/{si}/entry_format declares '{fname}' as "
                        f"{bits} bits (max {ceiling}). A field of {bits} "
                        f"bits spans {default} steps only as a countdown: load "
                        f"{ceiling} and expire at 0. Stored directly it "
                        f"truncates to {default & ceiling}, which every later "
                        f"test reads as already expired, so the mechanism "
                        f"never runs a single step of its span. Either write "
                        f"{target} = {pname} - 1, or widen the field.",
                    ))
                break
    return out


# ------------------------------------------ guards that can never be reached

# `(reg_val_64 >> 48) == 0xFFFF` -- a prefix test, which is how pseudocode
# classifies a NaN-boxed value. Two of them in one if/else-if chain can
# silently order one out of existence.
_SHIFT_EQ_RE = re.compile(
    r"\(?\s*([A-Za-z_]\w*)\s*>>\s*(\d+)\s*\)?\s*==\s*(0[xX][0-9A-Fa-f]+|\d+)"
)
_IF_RE = re.compile(r"^if\b")
_ELSE_IF_RE = re.compile(r"^(?:else\s+if|elif)\b")


def _guard_chains(body: str):
    """Yield each if/else-if chain as a list of its guard lines.

    Indentation is the only block structure pseudocode carries, and chains
    nest: the sR format classifier is an if/else-if inside the `else if` arm
    of an outer one. So chains are tracked per indent level rather than one
    at a time -- walking only the outermost would skip every guard that
    matters here. A line closes every chain deeper than itself, continues one
    at its own indent if it is an `else if`, and otherwise ends it.
    """
    open_chains: dict[int, list[str]] = {}
    for raw in strip_comments(body).splitlines():
        if not raw.strip():
            continue
        indent, line = len(raw) - len(raw.lstrip()), raw.strip()
        for deeper in sorted((d for d in open_chains if d > indent), reverse=True):
            yield open_chains.pop(deeper)
        if indent in open_chains:
            if _ELSE_IF_RE.match(line):
                open_chains[indent].append(line)
                continue
            yield open_chains.pop(indent)
        if _IF_RE.match(line):
            open_chains[indent] = [line]
    for indent in sorted(open_chains, reverse=True):
        yield open_chains.pop(indent)


def _prefix_guard(line: str):
    """(variable, shift, constant) for `(v >> k) == C`, else None."""
    m = _SHIFT_EQ_RE.search(line)
    if not m:
        return None
    raw = m.group(3)
    value = int(raw, 16) if raw[:2].lower() == "0x" else int(raw, 10)
    return m.group(1), int(m.group(2)), value


def _check_branch_guards(spec: dict) -> list[Finding]:
    """A later guard in an if/else-if chain must be reachable past the earlier ones.

    `(v >> b) == B` tests a longer prefix of `v` than `(v >> a) == A` whenever
    b < a, and it implies the shorter test exactly when `B >> (a - b) == A`.
    Put the shorter test first and the longer one can never run.

    This is not hypothetical ordering pedantry. The sR spec classified
    floating-point formats with

        if   (v >> 48) == 0xFFFF:      // FP16
        else if (v >> 32) == 0xFFFFFFFF: // FP32

    and every FP32 NaN-boxed value has its top 16 bits set too, so the FP16
    arm swallows all of them and the FP32 arm is dead code. The reverse order
    is correct and this check stays silent on it, so the finding also tells a
    reviewer which way to move the arms.

    Graded `error`: like the other width and range probes, it is arithmetic
    over what the spec itself wrote, and the failure mode is a branch that an
    implementer transcribes faithfully and can never execute.
    """
    out: list[Finding] = []
    for ai, a in enumerate(spec.get("algorithms") or []):
        for chain in _guard_chains(a.get("pseudocode", "") or ""):
            guards = [_prefix_guard(line) for line in chain]
            for j in range(1, len(guards)):
                if guards[j] is None:
                    continue
                var_j, shift_j, const_j = guards[j]
                for i in range(j):
                    if guards[i] is None:
                        continue
                    var_i, shift_i, const_i = guards[i]
                    if var_i != var_j or shift_j > shift_i:
                        continue
                    if (const_j >> (shift_i - shift_j)) != const_i:
                        continue
                    out.append(Finding(
                        f"/algorithms/{ai}/pseudocode",
                        "unreachable_branch_guard", "error",
                        f"in '{a.get('name')}', the guard "
                        f"'{chain[j]}' can never be reached: the earlier "
                        f"'{chain[i]}' in the same if/else-if chain is "
                        f"implied by it, because "
                        f"{hex(const_j)} >> {shift_i - shift_j} is "
                        f"{hex(const_i)}. Every value that satisfies the "
                        f"later test satisfies the earlier one first, so "
                        f"that branch is dead and its case is handled by "
                        f"the wrong arm. Test the longer prefix first, or "
                        f"restate the guards so they are disjoint.",
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


# `sampled_reg_id: 7 bits (0..64)` -- a field that declares the range of the
# values it holds, not just their width. A variable read out of that field
# inherits the range, which is how an index acquires a bound the body itself
# never states: `r_upd = latch.bank[b].sampled_reg_id` is bounded by what the
# state entry says the field holds.
_PAREN_RANGE_RE = re.compile(r"\(\s*(\d+)\s*(?:\.\.|to)\s*(\d+)\s*\)")


def _declared_field_ranges(spec: dict) -> dict[str, int]:
    """field name -> largest value the spec says that field holds.

    Only ranges written against a named field in `entry_format`. A range in
    `organization` describes the structure, not one field, and attributing it
    to whichever name happens to precede it invents a bound.
    """
    out: dict[str, int] = {}
    for s_entry in spec.get("state") or []:
        fmt = str(s_entry.get("entry_format", "") or "")
        for m in _PAREN_RANGE_RE.finditer(fmt):
            # Stay inside the field's own clause, so the name picked up is the
            # field the range was written for and not its left-hand neighbour.
            clause = re.split(r"[,;{]", fmt[:m.start()])[-1]
            names = re.findall(r"\b[A-Za-z_]\w*\b", clause)
            lo, hi = int(m.group(1)), int(m.group(2))
            if names and hi >= lo:
                out.setdefault(names[0].lower(), hi)
    return out


def _index_upper_bounds(body: str,
                        field_ranges: dict[str, int] | None = None) -> dict[str, int]:
    """Largest value each bare identifier can take, where the body says so.

    Resolution is transitive but shallow and deliberately incomplete: a name
    whose bound cannot be established simply gets none, and contributes no
    finding. Guessing here would manufacture errors.

    `field_ranges` lets a bound come from the spec's own declaration rather
    than from the body. That is what catches the recurring per-bank-vector
    defect on its update side: the loop variable in `predict` is built from a
    runtime list and cannot be bounded, but `update` reads the same index out
    of a latch field the state entry declares as `(0..64)`.
    """
    bounds: dict[str, int] = {}
    aliases: dict[str, str] = {}
    field_ranges = field_ranges or {}

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
                # `r_upd = latch.bank[b].sampled_reg_id` -- the trailing name
                # is a declared field, so its declared range bounds the
                # variable. Checked before the alias heuristics below, which
                # would otherwise read the subscript as the source.
                tail = re.search(r"([A-Za-z_]\w*)\s*$", rhs)
                if tail and tail.group(1).lower() in field_ranges:
                    bounds[name] = field_ranges[tail.group(1).lower()]
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
    field_ranges = _declared_field_ranges(spec)

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
        bounds = _index_upper_bounds(body, field_ranges)
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
