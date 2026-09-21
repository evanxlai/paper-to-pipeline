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
import re
from dataclasses import dataclass, field

import constants as C
import paper_markers
import spec_checks
from spec_checks import Finding, tokens

# A quote shorter than this matches too much text to be evidence of anything.
MIN_QUOTE_CHARS = 12

# Top-level spec keys that belong to the "global" review unit: cross-cutting
# claims that no single algorithm owns.
_GLOBAL_KEYS = ("summary", "source", "host_interfaces", "resource_accounting")


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

    @property
    def prefixes(self) -> list[str]:
        return [e["pointer"] for e in self.elements]

    def owns(self, pointer: str) -> bool:
        return any(
            pointer == p or pointer.startswith(p + "/") for p in self.prefixes
        )


def _elem(spec, pointer):
    return {"pointer": pointer, "value": ptr_get(spec, pointer)}


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

        units.append(ReviewUnit(f"algo:{a.get('name', ai)}", "algorithm", elements))

    globals_ = [_elem(spec, f"/{k}") for k in _GLOBAL_KEYS if k in spec]
    if globals_:
        units.append(ReviewUnit("global", "global", globals_))

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
        units.append(
            ReviewUnit(f"{a.unit_id}+{b.unit_id}", "algorithm", a.elements + b.elements)
        )
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
        if not r.open_question:
            r.open_question = (
                demote if demote.startswith(r.claim) else f"{r.claim} ({demote})"
            )


def carry_uncertainties(
    spec: dict, records: list[Record], annotation: "paper_markers.Annotation",
) -> int:
    """Record every declared ambiguity the spec actually leans on.

    The source's own convention says an UNCERTAIN note must be "carried
    forward as an open question", not resolved by guessing. Leaving that to a
    model is what failed: three rounds of reviewers never mentioned the notes,
    because nothing pointed at them. Code can do it instead, and does it here.

    Relevance is decided by citation, not by topic modelling, which keeps the
    rule feature-agnostic: a note is carried when some verified quote this
    round was drawn from the same figure section. A spec that never cites
    Figure 4 does not inherit Figure 4's ambiguities. The unit is the section
    rather than the paragraph on purpose -- an UNCERTAIN note routinely
    retracts a number printed above it inside a LITERAL block, as Figure 6(b)
    does to a whole derived column.
    """
    cited: set[tuple[str, str]] = set()
    for r in records:
        span = annotation.locate(r.quote or "")
        if span is not None and span.block:
            cited.add((span.block, span.section))
    carried = 0
    for note in annotation.notes:
        if (note.block, note.section) not in cited:
            continue
        before = len(spec.get("open_questions") or [])
        _append_open_question(
            spec,
            f"[source {note.note_id}: {note.where}] the input marks this "
            f"UNCERTAIN, so it must not be resolved by assumption: "
            + " ".join(note.text.split()),
        )
        carried += len(spec.get("open_questions") or []) > before
    return carried


# ------------------------------------------------------------ patch merging


def _self_consistency_scope(findings: list[Finding] | None) -> set[str]:
    """Pointers a self-consistency check actually named this round."""
    return {f.pointer for f in (findings or [])
            if f.code in _SELF_CONSISTENCY_CODES}


def apply_patches(
    spec: dict, records: list[Record], units: list[ReviewUnit],
    findings: list[Finding] | None = None,
) -> tuple[dict, list[dict]]:
    """Apply surviving patches deterministically. Returns (new_spec, rejections)."""
    by_unit = {u.unit_id: u for u in units}
    inconsistent_scope = _self_consistency_scope(findings)
    rejections: list[dict] = []
    candidates: list[Record] = []

    def reject(rec: Record, why: str) -> None:
        rec.rejected = why
        rejections.append({"unit": rec.unit_id, "pointer": rec.pointer,
                           "verdict": rec.verdict, "reason": why})

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
            # exactly the pointers a deterministic check flagged. Without this
            # the verdict degrades into "rewrite anything, cite nothing".
            target = str(r.patch.get("pointer") or r.pointer)
            if not any(target == p or target.startswith(p + "/")
                       or p.startswith(target + "/")
                       for p in inconsistent_scope):
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
                    _append_open_question(
                        spec, f"Reviewer wanted to shorten {pointer}: {r.claim}"
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

    new_spec = copy.deepcopy(spec)
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

    # Adds that append to the same array must not renumber each other, so
    # apply replaces first and adds last.
    for r in sorted(applied, key=lambda x: (x.patch["op"] == "add", x.patch["pointer"])):
        try:
            ptr_apply(new_spec, r.patch["pointer"], r.patch["value"], r.patch["op"])
        except Exception as e:  # malformed pointer, bad index, ...
            reject(r, f"patch failed to apply: {e}")

    for c in conflicts:
        _append_open_question(new_spec, c)
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


def _promotion_rank(rec: Record, consensus: dict, notes: set) -> tuple:
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
    """
    text = f"{rec.open_question or ''} {rec.claim or ''} {rec.why or ''}"
    declared = bool(notes and re.findall(r"\bU\d+\b", text) and
                    set(re.findall(r"\bU\d+\b", text)) & notes)
    return (-int(declared), -consensus.get(_candidate_key(rec.enum_candidates), 0))


def promote_unsupported(
    spec: dict, records: list[Record], source_notes: set | None = None,
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
    promotable: list[Record] = []
    for r in records:
        if r.verdict != "UNSUPPORTED":
            continue
        if r.open_question:
            _append_open_question(out, r.open_question, r.pointer)

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
                    key=lambda rec: _promotion_rank(rec, consensus, notes)):
        if promoted >= C.REVIEW_MAX_PROMOTED:
            break
        key = _candidate_key(r.enum_candidates)
        if key in minted:
            # One question, asked at three sibling pointers, is one dimension.
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
        })
    return out


def _enum_name(rec: Record, taken: set) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", (rec.pointer or rec.claim).lower()).strip("_")
    base = f"{base[:40] or 'ambiguity'}_variant"
    name, n = base, 2
    while name in taken:
        name, n = f"{base}_{n}", n + 1
    return name


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


def _render_unit(unit: ReviewUnit) -> str:
    return json.dumps(
        {"unit_id": unit.unit_id, "elements": unit.elements}, indent=2, default=str
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
        "resolved by guessing. Every `UNCERTAIN` note in the whole input is "
        "listed here:\n\n"
        + body
        + "\n\nBefore returning SUPPORTED, check this list. If a note bears "
        "on your claim, the verdict is UNSUPPORTED however definite the "
        "surrounding transcription looks -- including a `LITERAL` block, "
        "whose derived columns a note in the same figure section may retract. "
        "Give `enum_candidates` naming the readings the note lists."
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
    dump, spec: dict, paper_text: str, budget_bits: int | None = None
) -> tuple[dict, dict]:
    """Run review rounds until the spec stops changing. Returns (spec, summary).

    Rounds matter because resolving one ambiguity spawns the next: fixing the
    scope of a mechanism immediately raises the question of what controls it,
    and a single pass answers the second by assumption. The loop stops when a
    round lands no patches, a round is rejected, or the cap is reached.
    """
    from llm import load_prompt, make_llm, submit_llm, collect_llm  # lazy: needs chia

    summary: dict = {"rounds": [], "final": {}}
    # Parsed once: the grading is a property of the source, not of a round.
    ann = paper_markers.annotate(paper_text)
    caveats = _render_caveats(ann)
    summary["source_ambiguities"] = [
        {"id": n.note_id, "where": n.where, "text": " ".join(n.text.split())}
        for n in ann.notes
    ]

    for rnd in range(C.REVIEW_ROUNDS):
        findings = spec_checks.run_checks(spec, budget_bits)
        units = partition(spec)

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
                f"{caveats}"
                f"\n\n## The paper\n\n{paper_text}"
            )
            llm = make_llm(C.LLM_BACKEND, [], resume=False)
            jobs.append((unit.unit_id, llm, submit_llm(llm, prompt, [])))

        for ci, chunk in enumerate(chunk_text(paper_text, C.COVERAGE_CHUNK_CHARS)):
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
        candidate, rejections = apply_patches(spec, records, units, findings)
        candidate = promote_unsupported(
            candidate, records, {n.note_id for n in ann.notes})
        carried = carry_uncertainties(candidate, records, ann)

        new_findings = spec_checks.run_checks(candidate, budget_bits)
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
            "carried_uncertainties": carried,
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

        round_log["accepted"] = reject_reason is None
        round_log["reject_reason"] = reject_reason
        dump.json(f"review_round{rnd}.json", round_log)
        summary["rounds"].append({k: round_log[k] for k in (
            "round", "units", "failed_units", "quota_exhausted",
            "checks_before", "checks_after", "inconsistent_patches",
            "hedged_evidence", "carried_uncertainties",
            "verdicts", "accepted", "reject_reason"
        )})

        if reject_reason:
            break
        changed = candidate != spec
        spec = candidate
        if quota_exhausted or (not changed and not failed_units):
            break

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
    final_checks = spec_checks.run_checks(spec, budget_bits)
    summary["final"] = {
        "checks": [f.as_dict() for f in final_checks],
        "errors": spec_checks.severity_counts(final_checks)["error"],
        "open_questions": len(spec.get("open_questions") or []),
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
