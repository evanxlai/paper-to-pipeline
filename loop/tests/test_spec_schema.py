"""Tests for `spec/feature_spec.schema.json` as a gate on what the distiller
emits, rather than on what the loop then does with it.

There is one thing here the schema is uniquely able to stop. The distiller is
handed the schema inline in its prompt -- it has to be, or the document comes
back shaped like something else -- and a model given a schema and asked for an
instance will copy the schema's own metadata into the instance. Twelve of the
sixteen runs under `out/` did exactly that, carrying `$schema`, `$id`, `title`,
`description` or `type` into the artifact the integration agents read.

No deterministic check can catch that honestly: a spec with extra top-level
keys is not self-contradictory, it is just carrying furniture. Refusing
unknown keys at the schema is a one-line guard, and it is where the refusal
belongs.
"""

import json

import pytest

import constants as C
import helpers


@pytest.fixture
def valid_spec():
    return json.loads((C.REPO_ROOT / "spec" / "sr.paper_only.json").read_text())


def test_the_checked_in_spec_validates(valid_spec):
    _, errs = helpers.validate_spec(json.dumps(valid_spec))
    assert errs == []


@pytest.mark.parametrize("leaked", ["$schema", "$id", "title", "description",
                                    "type"])
def test_a_schema_key_copied_into_the_instance_is_refused(valid_spec, leaked):
    """The exact five keys the runs actually leaked."""
    valid_spec[leaked] = "https://example.invalid/whatever"
    _, errs = helpers.validate_spec(json.dumps(valid_spec))
    assert errs, f"{leaked} was accepted into the instance"
    assert any(leaked in e for e in errs)


def test_an_invented_top_level_field_is_refused(valid_spec):
    """Not only the schema's own keys. A field nothing downstream reads is a
    field nothing downstream reads, however plausible it sounds."""
    valid_spec["implementation_notes"] = "see the paper"
    _, errs = helpers.validate_spec(json.dumps(valid_spec))
    assert errs


def test_open_questions_is_still_optional_and_allowed(valid_spec):
    """`additionalProperties: false` refuses what the schema does not list,
    and `open_questions` is listed but not required -- the reviewer adds it.
    A guard that took it out with the rest would break the stage it protects.
    """
    valid_spec.pop("open_questions", None)
    assert helpers.validate_spec(json.dumps(valid_spec))[1] == []
    valid_spec["open_questions"] = ["is this still open?"]
    assert helpers.validate_spec(json.dumps(valid_spec))[1] == []
