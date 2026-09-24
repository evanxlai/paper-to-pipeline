"""Reviewer stage: evidence-checked verification of a distilled feature spec.

The distiller emits a draft. This stage partitions that draft, hands each part
to an independent reviewer that must ground every claim in a verbatim quote
from the paper, and then lets *code* decide which of the resulting patches
survive. Reviewers propose, the applier disposes -- the same split gate.py
already enforces for promotion.

Four verdicts, because two are not enough. Most defects in a distilled spec are
not claims the paper contradicts; they are claims the paper never addresses. A
reviewer whose only verbs are "confirm" and "fix" will invent a grounded-looking
fix for those, which is strictly worse than leaving them flagged. So an
unsupported claim becomes an open question plus candidate values for the DSE to
search, and is never silently rewritten.

Nothing in this module is keyed to a paper or a feature. Units are derived from
the spec's own name-reference graph, and evidence is validated by checking that
the quote occurs in the input text -- neither requires knowing what the paper
says.

The pure functions (partition / verify_evidence / apply_patches / regressions)
import nothing beyond the stdlib and constants, so they are unit-testable
without a cluster. The LLM backend is imported lazily inside the driver.
"""

from __future__ import annotations

import copy
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import constants as C
import paper_markers
import spec_checks
from spec_checks import Finding, stem, tokens

# A quote shorter than this matches too much text to be evidence of anything.
MIN_QUOTE_CHARS = 12

# Top-level spec keys that belong to the "global" review unit: cross-cutting
# claims that no single algorithm owns.
_GLOBAL_KEYS = ("summary", "source", "host_interfaces", "resource_accounting")
# Where a finding may ask for something the spec does not contain yet.
_APPEND_SCOPE = ("/algorithms/-",)


# ------------------------------------------------------------ json pointers


def _unescape(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def ptr_split(pointer: str) -> list[str]:
    if pointer in ("", "/"):
        return []
    if not pointer.startswith("/"):
        raise ValueError(f"not a JSON Pointer: {pointer!r}")
    return [_unescape(t) for t in pointer.split("/")[1:]]


def ptr_get(doc, pointer: str, default=None):
    cur = doc
    for tok in ptr_split(pointer):
        if isinstance(cur, list):
            if not tok.lstrip("-").isdigit():
                return default
            idx = int(tok)
            if idx >= len(cur):
                return default
            cur = cur[idx]
        elif isinstance(cur, dict):
            if tok not in cur:
                return default
            cur = cur[tok]
        else:
            return default
    return cur


def ptr_exists(doc, pointer: str) -> bool:
    sentinel = object()
    return ptr_get(doc, pointer, sentinel) is not sentinel


def ptr_apply(doc, pointer: str, value, op: str) -> None:
    """Mutate *doc* in place. `op` is 'replace' or 'add'.

    'add' with a trailing '-' appends to an array, matching RFC 6902.
    """
    parts = ptr_split(pointer)
    if not parts:
        raise ValueError("cannot patch the document root")
    cur = doc
    for tok in parts[:-1]:
        cur = cur[int(tok)] if isinstance(cur, list) else cur[tok]
    last = parts[-1]
    if isinstance(cur, list):
        if last == "-":
            cur.append(value)
        elif op == "add":
            cur.insert(int(last), value)
        else:
            cur[int(last)] = value
    else:
        cur[last] = value


def _is_append(pointer: str) -> bool:
    return pointer.endswith("/-")


# Required-property names for each appendable array, read from the spec schema
# rather than restated here: a field renamed in the schema has to rename here
# too, and a copy would not.
def _append_required(pointer: str) -> list[str]:
    key = pointer[1:-2]                 # "/algorithms/-" -> "algorithms"
    try:
        schema = json.loads(Path(C.SPEC_SCHEMA_PATH).read_text())
    except (OSError, ValueError):
        return []
    items = ((schema.get("properties") or {}).get(key) or {}).get("items") or {}
    return list(items.get("required") or [])


def _append_shape_error(pointer: str, value) -> str | None:
    """Why this appended object cannot be an element of its array, or None.

    An append is the one patch shape whose target does not exist yet, so none
    of the checks above can look at what it is replacing. Left unchecked it
    reaches the round-level schema gate, where a single missing field rejects
    the round *and* every correct patch beside it -- one observed round wrote
    the recovery algorithm the checks were asking for, called its body `logic`
    instead of `pseudocode`, and took nine unrelated fixes down with it.
    """
    required = _append_required(pointer)
    if not required:
        return None
    if not isinstance(value, dict):
        return (f"append to {pointer} must be an object with "
                f"{', '.join(required)}")
    missing = [k for k in required if k not in value]
    if not missing:
        return None
    return (f"append to {pointer} is missing required field(s) "
            f"{', '.join(missing)}; an element of that array needs "
            f"{', '.join(required)}")


_NUM_RE = re.compile(r"0[xX][0-9a-fA-F]+|\b\d+\b")
_NEGATION_RE = re.compile(r"\b(not|never|no|without|neither|unless)\b", re.I)


def _numeric_signature(text: str) -> frozenset:
    """The set of numbers a string asserts, with hex and decimal unified."""
    out = set()
    for m in _NUM_RE.finditer(text or ""):
        tok = m.group()
        out.add(int(tok, 16) if tok.lower().startswith("0x") else int(tok))
    return frozenset(out)


def _agreeing_value(values: list):
    """The preferred value when competing patches actually say the same thing.

    Independent reviewers converging on one number is the strongest signal the
    stage can produce, and comparing their prose byte-for-byte destroys it:
    three reviewers each deriving 0x0A8 and describing it differently read as a
    three-way dispute and all get dropped. Values agree when they assert the
    same numbers; the most detailed wording wins.

    Known limit: identical numbers with opposite meaning ("saturates at 63" vs
    "does not saturate at 63") would merge, so a difference in negation words
    forces the conflict path.
    """
    if len(values) < 2 or not all(isinstance(v, str) for v in values):
        return None
    if len({bool(_NEGATION_RE.search(v)) for v in values}) != 1:
        return None
    sigs = [_numeric_signature(v) for v in values]
    if any(not s for s in sigs):
        return None
    # The richest statement must contain every other one's numbers: a terse
    # "digest is 0x0A8" is consistent with a spelled-out derivation of the same
    # value, and the spelled-out one is what an implementer wants.
    widest = max(sigs, key=len)
    if not all(s <= widest for s in sigs):
        return None
    best = [v for v, s in zip(values, sigs) if s == widest]
    return max(best, key=len)


# A test expectation gets *better* by getting shorter: replacing "the digest is
# computed correctly" with "digest == 0x0A8" is the whole point of the
# vacuous_test check, and it is a 75% length cut. Length-loss rules must not
# apply here or they refuse the one fix they exist to provoke.
_TEST_TEXT_RE = re.compile(r"^/unit_tests/\d+(/(expect|given))?$")


def _is_test_text(pointer: str) -> bool:
    return bool(_TEST_TEXT_RE.match(pointer or ""))


# ----------------------------------------------------------- review units


@dataclass
class ReviewUnit:
    unit_id: str
    kind: str                       # "algorithm" | "global" | "orphan"
    elements: list = field(default_factory=list)   # [{"pointer","value"}]
    # Append pointers this unit may act on, for findings about something the
    # spec does not contain yet. An element pointer cannot express that: a
    # unit owns `/algorithms/0`, and a check reporting that the spec needs an
    # algorithm it has never had has nowhere to anchor. Without this, such a
    # finding is shown to no reviewer and patchable by none -- which makes an
    # `error` unclearable and deadlocks the stage rather than gating it.
    append_scope: list = field(default_factory=list)

    @property
    def prefixes(self) -> list[str]:
        return [e["pointer"] for e in self.elements]

    def owns(self, pointer: str) -> bool:
        if pointer in self.append_scope:
            return True
        return any(
            pointer == p or pointer.startswith(p + "/") for p in self.prefixes
        )


def _elem(spec, pointer):
    return {"pointer": pointer, "value": ptr_get(spec, pointer)}


# An assignment target, allowing subscripts and field access to interleave:
# `reg_status_table[r].valid = 0` and `wt[b].WT0[i] += 1` both name the
# structure being stored into. spec_checks' own target pattern stops at the
# first `]`, which is right for the bare-name flow analysis it does there and
# loses exactly the stores that matter here.
_STORE_TARGET_RE = re.compile(
    r"^\s*([A-Za-z_]\w*)(?:\s*\[[^\[\]]*\]|\s*\.\w+)*\s*(?:[-+*/|&^]|<<|>>)?=(?!=)"
)


def _norm_ident(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


# Below this, a containment match is noise: `v = victim_tag_table[PC]` binds a
# local named `v`, and "v" is a substring of "victimtagtable", so a rule that
# accepts any containment reads every local as a store into the table it was
# read from -- which merges every algorithm that touches the structure at all
# and dissolves the partition.
_MIN_STORE_MATCH_CHARS = 6


def _same_structure(state_name: str, root: str) -> bool:
    """Does an assignment target name the state entry, allowing for the
    abbreviations pseudocode uses (`decay_shadow` for "decay shadow
    counters")? Normalized equality, or containment with enough characters
    behind it to mean something."""
    if not state_name or not root:
        return False
    if state_name == root:
        return True
    short, long_ = sorted((state_name, root), key=len)
    return len(short) >= _MIN_STORE_MATCH_CHARS and short in long_


def _written_state(spec: dict) -> list[set[int]]:
    """Per algorithm, the indices of the state entries its pseudocode writes.

    Matched by normalized identifier, not by the token overlap the rest of
    `partition` uses. Overlap is the right rule for "which state does this
    algorithm talk about", where a false positive costs a reviewer nothing
    but some extra context; it is the wrong rule for "which algorithms must
    be reviewed together", where `sr_weight_tables` and
    `sr_usefulness_tables` share the word "table" and would collapse the
    whole partition into one unit.
    """
    names = [_norm_ident(s.get("name", "")) for s in (spec.get("state") or [])]
    out: list[set[int]] = []
    for a in (spec.get("algorithms") or []):
        mine: set[int] = set()
        body = spec_checks.strip_comments(a.get("pseudocode", ""))
        for line in body.splitlines():
            for st in line.split(";"):
                m = _STORE_TARGET_RE.match(st)
                if not m:
                    continue
                root = _norm_ident(m.group(1))
                for i, n in enumerate(names):
                    if _same_structure(n, root):
                        mine.add(i)
        out.append(mine)
    return out


def _merge_units(a: ReviewUnit, b: ReviewUnit) -> ReviewUnit:
    """One unit covering both, carrying each pointer once.

    Units share elements -- two algorithms that read the same table each
    attach it -- so concatenating their element lists shows a reviewer the
    same JSON twice and inflates the size key the cap merge sorts on.
    """
    seen: set[str] = set()
    elements = []
    for e in a.elements + b.elements:
        if e["pointer"] in seen:
            continue
        seen.add(e["pointer"])
        elements.append(e)
    return ReviewUnit(f"{a.unit_id}+{b.unit_id}", "algorithm", elements,
                      sorted(set(a.append_scope) | set(b.append_scope)))


def partition(spec: dict, max_units: int | None = None) -> list[ReviewUnit]:
    """Split a spec into mechanism-shaped review units.

    The partition is derived, not configured. Specs name their own state and
    then reference those names in pseudocode, so the reference graph is already
    in the document: one unit per algorithm, plus the state, parameters and
    tests that algorithm mentions. Depth one only -- no transitive closure --
    which bounds unit size without needing a cap for most specs.

    Splitting by schema field instead would cut across mechanisms: a digest
    format lives in `algorithms`, `unit_tests` and `open_questions` at once,
    and a reviewer that sees only one of those cannot spot the inconsistency.
    """
    algos = spec.get("algorithms") or []
    state = spec.get("state") or []
    params = spec.get("parameters") or []
    tests = spec.get("unit_tests") or []

    state_tok = [tokens(s.get("name", "")) for s in state]
    param_tok = [tokens(p.get("name", "")) for p in params]

    used_state: set[int] = set()
    used_param: set[int] = set()
    units: list[ReviewUnit] = []

    for ai, a in enumerate(algos):
        body = tokens(
            f"{a.get('name','')} {a.get('trigger','')} "
            f"{a.get('pseudocode','')} {a.get('notes','')}"
        )
        elements = [_elem(spec, f"/algorithms/{ai}")]

        mine_state = [i for i, t in enumerate(state_tok) if t and (t & body)]
        mine_param = [i for i, t in enumerate(param_tok) if t and (t & body)]
        used_state.update(mine_state)
        used_param.update(mine_param)
        elements += [_elem(spec, f"/state/{i}") for i in mine_state]
        elements += [_elem(spec, f"/parameters/{i}") for i in mine_param]

        # Tests that exercise anything in this unit ride along, so a reviewer
        # that corrects a mechanism can correct its test in the same breath.
        scope = set(body)
        for i in mine_state:
            scope |= state_tok[i]
        for i in mine_param:
            scope |= param_tok[i]
        for ti, t in enumerate(tests):
            if tokens(f"{t.get('name','')} {t.get('given','')} {t.get('expect','')}") & scope:
                elements.append(_elem(spec, f"/unit_tests/{ti}"))

        # `/parameters/-` so a reviewer told that a constant should be a knob
        # can mint it and read it from the pseudocode in the same round. The
        # repair spans two top-level arrays, and a round's patches land as a
        # set -- half of it is a regression, so half of it is refused.
        units.append(ReviewUnit(f"algo:{a.get('name', ai)}", "algorithm",
                                elements, ["/parameters/-"]))

    # Algorithms that store into the same state entry are reviewed together.
    # A defect in a shared field is rarely confined to one of them -- the
    # decay counter `decode` loads is the one `complete` reloads -- and the
    # gate applies a round's patches as a set, reverting all of them if the
    # spec ends less self-consistent than it started. So a reviewer holding
    # half the writers can only ever propose half the edit, and the half
    # lands as a regression. One observed run needed four coordinated edits
    # to fix a countdown encoding, three inside one unit and the fourth in
    # the next; the round was discarded whole, twice.
    writers = _written_state(spec)
    home = list(range(len(units)))          # algorithm index -> unit slot
    slots: list[ReviewUnit | None] = list(units)
    for si in range(len(state)):
        group = sorted({home[ai] for ai, w in enumerate(writers) if si in w})
        for other in group[1:]:
            slots[group[0]] = _merge_units(slots[group[0]], slots[other])
            slots[other] = None
            home = [group[0] if h == other else h for h in home]
    units = [u for u in slots if u is not None]

    globals_ = [_elem(spec, f"/{k}") for k in _GLOBAL_KEYS if k in spec]
    if globals_:
        # The global unit is where a whole-spec omission lands. It already
        # holds host_interfaces, which is where the signal such an algorithm
        # would need is declared, so it is the reviewer best placed to say
        # what the missing operation reads.
        units.append(ReviewUnit("global", "global", globals_,
                                list(_APPEND_SCOPE)))

    # Anything no algorithm touched. Being here is itself a smell, which is why
    # these get reviewed rather than dropped.
    orphans = [_elem(spec, f"/state/{i}") for i in range(len(state)) if i not in used_state]
    orphans += [
        _elem(spec, f"/parameters/{i}") for i in range(len(params)) if i not in used_param
    ]
    if orphans:
        units.append(ReviewUnit("orphan", "orphan", orphans))

    cap = max_units if max_units is not None else C.REVIEW_MAX_UNITS
    while len(units) > cap:
        units.sort(key=lambda u: len(u.elements))
        a, b = units.pop(0), units.pop(0)
        units.append(_merge_units(a, b))
    return units


# ----------------------------------------------------------------- records


VERDICTS = ("SUPPORTED", "CONTRADICTED", "UNSUPPORTED", "UNDERSPECIFIED",
            "INCONSISTENT")
_PATCHING_VERDICTS = ("CONTRADICTED", "UNDERSPECIFIED", "INCONSISTENT")

# Check codes that describe the spec disagreeing with ITSELF rather than with
# the paper. These are the only findings an INCONSISTENT patch may act on.
#
# The verdict exists because the other four cannot reach this class of defect.
# A spec that transcribes "invalidate after 256 instructions" from the prose
# and "decay_ctr (8)" from the storage table has copied both faithfully: every
# reviewer correctly returns SUPPORTED, because the paper does say both things.
# CONTRADICTED needs a quote saying otherwise and there is none; UNSUPPORTED
# forbids patching; UNDERSPECIFIED may only lengthen the field. So the
# contradiction survives every round no matter how many are run. INCONSISTENT
# is the verb for "these two statements cannot both be implemented", and its
# evidence is not a quote but the check going green.
_SELF_CONSISTENCY_CODES = frozenset({
    "storage_sum", "budget_fit", "param_range", "unrepresentable_default",
    "unrepresentable_literal", "breakdown_product", "inconsistent_index",
    "conditional_context_write",
    # An index whose range overruns the dimension the spec declares for it is
    # arithmetic, like the rest of this list. It was missing, and the omission
    # was not harmless: in one run a reviewer diagnosed the overrun correctly
    # in all three rounds -- "subscripts UT0 with the absolute register id
    # (0..64) rather than the intra-bank position" -- and all three patches
    # were refused as "a pointer no self-consistency check flagged", by a
    # check that had in fact flagged exactly that pointer. The run then failed
    # closed at the final gate with the defect intact.
    "index_exceeds_dimension",
    # A test whose own arithmetic does not close is the same kind of defect,
    # and it is the kind no reviewer can fix without this: the paper says
    # nothing about a decimal restatement, so CONTRADICTED has no quote to
    # offer and UNSUPPORTED forbids patching. Seven reviewers read
    # `0xBBB (decimal 2999)` and returned SUPPORTED because the half the
    # paper does settle was right.
    "arith_mismatch",
    # An unreachable threshold against a field width the spec itself declares
    # is the same arithmetic, reached through a comparison instead of a store.
    "unreachable_literal_compare",
    # And the third way to reach it: a span parameter stored into the field
    # without the countdown encoding that makes the span fit. The paper names
    # the span (256 instructions) but never the encoding, so CONTRADICTED has
    # no quote to offer and only INCONSISTENT can license the patch.
    "span_stored_directly",
    # A branch ordered behind a guard that subsumes it is dead code the spec
    # wrote against itself. The paper names the three FP formats but never
    # the discriminating bit patterns, so there is no quote to contradict --
    # the contradiction is between two lines of the spec's own pseudocode.
    "unreachable_branch_guard",
    # Speculative state with nothing to unwind it. The paper cannot settle
    # this one either way -- Section 5 defers recovering the table to future
    # work -- so CONTRADICTED has no quote to offer and UNSUPPORTED forbids
    # the patch. Without this entry the only check that enforces the
    # distiller's brief rather than the paper would be unfixable.
    "missing_recovery_algorithm",
})


@dataclass
class Record:
    unit_id: str
    pointer: str
    claim: str
    verdict: str
    quote: str | None = None
    why: str | None = None
    patch: dict | None = None
    open_question: str | None = None
    enum_candidates: list | None = None
    evidence_ok: bool = False
    rejected: str | None = None
    # Where the cited quote sits in the source, and how confidently that
    # source asserts it. Filled by verify_evidence; written to the round log
    # so a demotion can be audited without re-running the parse.
    tier: str | None = None
    source: str | None = None
    caveats: list | None = None

    def as_dict(self) -> dict:
        d = dict(self.__dict__)
        return d


def parse_records(unit_id: str, raw: str) -> tuple[list[Record], list[str]]:
    """Parse a reviewer reply into records, tolerating the usual noise."""
    errors: list[str] = []
    blocks = re.findall(r"```(?:json)?\s*\n(.*?)```", raw, re.S)
    text = blocks[-1] if blocks else raw
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        return [], [f"{unit_id}: reply was not valid JSON ({e})"]

    items = doc.get("records") if isinstance(doc, dict) else doc
    if not isinstance(items, list):
        return [], [f"{unit_id}: reply had no 'records' array"]

    out: list[Record] = []
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            errors.append(f"{unit_id}: record {i} is not an object")
            continue
        verdict = str(it.get("verdict", "")).upper().strip()
        if verdict not in VERDICTS:
            errors.append(f"{unit_id}: record {i} has unknown verdict {verdict!r}")
            continue
        ev = it.get("evidence") or {}
        out.append(Record(
            unit_id=unit_id,
            pointer=str(it.get("pointer", "")),
            claim=str(it.get("claim", "")),
            verdict=verdict,
            quote=(ev.get("quote") if isinstance(ev, dict) else None),
            why=(ev.get("why") if isinstance(ev, dict) else None),
            patch=it.get("patch") if isinstance(it.get("patch"), dict) else None,
            open_question=it.get("open_question"),
            enum_candidates=it.get("enum_candidates"),
        ))
    return out, errors


# -------------------------------------------------------- evidence checking


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def verify_evidence(
    records: list[Record], paper_text: str,
    annotation: "paper_markers.Annotation | None" = None,
) -> None:
    """Check each cited quote: that it is real, and that it is authoritative.

    This is what lets the stage generalize: no rule here knows what the paper
    says, only that a citation must be real and must not be hedged by the
    source it came from. A fabricated quote cannot promote a claim, and cannot
    carry a patch.

    Occurrence alone turned out to be too weak a bar. A source text that
    transcribes figures grades its own confidence per paragraph, and a quote
    lifted out of a paragraph the source marked INFERRED or UNCERTAIN occurs
    perfectly well while establishing nothing -- the sR floating-point digest
    placement rode three review rounds as SUPPORTED on exactly that move, with
    the retraction sitting two paragraphs below the sentence quoted. So a
    hedged quote is demoted here on the same footing as a fabricated one: the
    claim survives as an open question, not as an established fact.

    It does not catch a real, unhedged quote cited for a claim it does not
    support -- hence the mandatory `why`, which a sampled human audit reads.
    """
    hay = _normalize(paper_text)
    hay_low = hay.lower()
    ann = annotation if annotation is not None else paper_markers.annotate(paper_text)
    for r in records:
        if r.verdict not in ("SUPPORTED", "CONTRADICTED"):
            continue
        q = _normalize(r.quote or "")
        demote = None
        if len(q) < MIN_QUOTE_CHARS:
            r.evidence_ok = False
            r.rejected = (
                f"quote missing or shorter than {MIN_QUOTE_CHARS} characters"
            )
            demote = "reviewer cited unverifiable evidence; treat as assumed"
        elif q in hay or q.lower() in hay_low:
            r.evidence_ok = True
            span = ann.locate(r.quote or "")
            r.tier = span.tier if span else paper_markers.PROSE
            if span is not None:
                r.source = f"{span.block} {span.section}".strip()
                r.caveats = [n.note_id for n in ann.notes_for(span)] or None
            if r.tier in paper_markers.HEDGED_TIERS:
                r.evidence_ok = False
                r.rejected = (
                    f"quote is drawn from a passage the source marks "
                    f"{r.tier.upper()}, which does not state what the paper says"
                )
                where = r.source or "a figure transcription"
                demote = (
                    f"{r.claim} -- the only evidence offered is a passage the "
                    f"source marks {r.tier.upper()} in {where}, i.e. a reading "
                    f"of a figure rather than something the paper states. "
                    f"Treat as assumed until settled."
                )
            else:
                continue
        else:
            r.evidence_ok = False
            r.rejected = "quote does not occur in the paper text"
            demote = "reviewer cited unverifiable evidence; treat as assumed"

        # An unverifiable or hedged citation cannot settle anything. Demote
        # rather than discard: the claim is still worth flagging, just not as
        # established.
        r.verdict = "UNSUPPORTED"
        r.patch = None

        # ...but "this reviewer cited badly" and "the paper does not say" are
        # different findings, and only the first one is ours to report. When
        # the source prints the claim's numbers in a paragraph it grades
        # LITERAL or CROSS-CHECK, the rejection stands -- no patch rides a
        # quote nobody can find -- while the open question does not, because
        # there is nothing open. Writing one anyway is how the sR spec came to
        # ask six questions the paper had already answered, each phrased so it
        # read as the paper's silence rather than the reviewer's slip.
        #
        # Only the unfindable-quote branches reach this. A HEDGED quote is a
        # different case: there the reviewer quoted accurately and the source
        # itself declines to assert, so the open question is the correct
        # outcome and must survive.
        if r.tier not in paper_markers.HEDGED_TIERS:
            if corroborating := ann.corroborates(r.claim):
                where = f"{corroborating.block} {corroborating.section}".strip()
                r.rejected = (
                    f"{r.rejected}; but the source prints this claim's values "
                    f"in {where}, graded {corroborating.tier.upper()}, so the "
                    f"claim is the paper's own and only the citation is bad"
                )
                continue

        if not r.open_question:
            r.open_question = (
                demote if demote.startswith(r.claim) else f"{r.claim} ({demote})"
            )


# What each kind of note obliges the spec to admit, once it is carried.
_NOTE_DUTY = {
    paper_markers.UNCERTAIN: (
        "the input marks this UNCERTAIN, so it must not be resolved by "
        "assumption: "
    ),
    paper_markers.INFERRED: (
        "the input marks this INFERRED -- a reading of the figure's layout "
        "that the paper never states -- so whatever the spec derives from it "
        "is an assumption and not a fact: "
    ),
}


def carry_source_notes(
    spec: dict, records: list[Record], annotation: "paper_markers.Annotation",
) -> int:
    """Record every hedged point of the source the spec actually leans on.

    The source's own convention says an UNCERTAIN note must be "carried
    forward as an open question", not resolved by guessing. Leaving that to a
    model is what failed: three rounds of reviewers never mentioned the notes,
    because nothing pointed at them. Code can do it instead, and does it here.

    INFERRED notes are carried on the same footing even though the source
    never asks for it, because an unflagged inference is the worse of the two
    failures. An UNCERTAIN point at least arrives in the spec looking
    unfinished; an INFERRED one arrives looking settled, gets implemented, and
    passes every test written from the same reading. Figure 6(a)'s "the three
    fields are XORed together" is graded a reading of the drawing and sets
    every integer digest value in the design.

    Relevance is decided by citation, not by topic modelling, which keeps the
    rule feature-agnostic: a note is carried when some verified quote this
    round was drawn from the same figure section. A spec that never cites
    Figure 4 does not inherit Figure 4's ambiguities. The unit is the section
    rather than the paragraph on purpose -- a note routinely retracts a number
    printed above it inside a LITERAL block, as Figure 6(b) does to a whole
    derived column.
    """
    cited: set[tuple[str, str]] = set()
    for r in records:
        span = annotation.locate(r.quote or "")
        if span is not None and span.block:
            cited.add((span.block, span.section))
    carried = 0
    # UNCERTAIN first, document order within each tier. A section can hedge
    # one point from both ends -- infer an alignment, then retract it three
    # lines down -- and `_append_open_question` folds same-topic questions
    # together, so whichever is carried first is the wording the spec keeps.
    # The UNCERTAIN one is the better of the two to keep: it names the
    # alternative reading, where the INFERRED one only says its own reading
    # came from a drawing.
    ordered = sorted(annotation.notes,
                     key=lambda n: n.tier != paper_markers.UNCERTAIN)
    for note in ordered:
        if (note.block, note.section) not in cited:
            continue
        before = len(spec.get("open_questions") or [])
        _append_open_question(
            spec,
            f"[source {note.note_id}: {note.where}] "
            + _NOTE_DUTY[note.tier]
            + " ".join(note.text.split()),
        )
        carried += len(spec.get("open_questions") or []) > before
    return carried


# ------------------------------------------------------------ patch merging


def _enclosing_object(spec: dict, pointer: str) -> str:
    """The object whose fields a contradiction at *pointer* is between.

    Widening stops at the enclosing object: a list parent would name every
    sibling entry -- every parameter, every algorithm -- off a single
    finding, and the document root would name the whole spec. A pointer with
    no object parent is its own enclosure.
    """
    parent = pointer.rsplit("/", 1)[0]
    return parent if parent and isinstance(ptr_get(spec, parent), dict) else pointer


def _overlaps(pointer: str, region: str) -> bool:
    """Does *pointer* address something inside *region*, or contain it?"""
    return (pointer == region or pointer.startswith(region + "/")
            or region.startswith(pointer + "/"))


def _self_consistency_scope(
    spec: dict, findings: list[Finding] | None
) -> set[str]:
    """Pointers an INCONSISTENT patch may act on this round.

    A check names where a contradiction was *detected*, which is rarely the
    only place it can be *fixed*. `param_range` reports
    /parameters/0/default because that is the field it compared, but "default
    256 outside [64, 255]" is a disagreement between two siblings and widening
    /parameters/0/range settles it just as well -- only a reviewer holding the
    parameter can say which side is wrong. Scoping to the flagged leaf refused
    that repair and left the round with nowhere to put the fix.

    So the enclosing object joins the scope, bounded as `_enclosing_object`
    describes.
    """
    scope: set[str] = set()
    for f in (findings or []):
        if f.code not in _SELF_CONSISTENCY_CODES:
            continue
        scope.add(f.pointer)
        scope.add(_enclosing_object(spec, f.pointer))
    return scope


def _apply_to(spec: dict, records: list[Record]) -> tuple[dict, list]:
    """A fresh copy of *spec* with every record's patch applied.

    Adds that append to the same array must not renumber each other, so
    replaces go first and adds last. Returns the copy and the records whose
    pointer would not resolve, paired with why.
    """
    out = copy.deepcopy(spec)
    failed = []
    for r in sorted(records,
                    key=lambda x: (x.patch["op"] == "add", x.patch["pointer"])):
        try:
            ptr_apply(out, r.patch["pointer"], r.patch["value"], r.patch["op"])
        except Exception as e:  # malformed pointer, bad index, ...
            failed.append((r, e))
    return out, failed


def _num(v):
    """A range bound as the spec writes it: 256, not 256.0."""
    return int(v) if float(v).is_integer() else v


def _couple_param_ranges(
    doc: dict, findings: list[Finding], budget_bits: int | None,
    feature_budget_bits: int | None = None,
) -> dict:
    """Widen a search range that a landed default has just outgrown.

    `range` is this pipeline's own field -- the DSE's search space, and
    `_render_unit` marks it to reviewers as not a paper claim -- so a
    reviewer correcting a default *from* the paper should not have to patch
    it. Under the verdicts available it largely cannot: CONTRADICTED needs a
    quote and the paper says nothing about our search space, while
    INCONSISTENT is bounded to pointers a check flagged before the round,
    which for a spec that starts clean is nothing at all. The one edit no
    verdict could make was the mechanical one, and the correct patch beside
    it was reverted for the error it left behind.

    So the pipeline maintains its own field. The bound moves only to admit a
    default that is otherwise sound: if the value does not fit the state
    field that stores it, `unrepresentable_default` fires at the same pointer
    and nothing is widened -- a knob that overruns the hardware is a real
    defect and stays one.
    """
    before = {(f.code, f.pointer) for f in findings if f.severity == "error"}
    after = spec_checks.run_checks(doc, budget_bits, feature_budget_bits)
    # The value has to fit the hardware before the search space is asked to
    # admit it; these two findings share a pointer and only one of them is
    # ours to settle.
    unfit = {g.pointer for g in after if g.code == "unrepresentable_default"}
    for f in after:
        if f.severity != "error" or f.code != "param_range":
            continue
        if f.pointer in unfit:
            continue
        if (f.code, f.pointer) in before or not f.pointer.endswith("/default"):
            continue
        base = f.pointer.rsplit("/", 1)[0]
        param = ptr_get(doc, base)
        if not isinstance(param, dict):
            continue
        default = param.get("default")
        if isinstance(default, bool) or not isinstance(default, (int, float)):
            continue
        parsed = spec_checks.parse_range(param.get("range"))
        if not parsed or parsed[0] != "interval":
            continue
        _, lo, hi, mods = parsed
        if lo <= default <= hi:
            continue          # pow2 or some other modifier, not the bound
        lo, hi = (default, hi) if default < lo else (lo, default)
        param["range"] = (f"[{_num(lo)}, {_num(hi)}]"
                          + (f" {mods}" if mods else ""))
    return doc


def _drop_schema_breaking_patches(
    spec: dict, applied: list[Record],
) -> tuple[dict, list[tuple[Record, str]]]:
    """Re-apply the round without the patches that break the spec schema.

    The twin of `_drop_regressing_patches`, for the gate one step earlier. A
    schema error is not a judgement about whether a patch is *right*; it says
    the document can no longer be parsed as a spec at all, and the round-level
    gate answers that by discarding every patch in the round. That is the
    wrong unit of blame: one observed round appended the recovery algorithm
    the deterministic checks had been asking for, named its body `logic`
    rather than `pseudocode`, and the resulting rejection ended the stage at
    round 0 with nine unrelated fixes reverted and the error it had just
    fixed still standing.

    Leave-one-out, greedy, and it has to earn it the same way: a patch is
    dropped only if dropping it reduces the schema errors, and a document
    this cannot repair is returned untouched for the round gate to refuse.
    """
    patched = _apply_to(spec, applied)[0]
    errs = _schema_errors(patched)
    if not errs:
        return patched, []

    keep = list(applied)
    dropped: list[tuple[Record, str]] = []
    while errs and keep:
        best = None
        for r in keep:
            trial = [x for x in keep if x is not r]
            n = len(_schema_errors(_apply_to(spec, trial)[0]))
            if n < len(errs) and (best is None or n < best[1]):
                best = (r, n)
        if best is None:
            # Nothing attributable: hand the round gate the document as
            # patched rather than dropping patches on a guess.
            return patched, []
        culprit = best[0]
        keep = [x for x in keep if x is not culprit]
        dropped.append((culprit, errs[0]))
        errs = _schema_errors(_apply_to(spec, keep)[0])

    return _apply_to(spec, keep)[0], dropped


def _drop_laundering_patches(
    spec: dict, applied: list[Record],
) -> tuple[dict, list[tuple[Record, Finding]]]:
    """Re-apply the round without the patches that quietly lost detail.

    `uncovered_regressions` is a round-level verdict, and the round-level
    answer to it is to discard every patch. But a regression is attributable
    in a way a whole round is not: a field that lost 76% of its length lost it
    to whichever patch replaced the object enclosing it. One observed round
    replaced /state/1 with a correct, paper-backed correction to its size and
    organization, and in passing cut `indexing` from "3 different skewed
    hashes of the PC and the logical register index" to "skewed hashes of the
    PC". That is exactly the hollowing-out the differ exists to catch -- and
    catching it cost nine other patches, including the recovery algorithm a
    deterministic `error` had been asking for.

    Attribution is by enclosing pointer, the same rule `uncovered_regressions`
    uses to decide a patch does *not* excuse a nested loss. Unattributable
    losses are left standing for the round gate, which is the conservative
    direction: the round is still refused, just not for someone else's fault.
    """
    patched = _apply_to(spec, applied)[0]
    keep = list(applied)
    dropped: list[tuple[Record, Finding]] = []
    while True:
        left = uncovered_regressions(
            spec, patched, [r for r in keep if r.rejected is None])
        if not left:
            return patched, dropped
        culprit = blame = None
        for f in left:
            for r in keep:
                ptr = r.patch["pointer"]
                if f.pointer == ptr or f.pointer.startswith(ptr + "/"):
                    culprit, blame = r, f
                    break
            if culprit:
                break
        if culprit is None:
            # Nobody to blame: hand the round gate the document as patched.
            return _apply_to(spec, applied)[0], []
        keep = [x for x in keep if x is not culprit]
        dropped.append((culprit, blame))
        patched = _apply_to(spec, keep)[0]


def _drop_regressing_patches(
    spec: dict, patched: dict, landed: list[Record],
    findings: list[Finding], budget_bits: int | None,
    feature_budget_bits: int | None = None,
) -> tuple[dict, list[tuple[Record, Finding]]]:
    """Re-apply the round without the patches that introduced a new error.

    A patch that clears one contradiction by creating another is not a fix --
    but it must not cost the round the patches that were. One observed round
    landed three correct patches widening /parameters/0's range to admit its
    own default, plus one that cut /resource_accounting/total_storage_bits to
    the figure the paper's table prints. The second was right about the paper
    and wrong about the spec, which also declares 43008 bits of checkpoint
    state that figure excludes. Errors went 1 -> 1, and the whole round --
    correct patches included -- was discarded.

    Attribution is by enclosing object rather than by leaving each patch out
    in turn. A total and the breakdown that explains it are one statement
    spread over two fields; dropping only whichever of them a check happens to
    name leaves the other still asserting the number just rejected.

    The rebuild has to earn it: unless it actually reduces the introduced
    errors, nothing is dropped and the round-level gate decides. A regression
    this cannot attribute is left standing and visible rather than
    half-repaired.
    """
    # The coupling has to earn its place the same way the rebuild below does.
    # Applied unconditionally it clears the `param_range` that is often the
    # only error attributable to the patch that caused it -- leaving errors
    # attributable to nobody, which drops nothing and costs the round every
    # patch instead of one. So: keep the widened doc when it settles the
    # round completely, and otherwise judge the round on the doc as patched.
    def settled(doc: dict) -> tuple[dict, list[Finding]]:
        coupled = _couple_param_ranges(
            copy.deepcopy(doc), findings, budget_bits, feature_budget_bits)
        left = spec_checks.new_errors(
            findings,
            spec_checks.run_checks(coupled, budget_bits, feature_budget_bits))
        if not left:
            return coupled, []
        return doc, spec_checks.new_errors(
            findings,
            spec_checks.run_checks(doc, budget_bits, feature_budget_bits))

    patched, introduced = settled(patched)
    if not introduced:
        return patched, []

    culprit_of: dict[int, Finding] = {}
    for f in introduced:
        region = _enclosing_object(patched, f.pointer)
        for r in landed:
            if _overlaps(r.patch["pointer"], region):
                culprit_of.setdefault(id(r), f)
    if not culprit_of:
        return patched, []

    rebuilt, _ = _apply_to(spec, [r for r in landed if id(r) not in culprit_of])
    rebuilt, still = settled(rebuilt)
    if len(still) >= len(introduced):
        return patched, []
    return rebuilt, [(r, culprit_of[id(r)]) for r in landed if id(r) in culprit_of]


def _patch_digest(patch: dict | None, limit: int = 400) -> str | None:
    """The value a refused patch proposed, short enough to quote in a prompt."""
    if not isinstance(patch, dict):
        return None
    text = json.dumps(patch.get("value"), default=str)
    return text if len(text) <= limit else text[:limit] + " ...[truncated]"


def apply_patches(
    spec: dict, records: list[Record], units: list[ReviewUnit],
    findings: list[Finding] | None = None, budget_bits: int | None = None,
    feature_budget_bits: int | None = None,
) -> tuple[dict, list[dict]]:
    """Apply surviving patches deterministically. Returns (new_spec, rejections)."""
    by_unit = {u.unit_id: u for u in units}
    inconsistent_scope = _self_consistency_scope(spec, findings)
    rejections: list[dict] = []
    candidates: list[Record] = []

    def reject(rec: Record, why: str, detail: str | None = None) -> None:
        rec.rejected = why
        entry = {"unit": rec.unit_id, "pointer": rec.pointer,
                 "verdict": rec.verdict, "reason": why,
                 "value": _patch_digest(rec.patch)}
        # What the refusing check actually said. The reason names its code and
        # its pointer; the message is the half that says what would satisfy it
        # ("write target = pname - 1, or widen the field"), and it is the half
        # the next round needs.
        if detail:
            entry["detail"] = detail
        rejections.append(entry)

    for r in records:
        if not r.patch:
            continue
        if r.verdict not in _PATCHING_VERDICTS:
            reject(r, f"verdict {r.verdict} may not carry a patch")
            continue
        if r.verdict == "CONTRADICTED" and not r.evidence_ok:
            reject(r, "CONTRADICTED patch without verified evidence")
            continue
        if r.verdict == "INCONSISTENT":
            # Quote-free patching is a large hole to open, so it is bounded to
            # the objects a deterministic check flagged. Without this the
            # verdict degrades into "rewrite anything, cite nothing".
            target = str(r.patch.get("pointer") or r.pointer)
            if not any(_overlaps(target, p) for p in inconsistent_scope):
                reject(r, "INCONSISTENT patch at a pointer no self-consistency "
                          "check flagged")
                continue

        op = str(r.patch.get("op", "replace")).lower()
        pointer = str(r.patch.get("pointer") or r.pointer)
        if op not in ("replace", "add"):
            reject(r, f"unsupported patch op {op!r}")
            continue

        unit = by_unit.get(r.unit_id)
        # Coverage records legitimately add elements anywhere; they are
        # restricted to 'add' instead, so they can never remove detail.
        if unit is not None and not unit.owns(pointer):
            if not (r.unit_id == "coverage" and op == "add"):
                reject(r, f"pointer {pointer} lies outside the unit's scope")
                continue

        if op == "replace" and not ptr_exists(spec, pointer):
            reject(r, f"replace target {pointer} does not exist")
            continue

        if op == "add" and _is_append(pointer):
            shape = _append_shape_error(pointer, r.patch.get("value"))
            if shape:
                reject(r, shape)
                continue

        if op == "replace" and not _is_test_text(pointer):
            old, new = ptr_get(spec, pointer), r.patch.get("value")
            if isinstance(old, str) and isinstance(new, str):
                if r.verdict == "UNDERSPECIFIED" and len(new) <= len(old):
                    reject(r, "UNDERSPECIFIED patch must add detail, not shorten it")
                    continue
                # A patch is its own justification as far as the regression
                # differ is concerned, so without this a reviewer could cite a
                # real quote and then replace a rule with a stub -- exactly the
                # silent hollowing-out the differ exists to stop. Gutting a
                # field is refused here and escalated instead of landing.
                if old and len(new) < C.REGRESSION_RATIO * len(old):
                    reject(r, f"patch would drop "
                              f"{100 * (1 - len(new) / len(old)):.0f}% of the field; "
                              f"restate it in full or raise it as an open question")
                    # Tagged with the field, and phrased as a question about
                    # it. Integration agents read this list, and "Reviewer
                    # wanted to shorten /x" is the loop's bookkeeping rather
                    # than anything about the feature -- untagged, it was
                    # also invisible to the pointer-scoped dedup.
                    _append_open_question(
                        spec,
                        f"{r.claim} A reviewer proposed cutting this field "
                        f"down to that, which would have dropped most of what "
                        f"it says; confirm the full text before implementing.",
                        pointer,
                    )
                    continue

        r.patch = {"op": op, "pointer": pointer, "value": r.patch.get("value")}
        candidates.append(r)

    # Two reviewers disagreeing about the same field is signal. Drop both and
    # escalate rather than letting apply order pick a winner.
    #
    # Appends are exempt. Every append to an array shares the pointer "/xs/-",
    # so grouping them by pointer reads three independent additions as one
    # three-way disagreement and discards all of them. They do not address the
    # same location and cannot contradict each other.
    grouped: dict[str, list[Record]] = {}
    appends: list[Record] = []
    for r in candidates:
        if _is_append(r.patch["pointer"]):
            appends.append(r)
        else:
            grouped.setdefault(r.patch["pointer"], []).append(r)

    conflicts: list[str] = []
    applied: list[Record] = []
    for pointer, group in sorted(grouped.items()):
        values = {json.dumps(g.patch["value"], sort_keys=True, default=str) for g in group}
        if len(values) > 1:
            agreed = _agreeing_value([g.patch["value"] for g in group])
            if agreed is not None:
                winner = next(g for g in group if g.patch["value"] == agreed)
                for g in group:
                    if g is not winner:
                        reject(g, f"same assertion as another patch at {pointer}; "
                                  f"kept the more detailed wording")
                applied.append(winner)
                continue
            for g in group:
                reject(g, f"conflicting patches at {pointer} from {len(group)} reviewers")
            conflicts.append(
                f"Reviewers disagreed on {pointer}: "
                + " | ".join(sorted(g.claim for g in group))
            )
            continue
        applied.append(group[0])

    # Identical appends from different reviewers are duplicates, not conflicts.
    seen: set[str] = set()
    for r in sorted(appends, key=lambda x: (x.patch["pointer"], x.unit_id, x.claim)):
        key = r.patch["pointer"] + json.dumps(r.patch["value"], sort_keys=True, default=str)
        if key in seen:
            reject(r, "duplicate of an append already applied this round")
            continue
        seen.add(key)
        applied.append(r)

    new_spec, failed = _apply_to(spec, applied)
    for r, e in failed:
        reject(r, f"patch failed to apply: {e}")

    # Three drops, in this order. Each asks a different question of the round
    # -- is it still a spec, did it lose detail, did it break a check -- and
    # each answers by naming the patch responsible rather than by refusing the
    # round, because the round is not the unit of blame. The order is forced:
    # `_drop_regressing_patches` returns a range-coupled document that the
    # other two could not rebuild by replaying patches, so it goes last, and a
    # document that is not a spec cannot meaningfully be asked either of the
    # later questions, so the schema drop goes first.
    new_spec, broke = _drop_schema_breaking_patches(
        spec, [r for r in applied if r.rejected is None])
    for r, e in broke:
        reject(r, f"patch left the spec failing its own schema ({e})")

    new_spec, laundered = _drop_laundering_patches(
        spec, [r for r in applied if r.rejected is None])
    for r, f in laundered:
        reject(r, f"patch caused {f.code} at {f.pointer}, a loss of detail no "
                  f"patch this round claimed", detail=f.message)

    # Without a baseline there is no way to tell a regression from a defect
    # the round inherited, so the whole comparison is skipped rather than
    # guessed at.
    if findings is not None:
        new_spec, reverted = _drop_regressing_patches(
            spec, new_spec, [r for r in applied if r.rejected is None],
            findings, budget_bits, feature_budget_bits,
        )
        for r, f in reverted:
            reject(r, f"patch introduced {f.code} at {f.pointer}, which the "
                      f"spec did not have before this round", detail=f.message)

    for c in conflicts:
        _append_open_question(new_spec, c)

    # A CONTRADICTED record with verified evidence is the strongest thing this
    # stage produces: a verbatim quote from the paper saying the spec is
    # wrong. When its patch cannot land the finding used to vanish with it,
    # and the spec went on to the integration agents asserting the very thing
    # the paper contradicts, with nothing recorded anywhere. Landing the fix
    # is the reviewer's job and the gate's; surviving the failure to land it
    # is this. The question is tagged with the pointer the patch aimed at, so
    # the next round dedups against it rather than re-asking.
    for r in records:
        if r.verdict != "CONTRADICTED" or not r.rejected or not r.evidence_ok:
            continue
        where = str((r.patch or {}).get("pointer") or r.pointer)
        quote = " ".join((r.quote or "").split())
        _append_open_question(
            new_spec,
            # The claim and the quote are the substance; which internal gate
            # rejected the patch is this loop talking to itself, and it was
            # reaching the integration agents verbatim.
            f"{r.claim} The paper says: \"{quote}\" "
            f"The correction did not land, so this field still says what it "
            f"said -- resolve it before implementing.",
            where,
        )
    return new_spec, rejections


# Questions are stored tagged with the spec location that raised them, both so
# the implementing agent can jump straight there and so that dedup has a key
# that survives rewording. Anything already in the list untagged still parses:
# _question_pointer just returns None for it.
_TAGGED_RE = re.compile(r"^\[(/[^\]]*)\]\s*(.*)$", re.S)


def _question_pointer(entry: str) -> tuple[str | None, str]:
    m = _TAGGED_RE.match(entry or "")
    return (m.group(1), m.group(2)) if m else (None, entry or "")


def _element_pointer(pointer: str | None) -> str | None:
    """Collapse a pointer to the spec element it lives in.

    Reviewers anchor the same question at `/algorithms/0` one round and
    `/algorithms/0/pseudocode` the next. Those are one location as far as an
    implementer is concerned, so they must dedup against each other; keying on
    the exact pointer lets every reworded re-ask back in through a suffix.
    """
    if not pointer:
        return pointer
    parts = pointer.split("/")
    return "/".join(parts[:3]) if len(parts) > 3 else pointer


def _spec_vocabulary(spec: dict) -> set[str]:
    """Stemmed tokens of every name the spec gives something of its own."""
    vocab: set[str] = set()
    for s in spec.get("state") or []:
        vocab |= tokens(s.get("name", ""))
        for fname in spec_checks.field_widths(s.get("entry_format", "")):
            vocab |= tokens(fname)
    for p in spec.get("parameters") or []:
        vocab |= tokens(p.get("name", ""))
    for a in spec.get("algorithms") or []:
        vocab |= tokens(a.get("name", ""))
    return vocab


def _topic_signature(text: str, vocab: set[str]) -> frozenset:
    """What a question is *about*: the spec names and the numbers it cites.

    Deliberately blind to the sentence around them. "How is the 8-bit decay_ctr
    initialised to span 256 instructions?" and "What reset value does decay_ctr
    take, given 256 exceeds 8 bits?" share almost no prose and are one question.
    Small integers are dropped -- 0, 1 and 2 appear in everything.
    """
    return frozenset(t for t in tokens(text) if t in vocab) | frozenset(
        f"n{n}" for n in spec_checks.numerals(text) if n > 2
    )


def _similar(a: str, b: str, vocab: set[str]) -> bool:
    """Jaccard overlap of topic signatures, above the configured threshold."""
    sa, sb = _topic_signature(a, vocab), _topic_signature(b, vocab)
    union = sa | sb
    if not union:
        # Neither names anything the spec declares; fall back to exact text so
        # a contentless question is not deduped against an unrelated one.
        return a.strip() == b.strip()
    return len(sa & sb) / len(union) >= C.REVIEW_QUESTION_SIMILARITY


def _append_open_question(spec: dict, text: str, pointer: str | None = None) -> None:
    """Record an ambiguity once per spec location.

    Every round re-reviews the whole spec with fresh reviewers, so the same
    hole comes back reworded each time. Exact-string dedup never fires on
    those, which is how a six-page paper accumulates a hundred questions that
    are really forty.

    Dedup is scoped to the pointer, because two questions about one spec
    location are near-certainly the same question, and compares topic
    signatures rather than prose. There is deliberately no cap: a genuinely
    distinct question is never dropped, and a spec with forty under-specified
    locations should say so rather than look tidier than it is. The pointer tag
    is what makes that list navigable.
    """
    oq = spec.setdefault("open_questions", [])
    if text in oq:
        return

    vocab = _spec_vocabulary(spec)
    here = _element_pointer(pointer)
    for entry in oq:
        ptr, body = _question_pointer(entry)
        if _element_pointer(ptr) != here:
            continue
        if _similar(text, body, vocab):
            return

    oq.append(f"[{pointer}] {text}" if pointer else text)


# ------------------------------------------------ pruning at merge time

# Templates this loop writes into questions itself. They are identical across
# every question of their kind, so they dominate any word-overlap comparison
# and make two unrelated questions look like one: the four carried source
# notes in run 6 share thirty words of boilerplate and nothing else.
_QUESTION_BOILERPLATE = tuple(re.compile(rx, re.S) for rx in (
    r"the input marks this (?:UNCERTAIN|INFERRED)\b.*?:\s*",
    r"\bUnrepaired contradiction:\s*",
    r"The correction was refused by code \(.*?\), so this field still says "
    r"what it said -- resolve it before implementing\.",
    # The wordings that replaced the two above. Both spellings stay matched:
    # a spec carried forward from an earlier run still holds the old text,
    # and a gist that keeps the template scores every unrelated pair alike.
    r"The correction did not land, so this field still says what it said "
    r"-- resolve it before implementing\.",
    r"A reviewer proposed cutting this field down to that, which would have "
    r"dropped most of what it says; confirm the full text before implementing\.",
    r"This is the same decision '[^']*' already carries; resolve it in that "
    r"knob's range rather than as a second knob\.",
    # Two escalations of disagreement share "reviewers disagreed on unit
    # test", which is four content words about the review and none about
    # the spec -- enough to score a decay question against an alignment one.
    r"Reviewers disagreed on \S+:\s*",
    r"\bAlso raised at [^.]*\.",
))

# English that survives `tokens()` because that filter was written for spec
# names, not for sentences. "should" and "be" are rare across a list of
# thirty questions and carry nothing, and an overlap of exactly those three
# words merged a question about squash recovery into one about usefulness
# updates.
_QUESTION_STOPWORDS = frozenset("""
    a about all also an and any are as at be been being both but by can could
    do does each either else for from given had has have here how if in into is it its
    may might must no not of on one only or other out over per shall
    should so some such take than that the their them then there these they
    this those to two up use used using was we were what when where whether
    which will with would
""".split())

# The words every question in a list like this uses to point at its own
# subject matter rather than to say anything about it. "The paper does not
# specify the exact ..." is how half the entries open, and "paper" alone
# linked an ROB-size question to a usefulness-gate one.
_QUESTION_STOPWORDS |= frozenset(("paper", "spec", "specification"))

# The list above is written as words, and what it gets subtracted from is
# stems -- the same mismatch `_GENERIC_STEMS` was introduced to fix for
# `GENERIC_TOKENS`. Half of it never matched: `stem("does")` is "doe",
# `stem("using")` is "us", and both leaked through as content words. Two
# questions sharing nothing but "does" scored a real overlap.
_QUESTION_STOPWORD_STEMS = _QUESTION_STOPWORDS | {
    stem(w) for w in _QUESTION_STOPWORDS
}

# `0x0BDC` -- a value a question quotes back at the spec. When the spec no
# longer holds it the question is answered and nobody withdrew it: run 6
# carried "the expected value 0xBEC" against a unit test that had already
# been repaired to 0x0BDC.
#
# Three digits minimum. `0x0` and `0xF` are arguments in a sentence, not
# citations of anything -- one source note explains that "a 64-bit register
# yields a count of 64 for 0x0", and reading that as a quotation of the spec
# withdrew a hedge the paper never resolved.
_HEX_CITATION_RE = re.compile(r"\b0x[0-9A-Fa-f]{3,}\b")
# "the parameter defaults set wt0_entries to 128" -- a claim about a knob's
# value that the spec can settle. Run 6 carried this one after the defaults
# had been swapped back to match the figure.
_VALUE_CLAIM_RE = re.compile(r"\b([A-Za-z_]\w*)\s+(?:to|=|is|of)\s+(\d+)\b")
# How much of the smaller question's rare vocabulary the two have to share.
# See `_question_clusters` for how it was calibrated.
_CLUSTER_RATIO = 0.4
# The companion bar, on rarity-weighted overlap normalised by the lighter
# question. Calibrated over every pair of run 7's thirty-five live
# questions. Ranked by score, the first thirteen pairs are all genuinely
# one question -- 1.00, 1.00, 1.00, 0.66, 0.61, 0.61, 0.47, 0.41, 0.38,
# 0.38, 0.30, 0.30, 0.29 -- and the first that is not scores 0.287, two
# UNCERTAIN notes that happen to come off the same figure.
#
# The bar is 0.40 rather than anywhere in that overlap zone. It takes the
# three clusters the audit named -- the usefulness threshold asked four
# ways, the theta pair, FP classification -- with 40% of headroom over the
# first false merge, and leaves three real duplicates below it uncollapsed.
# That is the right way round: a surviving duplicate costs a reviewer a
# second read, a wrong merge loses a question for good. A bar tuned to
# catch those last three would sit inside a 0.003 gap, which is fitting to
# one run's noise rather than calibrating against it.
#
# The weighting is degenerate on a very short list -- with two questions,
# every word they share has frequency 2 out of 2 and so weighs log(1) = 0,
# and the rule can never fire. That is the safe degeneracy: this rule is
# purely additive to the rare-word one above, so a short list simply keeps
# the behaviour it had before. It needs a real list to say anything, which
# is the same list it was calibrated on.
_CLUSTER_WEIGHTED_RATIO = 0.40


def _question_gist(entry: str) -> str:
    """A question with its pointer tag and this loop's own templates removed."""
    _, body = _question_pointer(entry)
    for rx in _QUESTION_BOILERPLATE:
        body = rx.sub(" ", body)
    return " ".join(body.split())


def _spec_without_questions(spec: dict) -> str:
    """Everything the spec asserts, minus the questions about it.

    Searching the whole document for a quoted value finds the question's own
    copy of it and calls every stale citation live -- which is exactly what
    the first draft of `_stale_questions` did.
    """
    return json.dumps({k: v for k, v in spec.items() if k != "open_questions"})


# A carried source note tags itself with the paper location it came from --
# `carry_source_notes` passes no spec pointer. One that also carries a
# `[/...]` tag got it from `prune_open_questions` merging it into a cluster
# of real spec questions, which is the spec claiming it.
_SOURCE_NOTE_TAG_RE = re.compile(r"\[source\s+([A-Za-z]\d+)\s*:\s*([^\]]*)\]")
# How much of a carried note's own vocabulary the spec has to use before the
# note counts as being about something the spec does.
#
# Measured over run 7's five carried notes. The four the spec draws on score
# 0.327, 0.333, 0.364 and 0.368; Figure 7's -- a stacked MPKI bar chart a
# register-value predictor reads nothing off -- scores 0.080, its only
# shared words being "feature" and "source". Anywhere in 0.1 to 0.3
# separates them; 0.15 leaves the wider margin on the side that matters,
# since keeping an off-topic note costs a reviewer's attention and dropping
# a live one loses a hedge the paper asked to have carried.
#
# Stopwords come out first. `tokens()` was written for identifiers, and on
# a sentence it scores "are", "at", "be" and "by" as shared vocabulary --
# which alone put Figure 7's note at 0.289, above any usable bar.
_NOTE_RELEVANCE = 0.15
_NOTE_STOPWORDS = _QUESTION_STOPWORD_STEMS


def _off_topic_source_notes(spec: dict, questions: list[str]) -> dict[int, str]:
    """Carried source notes about a part of the paper the spec never uses.

    `carry_source_notes` decides relevance by citation: a note is carried
    when some verified quote that round came from the same figure section.
    That is the right rule at the time -- it keeps the loop
    feature-agnostic -- but a section is coarse, and a reviewer who quotes
    one sentence of Section 6 inherits every hedge in it. Run 7 shipped
    Figure 7's note, which says no per-feature MPKI delta can be read off a
    stacked bar chart, into a spec for a register-value predictor that
    never reads that chart.

    Decided against the finished document rather than against the round
    that carried it, which is the whole reason this runs at merge time:
    whether the spec ended up using a figure is not knowable while it is
    still being repaired.

    Only a carried note with no spec pointer is eligible, on both counts.
    A reviewer-written question is *supposed* to name things the spec does
    not contain -- that is what a gap is -- and applying this rule to one
    would delete the list. A note that does carry a spec pointer was merged
    into a cluster of questions about that location, which is the spec
    claiming it whatever its own words score.
    """
    out: dict[int, str] = {}
    vocab = tokens(_spec_without_questions(spec))
    for i, entry in enumerate(questions):
        ptr, _ = _question_pointer(entry)
        if (ptr or "").startswith("/"):
            continue
        tag = _SOURCE_NOTE_TAG_RE.search(entry)
        if not tag:
            continue
        body = entry[tag.end():]
        for rx in _QUESTION_BOILERPLATE:
            body = rx.sub(" ", body)
        subject = tokens(body) - _NOTE_STOPWORDS
        if not subject:
            continue
        if len(subject & vocab) / len(subject) < _NOTE_RELEVANCE:
            out[i] = (f"it carries {tag.group(1)} from {tag.group(2).strip()}, "
                      f"which the spec draws nothing from")
    return out


def _stale_questions(spec: dict, questions: list[str]) -> dict[int, str]:
    """Questions the spec has already answered, with the reason.

    A round repairs the field a question was about and nothing withdraws the
    question, so the list grows monotonically while the spec improves. Both
    probes below are decidable against the document -- a quoted value that is
    no longer anywhere in it, and a claim about a knob's default that the
    knob contradicts -- so neither is a judgement about whether the question
    is still interesting, only about whether its premise still holds.
    """
    out: dict[int, str] = {}
    body = _spec_without_questions(spec)
    defaults = {str(q.get("name")): q.get("default")
                for q in spec.get("parameters") or []}
    for i, entry in enumerate(questions):
        text = _question_gist(entry)
        cited = [h for h in _HEX_CITATION_RE.findall(text)
                 if not re.search(rf"0x0*{h[2:].lstrip('0') or '0'}\b", body, re.I)]
        if cited:
            out[i] = (f"it quotes {cited[0]}, which appears nowhere in the "
                      f"spec any more")
            continue
        for name, val in _VALUE_CLAIM_RE.findall(text):
            if name in defaults and str(defaults[name]) != str(val):
                out[i] = (f"it says {name} is {val}; the spec declares "
                          f"{defaults[name]}")
                break
    return out


def _question_clusters(questions: list[str]) -> dict[int, list[int]]:
    """Group questions that are one question asked twice. head -> members.

    Every round re-reviews the whole spec with fresh reviewers, and
    `_append_open_question` only dedups within a pointer -- so the same
    ambiguity raised at `/algorithms/2/pseudocode` and at `/unit_tests/0`
    survives as two entries, and run 6 shipped roughly five such clusters.

    Similarity is overlap of RARE words, not of all of them. Plain Jaccard
    does not separate these: the pairs that are genuinely one question score
    between 0.16 and 0.30, and unrelated pairs score up to 0.40. What does
    separate them is sharing several words that few other questions use --
    "nan", "boxing", "opcode", "fp64" -- which is a signature of subject and
    not of phrasing.

    Normalised by the SMALLER question, because an absolute count rewards
    length: the longest entry in run 6 shared three rare words with almost
    everything and, unnormalised, absorbed four unrelated questions.

    Both bars were set against run 6's list of thirty-four. Below 0.4 the
    result stops changing, and above 0.45 the two recovery-mechanism
    questions stop merging; 0.5 was the first value tried and lost that
    pair. Nothing false merges anywhere in that range, which is the
    direction that matters -- a surviving duplicate costs a reviewer a
    second read, a wrong merge loses a question for good.

    The head is the longest member, which is deliberately the most
    informative one: a carried source note states the ambiguity, quotes the
    paper and records the duty not to resolve it by assumption, while the
    terse re-ask states only the ambiguity. Pointers from the members it
    absorbs are carried onto it, so nothing loses its way back into the spec.
    """
    gists = [_question_gist(q) for q in questions]
    toks = [tokens(g) - _QUESTION_STOPWORD_STEMS for g in gists]
    n = len(questions)
    freq: dict[str, int] = {}
    for t in toks:
        for w in t:
            freq[w] = freq.get(w, 0) + 1
    # "Rare" has to scale with the list: at a fixed cut a short list has no
    # rare words and a long one has nothing else.
    cutoff = max(3, n // 8)
    rare = [{w for w in t if freq[w] <= cutoff} for t in toks]
    # Rarity as a weight rather than a cut, for the companion rule below.
    weight = {w: math.log(n / f) for w, f in freq.items()} if n else {}
    mass = [sum(weight[w] for w in t) for t in toks]

    def linked(i: int, j: int) -> bool:
        # The same sentence at two pointers, which is what a reviewer
        # raising one ambiguity against two algorithms produces. It can
        # sit below the rare-word bar -- "How is the PC skewed for UT
        # indexing?" has four content words and two of them are common
        # across the list -- so it is settled before the bar is applied.
        if gists[i] == gists[j]:
            return True
        shared = rare[i] & rare[j]
        smaller = min(len(rare[i]), len(rare[j]))
        if smaller and len(shared) >= 3 and len(shared) / smaller >= _CLUSTER_RATIO:
            return True
        # The rare-word rule has a blind spot that grows with the thing it
        # is looking for: the more often a topic is re-asked, the less rare
        # its words are, until the topic drops out of every signature. Run
        # 7's usefulness-threshold question was asked four times, which put
        # "usefulnes" at eight occurrences against a cutoff of four, and
        # the four entries did not cluster at all. The theta pair missed
        # for the opposite reason -- both questions are short, so their
        # two genuinely shared words could not reach a floor of three.
        #
        # Weighting by rarity instead of cutting on it fixes both: a common
        # word still counts, just for less. Two shared words minimum, so a
        # single coincidence cannot link anything.
        overlap = toks[i] & toks[j]
        if len(overlap) < 2:
            return False
        smaller_mass = min(mass[i], mass[j])
        if not smaller_mass:
            return False
        return (sum(weight[w] for w in overlap) / smaller_mass
                >= _CLUSTER_WEIGHTED_RATIO)

    # Single-linkage: a question joins a cluster when it matches *any*
    # member, not only the head. The four usefulness entries pair up as
    # 9-26, 7-26, 9-27 and 1-9, so a head-only sweep collects two of them
    # and leaves the other two as their own clusters -- the same question
    # in three places instead of four.
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if find(i) != find(j) and linked(i, j):
                parent[find(j)] = find(i)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    # The head is the longest member, which is deliberately the most
    # informative one -- see the docstring above.
    return {max(m, key=lambda i: (len(gists[i]), -i)): sorted(m)
            for m in groups.values()}


def prune_open_questions(spec: dict) -> dict:
    """Drop answered questions and collapse re-asks. Mutates `spec`.

    Run at the end of the review rather than per round, on purpose. A
    question raised in round 0 and repaired in round 2 is stale only once the
    last round has run, and a question that looks like a duplicate of one the
    next round is about to withdraw should not be the entry that survives.
    Stale first for the same reason: run 6's `0xBEC` question was both stale
    and the longest member of its cluster, so deduping first would have kept
    the wrong one and dropped the question that was still live.
    """
    questions = list(spec.get("open_questions") or [])
    if not questions:
        return {"before": 0, "stale": 0, "merged": 0, "after": 0}

    stale = _stale_questions(spec, questions)
    stale.update(_off_topic_source_notes(spec, questions))
    live = [q for i, q in enumerate(questions) if i not in stale]

    clusters = _question_clusters(live)
    kept: list[str] = []
    merged = 0
    for head in sorted(clusters):
        members = clusters[head]
        merged += len(members) - 1
        # Every pointer the cluster carried, so a merged question is still
        # reachable from each place it was raised. One tag, not several:
        # `_question_pointer` reads a single leading `[...]`, and a second
        # bracket would leave the rest of the tag inside the question body
        # where the next round's dedup cannot key on it. The extras go in a
        # sentence instead.
        pointers, seen = [], set()
        for m in members:
            ptr, _ = _question_pointer(live[m])
            if ptr and ptr not in seen:
                seen.add(ptr)
                pointers.append(ptr)
        _, body = _question_pointer(live[head])
        if len(pointers) > 1:
            body = f"{body} Also raised at {', '.join(pointers[1:])}."
        kept.append(f"[{pointers[0]}] {body}" if pointers else body)

    spec["open_questions"] = kept
    return {"before": len(questions), "stale": len(stale),
            "merged": merged, "after": len(kept)}


# A knob only reaches the simulator through dse.py, which emits
# `#define SR_<NAME> <value>`. A candidate that is an English sentence produces
# uncompilable garbage, so only token-like literals may become knobs. Prose
# candidates still become open questions -- the information is kept, it just
# does not masquerade as a search dimension.
_LITERAL_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.+-]{0,31}$")


def _literal_candidates(cands) -> list[str] | None:
    if not isinstance(cands, list) or len(cands) < 2:
        return None
    vals = [str(c).strip() for c in cands]
    if not all(_LITERAL_RE.match(v) for v in vals):
        return None
    return vals if len(set(vals)) >= 2 else None


# Only these parts of the spec become code the host compiles, so only these
# can be resolved by a compile-time knob.
_PROMOTABLE_RE = re.compile(r"^/(algorithms|state)/")


def _candidate_key(cands) -> frozenset:
    """A candidate set's identity, insensitive to how it was spelled.

    `align_bit_3` and `align_bit3` are one question asked twice. Without this
    the same ambiguity, raised by four reviewers at four pointers, reads as
    four independent search dimensions and eats four slots of a budget of six.
    """
    return frozenset(
        re.sub(r"[^a-z0-9]", "", str(c).lower()) for c in (cands or ())
    )


# The fewest name tokens a parameter must have before a question that
# mentions all of them counts as being *about* that parameter.
#
# One token is too little. `num_banks` reduces to {bank} and `digest_width`
# to {digest}, and half the questions in a register-file spec say "bank" or
# "digest" in passing; refusing to mint on that would silently drop real
# ambiguities, which is the expensive direction -- a duplicate knob wastes a
# search dimension, a dropped one loses the question. Two tokens is the
# first bar at which `usefulness_threshold` is caught and nothing else in
# run 7's list is.
_KNOB_SUBJECT_MIN_TOKENS = 2


def _duplicates_existing_knob(question: str, params: list) -> str | None:
    """The existing parameter `question` is really about, if there is one.

    `promote_unsupported` already refuses an ambiguity raised *at* a
    `/parameters/` pointer, on the reasoning that it belongs in that knob's
    range rather than in a second knob whose values are range strings. That
    guard reads the pointer only, and run 7 walked straight past it: a
    reviewer raised the usefulness gate at `/algorithms/0/pseudocode`, so the
    stage minted `algorithms_0_pseudocode_variant` (`ge_zero|gt_zero`) beside
    the `usefulness_threshold` knob (default 0) that already encoded exactly
    that decision. Stage 4 sweeps both, and they disagree.

    So ask what the question is *about*, not where it was filed. A question
    naming every token of a knob's name is a question about that knob.
    """
    subject = tokens(question or "")
    if not subject:
        return None
    for p in params or []:
        if str(p.get("origin", "")).startswith("review:"):
            continue  # the minted-question pass below owns these
        sig = tokens(str(p.get("name", "")))
        if len(sig) >= _KNOB_SUBJECT_MIN_TOKENS and sig <= subject:
            return str(p.get("name"))
    return None


def _raised_against_a_parameter(rec: Record, records: list, params: list) -> str | None:
    """The knob another reviewer filed this same ambiguity against.

    `_duplicates_existing_knob` asks whether a question names every token of
    a knob's name, which needs the reviewer to have used the knob's own
    words. Run 7's escape did not: `usefulness_threshold` was already
    declared with default 0, one reviewer asked "What is the exact
    usefulness threshold value?" at `/parameters/15/default` -- correctly
    refused, an ambiguity about a knob belongs in its range -- and another
    asked "Does the usefulness gate open at >= 0 or > 0?" at
    `/algorithms/0/pseudocode`, which was minted as a second knob for the
    same decision.

    The second reviewer's filing is the evidence the first one's wording
    lacked. So compare only against the parameters *this round's reviewers
    themselves* pointed at -- a handful, not all twenty-three.

    Even scoped that way, one shared word is too loose. `num_logical_
    registers` reduces to the single token {logical}, and "What is the
    mapping of logical registers to banks?" shares it with "The default
    number of logical registers is 65" while asking something else
    entirely; the first version of this guard refused a real dimension on
    that. So the knob's name must have at least two tokens, and the two
    questions must cover all of them *between* them -- one reviewer saying
    "usefulness gate" and the other "usefulness threshold" is the pair
    naming `usefulness_threshold`, which a single word is not.
    """
    subject = tokens(rec.open_question or rec.claim or "")
    if not subject:
        return None
    for other in records or []:
        if other is rec or other.verdict != "UNSUPPORTED":
            continue
        m = re.match(r"^/parameters/(\d+)", other.pointer or "")
        if not m:
            continue
        idx = int(m.group(1))
        if idx >= len(params or []):
            continue
        name = str((params or [])[idx].get("name", ""))
        sig = tokens(name)
        if len(sig) < _KNOB_SUBJECT_MIN_TOKENS:
            continue
        theirs = tokens(other.open_question or other.claim or "")
        # The shared word has to be the knob's own, not incidental prose the
        # two questions happen to have in common -- and between them the two
        # questions have to name the whole knob.
        if (subject & theirs & sig) and sig <= (subject | theirs):
            return name
    return None


def _duplicates_minted_knob(question: str, params: list) -> str | None:
    """The already-minted knob whose question is this question, if any.

    `_candidate_key` dedups on the candidate *values*, so one ambiguity
    reduced to `ge_zero|gt_zero` by one reviewer and to `zero|positive` by
    the next reads as two dimensions. The question text is what the two have
    in common, and `_question_clusters` is already calibrated to decide when
    two questions are one. Minted knobs carry their question for this.
    """
    prior = [p for p in params or []
             if str(p.get("origin", "")).startswith("review:") and p.get("question")]
    if not prior or not (question or "").strip():
        return None
    clusters = _question_clusters([str(p["question"]) for p in prior] + [question])
    mine = len(prior)
    for members in clusters.values():
        # Whether the new question or an old one ends up the cluster head is
        # decided by length, which says nothing about which knob exists. Any
        # cluster-mate that is not the candidate itself is a knob that
        # already covers it.
        if mine not in members:
            continue
        for other in members:
            if other != mine:
                return str(prior[other].get("name"))
    return None


def _promotion_rank(
    rec: Record, consensus: dict, notes: set, flagged: set | None = None,
) -> tuple:
    """How much a knob slot is worth spending on this ambiguity.

    The cap is a real budget -- every knob is a dimension the evolver has to
    search -- and it used to be spent in arrival order, which is to say at
    random. In the sR run that handed all six slots to hash-function choices
    nobody had flagged, and dropped every one of the three ambiguities the
    source itself declares, because those records happened to arrive 12th,
    13th and 14th.

    So rank by evidence instead. An ambiguity the source explicitly refuses to
    resolve outranks one a reviewer merely noticed, and one that several
    reviewers independently reduced to the same candidate set outranks a
    one-off.

    Between those two sits code corroboration. A deterministic check that
    already flagged the same element found the hole without being asked, so an
    ambiguity there is load-bearing rather than merely noticeable: in the sR
    run the cap was spent on decay bookkeeping and a tie-break rule while
    `update`'s invented usefulness-training rule -- whose pointer
    `_check_carried_state` had flagged for reading digests nothing produces --
    got no slot at all. This key is also what keeps the ordering meaningful on
    an unmarked source, where `declared` is uniformly false and the rank
    otherwise collapses to a bare consensus count.
    """
    text = f"{rec.open_question or ''} {rec.claim or ''} {rec.why or ''}"
    # Both hedged tiers count as declared, but not equally: an UNCERTAIN note
    # names the fork and refuses to pick, while an INFERRED one has already
    # picked and only admits where the pick came from. The first is a question
    # the source is asking, the second a question it did not notice it was
    # answering, so the first gets the slot when they compete.
    cited = set(paper_markers.NOTE_ID_RE.findall(text)) & set(notes or ())
    declared = max((2 if n.startswith("U") else 1 for n in cited), default=0)
    corroborated = _element_pointer(rec.pointer) in (flagged or set())
    return (-declared, -int(corroborated),
            -consensus.get(_candidate_key(rec.enum_candidates), 0))


def promote_unsupported(
    spec: dict, records: list[Record], source_notes: set | None = None,
    findings: list[Finding] | None = None,
) -> dict:
    """Turn UNSUPPORTED verdicts into open questions and DSE enum knobs.

    An ambiguity the paper cannot settle is better searched than guessed: the
    evolver already tunes `parameters`, so a candidate list becomes a real
    dimension instead of one run's silent assumption. Promotion is deliberately
    stingy -- a knob that cannot be compiled, or that restates an existing
    parameter's range, costs DSE budget and buys nothing.

    Open questions are recorded for every UNSUPPORTED record, in the order the
    reviewers raised them. Knobs are minted afterwards, best-evidenced first,
    because only the knobs are capped.
    """
    out = copy.deepcopy(spec)
    notes = set(source_notes or ())
    # Elements the deterministic checks independently flagged this round.
    # `info` is excluded: it exists to inform a reviewer, not to rank one.
    flagged = {
        _element_pointer(f.pointer) for f in (findings or [])
        if f.severity in ("error", "warn")
    }
    # Consensus is counted over every UNSUPPORTED record, including those at
    # pointers no knob can resolve: a reviewer raising the same fork against a
    # unit test is still a second reviewer raising that fork.
    consensus: dict = {}
    for r in records:
        if r.verdict == "UNSUPPORTED" and r.enum_candidates:
            key = _candidate_key(r.enum_candidates)
            consensus[key] = consensus.get(key, 0) + 1
    existing = {p.get("name") for p in (out.get("parameters") or [])}
    # Count knobs this stage already minted in EARLIER rounds. A counter that
    # restarts at zero each round turns a cap of N into a cap of
    # N * REVIEW_ROUNDS, which is how the search space triples behind your back.
    promoted = sum(
        1 for p in (out.get("parameters") or [])
        if str(p.get("origin", "")).startswith("review:")
    )
    # Which existing knob each ambiguity is really about, decided before the
    # question is recorded so the recorded text can say so. Appending the
    # explanation afterwards does not work: `_append_open_question` dedups
    # within a pointer, so the second, more useful wording is swallowed by
    # the first.
    duplicates: dict = {}
    for r in records:
        if r.verdict != "UNSUPPORTED" or not r.enum_candidates:
            continue
        if not _PROMOTABLE_RE.match(r.pointer or ""):
            continue
        question = r.open_question or r.claim or ""
        dup = (_duplicates_existing_knob(question, out.get("parameters") or [])
               or _raised_against_a_parameter(r, records,
                                              spec.get("parameters") or []))
        if dup:
            duplicates[id(r)] = dup

    promotable: list[Record] = []
    for r in records:
        if r.verdict != "UNSUPPORTED":
            continue
        if r.open_question:
            dup = duplicates.get(id(r))
            _append_open_question(
                out,
                f"{r.open_question} This is the same decision '{dup}' already "
                f"carries; resolve it in that knob's range rather than as a "
                f"second knob." if dup else r.open_question,
                r.pointer)

        # An ambiguity about an existing knob belongs in that knob's range, not
        # in a second knob whose values are range strings.
        if (r.pointer or "").startswith("/parameters/"):
            continue
        # A knob only does anything if the host can switch on it, and the host
        # compiles behaviour -- algorithms and the state they read. An enum
        # standing in for a budget-accounting sentence or a unit test's
        # expectation emits a #define nothing branches on: it costs a real
        # search dimension and cannot change a single simulated cycle.
        if not _PROMOTABLE_RE.match(r.pointer or ""):
            if r.enum_candidates and not r.open_question:
                _append_open_question(
                    out, f"{r.claim} (candidates: "
                         + " | ".join(str(c) for c in r.enum_candidates) + ")",
                    r.pointer,
                )
            continue
        if _literal_candidates(r.enum_candidates) is None:
            if r.enum_candidates and not r.open_question:
                _append_open_question(
                    out, f"{r.claim} (candidates: "
                         + " | ".join(str(c) for c in r.enum_candidates) + ")",
                    r.pointer,
                )
            continue
        promotable.append(r)

    minted: set = set()
    for r in sorted(promotable,
                    key=lambda rec: _promotion_rank(
                        rec, consensus, notes, flagged)):
        if promoted >= C.REVIEW_MAX_PROMOTED:
            break
        key = _candidate_key(r.enum_candidates)
        if key in minted:
            # One question, asked at three sibling pointers, is one dimension.
            continue
        # Two knobs encoding one decision is worse than no knob at all: the
        # evolver sweeps both, and the candidate it settles on states the
        # decision twice, in two ways, with nothing making them agree.
        # Neither guard loses anything -- the question was recorded above,
        # and the first of them said in the question which knob already
        # carries the decision. Only the search dimension is declined.
        if id(r) in duplicates:
            continue
        question = r.open_question or r.claim or ""
        if _duplicates_minted_knob(question, out.get("parameters") or []):
            continue
        minted.add(key)
        cands = _literal_candidates(r.enum_candidates)
        promoted += 1
        name = _enum_name(r, existing)
        existing.add(name)
        out.setdefault("parameters", []).append({
            "name": name,
            "type": "enum",
            "default": str(cands[0]),
            "range": "choices: " + "|".join(str(c) for c in cands),
            "storage_impact": "None (semantic variant; storage unchanged)",
            # Provenance, and a marker the checks read: a knob that stands in
            # for an unresolved ambiguity is legitimately absent from the
            # pseudocode, so it must not trip the unreferenced-knob warning.
            "origin": "review:unsupported",
            "resolves": r.pointer,
            # The question this knob stands in for, kept so a later round can
            # tell that its own reviewer is asking it again. Without it the
            # only identity a minted knob has is its candidate values, and
            # two reviewers rarely spell one fork the same way twice.
            "question": question,
        })
    return out


def _enum_name(rec: Record, taken: set) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", (rec.pointer or rec.claim).lower()).strip("_")
    base = f"{base[:40] or 'ambiguity'}_variant"
    name, n = base, 2
    while name in taken:
        name, n = f"{base}_{n}", n + 1
    return name


def review_knobs(spec: dict) -> int:
    """How many knobs this stage has minted, across every round so far.

    Reads the provenance marker `promote_unsupported` writes, which is also
    what the spec-wide cap counts, so "did this round mint anything" and "is
    the budget spent" stay the same question.
    """
    return sum(1 for p in (spec.get("parameters") or [])
               if str(p.get("origin", "")).startswith("review:"))


# ------------------------------------------------------- regression differ


def regressions(old, new, ratio: float | None = None, path: str = "") -> list[Finding]:
    """Flag detail lost between two spec revisions.

    The failure this exists for is silent: a resolver pass rewrites a field and
    drops a guard clause or hollows a rule into a stub, and nothing downstream
    notices because the result still validates and still builds. Any loss here
    must be justified by a patch or the round is rejected.
    """
    r = C.REGRESSION_RATIO if ratio is None else ratio
    out: list[Finding] = []

    if isinstance(old, dict) and isinstance(new, dict):
        for k in old:
            child = f"{path}/{k}"
            if k not in new:
                out.append(Finding(child, "removed_key", "error",
                                   f"key '{k}' was present before the round and is gone"))
            else:
                out += regressions(old[k], new[k], r, child)
    elif isinstance(old, list) and isinstance(new, list):
        if len(new) < len(old):
            out.append(Finding(path or "/", "removed_element", "error",
                               f"array shrank from {len(old)} to {len(new)} entries"))
        for i in range(min(len(old), len(new))):
            out += regressions(old[i], new[i], r, f"{path}/{i}")
    elif isinstance(old, str) and isinstance(new, str):
        if old and len(new) < r * len(old) and not _is_test_text(path):
            out.append(Finding(path or "/", "shortened_field", "error",
                               f"field lost {100 * (1 - len(new) / len(old)):.0f}% of its "
                               f"length ({len(old)} -> {len(new)} chars)"))
    return out


def uncovered_regressions(
    old: dict, new: dict, records: list[Record]
) -> list[Finding]:
    """Regressions not explained by an applied patch at exactly that pointer.

    Exactly, not at-or-above: a patch that rewrites a whole object would
    otherwise excuse every field quietly dropped inside it, which is the
    laundering route this gate exists to close. Changing what you patched is
    allowed; losing something nested under it is not.
    """
    justified = {
        r.patch["pointer"] for r in records
        if r.patch and not r.rejected
    }
    return [f for f in regressions(old, new) if f.pointer not in justified]


# ------------------------------------------------------------ prompt bodies


def _findings_for(findings: list[Finding], unit: ReviewUnit) -> list[Finding]:
    return [f for f in findings if unit.owns(f.pointer)]


# Fields whose content is this pipeline's own invention rather than a reading
# of the paper. Marking them inline is what the prose exemption in reviewer.md
# cannot do on its own: the reviewer sees the element as JSON, and an
# unannotated `"range": "[8, 16]"` looks exactly like a transcribed fact.
_INVENTED_FIELDS = {"range": "search space set by this pipeline, not the paper"}


def _annotate_invented(element: dict) -> dict:
    value = element.get("value")
    if not isinstance(value, dict):
        return element
    marks = {k: why for k, why in _INVENTED_FIELDS.items() if k in value}
    if not marks:
        return element
    return {**element, "_not_paper_claims": marks}


def _render_unit(unit: ReviewUnit) -> str:
    return json.dumps(
        {"unit_id": unit.unit_id,
         "elements": [_annotate_invented(e) for e in unit.elements]},
        indent=2, default=str,
    )


def _render_caveats(ann: "paper_markers.Annotation") -> str:
    """The source's declared ambiguities, as a section for a reviewer prompt.

    Empty for an input that uses no marker convention, so the prompt is
    unchanged for such a source rather than carrying a hollow heading.
    """
    body = ann.render_notes()
    if not body:
        return ""
    return (
        "\n\n## Declared ambiguities in the source\n\n"
        "The source text grades its own figure transcriptions: `LITERAL` is "
        "copied from the figure, `INFERRED` is a reading of the layout that "
        "the paper never states, and `UNCERTAIN` marks a point the source "
        "says must be carried forward as an open question rather than "
        "resolved by guessing. Every `UNCERTAIN` note (`U1`, `U2`, ...) and "
        "every `INFERRED` one (`I1`, `I2`, ...) in the whole input is listed "
        "here, tagged with which it is:\n\n"
        + body
        + "\n\nBefore returning SUPPORTED, check this list. If a note bears "
        "on your claim, the verdict is UNSUPPORTED however definite the "
        "surrounding transcription looks -- including a `LITERAL` block, "
        "whose derived columns a note in the same figure section may retract. "
        "An `INFERRED` note reads as settled and is not: it states a "
        "conclusion and then says the conclusion was read off a drawing, so "
        "treat the conclusion as one candidate rather than as the answer. "
        "Give `enum_candidates` naming the readings the note lists."
    )


def _render_rejections(rejections: list[dict], unit: ReviewUnit) -> str:
    """Last round's refused patches in this unit's scope, as a prompt section.

    A reviewer that cannot see why its patch was refused proposes the same
    patch again. The sR decay-interval correction was re-derived in the round
    after the one that rejected it, same pointer, same value, same quote, and
    refused again for the same reason -- two rounds spent on a fix that was
    right about the paper and incomplete about the spec. What the gate knows
    and the reviewer does not is the refusing check's message, which names
    the other fields that have to move with it.

    Scoped by pointer rather than by unit id, because unit ids are derived
    from the partition and the partition changes between rounds.
    """
    mine = [r for r in rejections
            if r.get("value") and unit.owns(str(r.get("pointer") or ""))]
    if not mine:
        return ""
    lines = [
        f"- {r['pointer']} ({r.get('verdict')}) proposed: {r['value']}\n"
        f"  refused: {r.get('reason')}"
        + (f"\n  the check that refused it says: {r['detail']}"
           if r.get("detail") else "")
        for r in mine
    ]
    return (
        "\n\n## Patches refused last round in this scope\n\n"
        + "\n".join(lines)
        + "\n\nThese were refused by code, not by another reviewer. A patch "
        "refused for introducing a new error was incomplete, not wrong: the "
        "gate applies a round's patches as one set and reverts the set if "
        "the spec ends less self-consistent than it started. If you still "
        "believe the finding, emit EVERY edit the repair needs as its own "
        "record this round -- the parameter default, the range that bounds "
        "it, and each line of pseudocode that stores it -- so the spec is "
        "consistent once all of them are applied together. Re-proposing the "
        "same single edit will be refused the same way. If the elements you "
        "were given do not contain every field the repair needs, say which "
        "field is missing in `why` and return the verdict without a patch."
    )


def _render_findings(findings: list[Finding]) -> str:
    if not findings:
        return "(none -- the deterministic checks found nothing here)"
    return "\n".join(
        f"- [{f.severity}] {f.pointer} ({f.code}): {f.message}" for f in findings
    )


def chunk_text(text: str, limit: int) -> list[str]:
    """Split on paragraph boundaries so a long paper still fits a context."""
    if len(text) <= limit:
        return [text]
    chunks, cur = [], ""
    for para in text.split("\n\n"):
        if cur and len(cur) + len(para) + 2 > limit:
            chunks.append(cur)
            cur = para
        else:
            cur = f"{cur}\n\n{para}" if cur else para
    if cur:
        chunks.append(cur)
    return chunks


# ----------------------------------------------------------------- driver


def review_spec(
    dump, spec: dict, paper_text: str, budget_bits: int | None = None,
    feature_budget_bits: int | None = None,
) -> tuple[dict, dict]:
    """Run review rounds until the spec stops improving. Returns (spec, summary).

    Rounds matter because resolving one ambiguity spawns the next: fixing the
    scope of a mechanism immediately raises the question of what controls it,
    and a single pass answers the second by assumption. The loop stops when a
    round lands no patch and mints no knob, a round is rejected, or the cap is
    reached.
    """
    from llm import load_prompt, make_llm, submit_llm, collect_llm  # lazy: needs chia

    summary: dict = {"rounds": [], "final": {}}
    # Parsed once: the grading is a property of the source, not of a round.
    ann = paper_markers.annotate(paper_text)
    caveats = _render_caveats(ann)
    # When a round's only unfinished business is a reviewer whose call died,
    # the next round is that unit's retry -- not a re-derivation of the
    # answers every other unit already gave. Carried across iterations rather
    # than recomputed, because `partition` reads the spec and the spec cannot
    # know which backend call came back empty.
    #
    # One observed round lost a single unit to an empty response and spent the
    # next hour re-reviewing all nine to get it back, with the retry queued
    # behind seven reviews that returned the same verdicts as before.
    retry_only: set[str] | None = None
    # Carried into the next round's prompts so a reviewer sees why the gate
    # refused its last patch, instead of re-deriving it unchanged.
    prev_rejections: list[dict] = []

    summary["source_ambiguities"] = [
        {"id": n.note_id, "tier": n.tier, "where": n.where,
         "text": " ".join(n.text.split())}
        for n in ann.notes
    ]

    for rnd in range(C.REVIEW_ROUNDS):
        findings = spec_checks.run_checks(spec, budget_bits, feature_budget_bits)
        units = partition(spec)
        retrying = retry_only
        if retrying:
            scoped = [u for u in units if u.unit_id in retrying]
            # A unit id can legitimately vanish between rounds: minted knobs
            # change which unit owns which parameter, and `orphan` exists only
            # while something is unreferenced. Falling back to the full
            # partition is the safe direction to fail -- reviewing too much
            # costs time, reviewing nothing would let the run report a spec as
            # fully reviewed when the failed unit never was.
            units = scoped or units

        # One fresh session per unit. Reviewers never see the distiller's
        # transcript: independence from its reasoning is the whole point.
        jobs = []
        for unit in units:
            prompt = load_prompt(
                "reviewer.md",
                feature_name=C.FEATURE_NAME,
                unit_id=unit.unit_id,
                unit_kind=unit.kind,
            ) + (
                f"\n\n## Elements under review\n\n```json\n{_render_unit(unit)}\n```"
                f"\n\n## Deterministic findings in this scope\n\n"
                f"{_render_findings(_findings_for(findings, unit))}"
                f"{_render_rejections(prev_rejections, unit)}"
                f"{caveats}"
                f"\n\n## The paper\n\n{paper_text}"
            )
            llm = make_llm(C.LLM_BACKEND, [], resume=False)
            jobs.append((unit.unit_id, llm, submit_llm(llm, prompt, [])))

        # Coverage reads the whole spec against the whole paper, so it is the
        # most expensive single call in a round and the least unit-scoped.
        # A retry round re-runs it only if coverage is itself what failed.
        chunks = (
            [] if retrying and not any(u.startswith("coverage") for u in retrying)
            else chunk_text(paper_text, C.COVERAGE_CHUNK_CHARS)
        )
        for ci, chunk in enumerate(chunks):
            prompt = load_prompt(
                "coverage.md", feature_name=C.FEATURE_NAME
            ) + (
                f"\n\n## The spec\n\n```json\n{json.dumps(spec, indent=2)}\n```"
                f"{caveats}"
                f"\n\n## Paper section under review\n\n{chunk}"
            )
            llm = make_llm(C.LLM_BACKEND, [], resume=False)
            jobs.append((f"coverage" if ci == 0 else f"coverage:{ci}",
                         llm, submit_llm(llm, prompt, [])))

        records: list[Record] = []
        parse_errors: list[str] = []
        failed_units: list[str] = []
        quota_exhausted = False
        for unit_id, llm, ref in jobs:
            try:
                resp = collect_llm(ref, llm)
            # SystemExit, not just Exception: collect_llm signals a backend
            # failure by raising SystemExit, which derives from BaseException
            # and sails straight through `except Exception`. Catching only
            # Exception let one exhausted reviewer kill the entire job and skip
            # every bit of the partial-review handling below.
            except (Exception, SystemExit) as e:
                parse_errors.append(f"{unit_id}: backend call failed ({e})")
                failed_units.append(unit_id)
                if _is_quota_error(e):
                    # Every later call will fail the same way. Finish this
                    # round with what came back, then stop: firing another
                    # wave at an exhausted account buys nothing.
                    quota_exhausted = True
                continue
            dump.llm(f"review_r{rnd}_{_slug(unit_id)}", resp)
            recs, errs = parse_records(unit_id, resp.result)
            # Coverage runs against a chunk, so normalize its id for scoping.
            for r in recs:
                if r.unit_id.startswith("coverage"):
                    r.unit_id = "coverage"
            records += recs
            parse_errors += errs

        verify_evidence(records, paper_text, ann)
        candidate, rejections = apply_patches(
            spec, records, units, findings, budget_bits, feature_budget_bits)
        candidate = promote_unsupported(
            candidate, records, {n.note_id for n in ann.notes}, findings)
        carried = carry_source_notes(candidate, records, ann)

        new_findings = spec_checks.run_checks(
            candidate, budget_bits, feature_budget_bits)
        uncovered = uncovered_regressions(spec, candidate, records)
        schema_errs = _schema_errors(candidate)

        landed_inconsistent = [
            r for r in records
            if r.verdict == "INCONSISTENT" and r.patch and not r.rejected
        ]
        errors_before = spec_checks.severity_counts(findings)["error"]
        errors_after = spec_checks.severity_counts(new_findings)["error"]

        round_log = {
            "round": rnd,
            "units": [u.unit_id for u in units],
            "failed_units": failed_units,
            "quota_exhausted": quota_exhausted,
            "records": [r.as_dict() for r in records],
            "rejections": rejections,
            "parse_errors": parse_errors,
            "checks_before": spec_checks.severity_counts(findings),
            "checks_after": spec_checks.severity_counts(new_findings),
            "inconsistent_patches": len(landed_inconsistent),
            "hedged_evidence": sum(
                1 for r in records if r.tier in paper_markers.HEDGED_TIERS
            ),
            "carried_source_notes": carried,
            "regressions": [f.as_dict() for f in uncovered],
            "schema_errors": schema_errs,
            "verdicts": _verdict_counts(records),
        }

        reject_reason = None
        if schema_errs:
            reject_reason = "patched spec failed schema validation"
        elif uncovered:
            reject_reason = f"{len(uncovered)} unjustified regression(s)"
        elif spec_checks.is_worse(findings, new_findings):
            reject_reason = "deterministic checks got worse"
        elif landed_inconsistent and errors_after >= errors_before:
            # An INCONSISTENT patch carries no quote, so the only thing
            # vouching for it is the contradiction disappearing. If the error
            # count did not fall, the patch rewrote the spec on no authority
            # at all and must not stand.
            reject_reason = (
                f"{len(landed_inconsistent)} INCONSISTENT patch(es) landed but "
                f"the error count did not fall ({errors_before} -> "
                f"{errors_after})"
            )

        # What this round actually accomplished: a patch that rewrote a field,
        # or a knob minted for an ambiguity. A later round can build on
        # either. Appending an open question cannot be progress -- and it is
        # the one thing EVERY round does, once per UNSUPPORTED record, so the
        # old `candidate != spec` test never went False and the round cap
        # rather than convergence ended every run. One observed round cost an
        # hour, landed no patch, left all three check counts identical, and
        # added ten lines of prose; the loop then started another.
        #
        # The knob cap is spec-wide, so `knobs_minted` is permanently zero
        # once it is spent. From that point the loop stops at the first round
        # that lands no patch, which is what this function has always claimed
        # to do.
        patched = sum(1 for r in records if r.patch and not r.rejected)
        minted = review_knobs(candidate) - review_knobs(spec)

        if reject_reason:
            stop_reason = f"round rejected: {reject_reason}"
        elif quota_exhausted:
            stop_reason = "backend quota exhausted"
        elif not patched and not minted and not failed_units:
            # A failed unit is not convergence: it was never reviewed, so the
            # next round is its retry.
            stop_reason = "converged: no patch landed and no knob was minted"
        else:
            stop_reason = None

        round_log["accepted"] = reject_reason is None
        round_log["reject_reason"] = reject_reason
        round_log["patches_landed"] = patched
        round_log["knobs_minted"] = minted
        round_log["stop_reason"] = stop_reason
        round_log["retry_of"] = sorted(retrying) if retrying else None
        dump.json(f"review_round{rnd}.json", round_log)
        summary["rounds"].append({k: round_log[k] for k in (
            "round", "units", "failed_units", "quota_exhausted",
            "checks_before", "checks_after", "inconsistent_patches",
            "hedged_evidence", "carried_source_notes",
            "verdicts", "accepted", "reject_reason",
            "patches_landed", "knobs_minted", "stop_reason", "retry_of",
        )})

        # A rejected round is discarded, not adopted: its candidate never
        # becomes the spec.
        if reject_reason:
            break
        spec = candidate
        if stop_reason:
            break
        prev_rejections = rejections

        # The next round is a scoped retry only when nothing else is left to
        # do. A round that landed a patch or minted a knob changed the spec
        # under every unit, so the round after it has to be a full one.
        retry_only = (
            set(failed_units) if failed_units and not patched and not minted
            else None
        )

    # A unit whose reviewer died was never checked, and a spec that reaches the
    # integration agents unmarked looks identical either way. Rolling the round
    # back would be worse -- it would discard evidence-verified fixes because of
    # an unrelated backend failure -- so the patches stand and the gap is stated.
    unreviewed = sorted({
        u for r in summary["rounds"] for u in r["failed_units"]
        if u not in {
            v for r2 in summary["rounds"] if not r2["failed_units"]
            for v in r2["units"]
        }
    })
    # Last, once no further round can repair a field or re-ask a question.
    pruned = prune_open_questions(spec)
    final_checks = spec_checks.run_checks(spec, budget_bits, feature_budget_bits)
    summary["final"] = {
        "checks": [f.as_dict() for f in final_checks],
        "errors": spec_checks.severity_counts(final_checks)["error"],
        "open_questions": len(spec.get("open_questions") or []),
        "questions_pruned": pruned,
        "parameters": len(spec.get("parameters") or []),
        "complete": not unreviewed,
        "unreviewed_units": unreviewed,
    }
    if unreviewed:
        print(
            f"WARNING: spec review is INCOMPLETE. {len(unreviewed)} unit(s) were "
            f"never reviewed because their backend call failed: "
            + ", ".join(unreviewed)
            + ".\nThe spec carries only the fixes from the units that did run."
        )
    return spec, summary


def _schema_errors(spec: dict) -> list[str]:
    import helpers
    _, errs = helpers.validate_spec(json.dumps(spec))
    return [helpers.truncate(e) for e in errs]


def _verdict_counts(records: list[Record]) -> dict:
    out: dict = {}
    for r in records:
        out[r.verdict] = out.get(r.verdict, 0) + 1
    return out


_QUOTA_RE = re.compile(
    r"rate.?limit|resource_exhausted|quota|429|too many requests", re.I
)


def _is_quota_error(exc: Exception) -> bool:
    """Is this the kind of failure that will repeat on every later call?

    A quota wall is not a flaky reviewer: the remaining fan-out and every
    subsequent round will hit the same error, so the loop should stop rather
    than spend wall-clock proving it.
    """
    return bool(_QUOTA_RE.search(f"{type(exc).__name__} {exc}"))


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")[:48] or "unit"
