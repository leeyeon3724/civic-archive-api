import pytest
from conftest import StubResult
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# P11-7 regression: JSONB field max nesting depth guard
# ---------------------------------------------------------------------------


def test_canonical_json_value_rejects_excessively_nested_input(segments_module):
    """P11-7: _canonical_json_value must raise 400 when nesting exceeds _MAX_CANONICAL_JSON_DEPTH."""
    limit = segments_module._MAX_CANONICAL_JSON_DEPTH
    nested: object = "leaf"
    for _ in range(limit + 2):
        nested = {"child": nested}

    with pytest.raises(HTTPException) as exc_info:
        segments_module.normalize_segment({"council": "A", "tag": [nested]})
    assert exc_info.value.status_code == 400


def test_canonical_json_value_accepts_realistic_nesting(segments_module):
    """P11-7: realistic nesting depth (5 levels) must not raise."""
    nested: object = "leaf"
    for _ in range(5):
        nested = {"child": nested}

    result = segments_module.normalize_segment({"council": "A", "tag": [nested]})
    assert result["council"] == "A"


# ---------------------------------------------------------------------------
# P11-4 regression: canonical vs legacy hash inequality invariant
# ---------------------------------------------------------------------------


def test_normalize_segment_generates_stable_dedupe_hash(segments_module):
    first = segments_module.normalize_segment(
        {
            "council": "A",
            "committee": "Budget",
            "tag": [{"k": "v"}],
            "meeting_date": "2026-02-17",
        }
    )
    second = segments_module.normalize_segment(
        {
            "meeting_date": "2026-02-17",
            "tag": [{"k": "v"}],
            "committee": "Budget",
            "council": "A",
        }
    )

    assert isinstance(first["dedupe_hash"], str)
    assert len(first["dedupe_hash"]) == 64
    assert first["dedupe_hash"] == second["dedupe_hash"]


def test_insert_segments_counts_only_non_conflict_rows(segments_module, make_connection_provider):
    def handler(_statement, _params):
        return StubResult(rows=[{"inserted": 2}])

    connection_provider, _ = make_connection_provider(handler)
    inserted = segments_module.insert_segments(
        [{"council": "A"}, {"council": "A"}, {"council": "B"}],
        connection_provider=connection_provider,
    )
    assert inserted == 2


def test_normalize_segment_blank_and_none_optional_strings_share_dedupe_hash(segments_module):
    blank_payload = {
        "council": "A",
        "committee": "",
        "session": "",
        "meeting_no": None,
        "meeting_date": "2026-02-17",
        "content": "",
        "summary": "",
        "subject": "",
        "party": "",
        "constituency": "",
        "department": "",
    }
    none_payload = {
        "council": "A",
        "committee": None,
        "session": None,
        "meeting_no": None,
        "meeting_date": "2026-02-17",
        "content": None,
        "summary": None,
        "subject": None,
        "party": None,
        "constituency": None,
        "department": None,
    }

    blank_normalized = segments_module.normalize_segment(blank_payload)
    none_normalized = segments_module.normalize_segment(none_payload)

    assert blank_normalized["dedupe_hash"] == none_normalized["dedupe_hash"]
    assert blank_normalized["dedupe_hash_legacy"] == none_normalized["dedupe_hash_legacy"]
    assert blank_normalized["dedupe_hash_legacy"] is not None


def test_canonical_and_legacy_dedupe_hash_differ_when_optional_fields_are_none(segments_module):
    """P11-4 invariant: when any LEGACY_EMPTY_STRING_FIELDS are None, the canonical hash
    (which encodes None as JSON null) must differ from the legacy hash (which substitutes "").
    This guarantees the NOT EXISTS legacy fallback path is genuinely distinct from the
    canonical path — preventing false deduplication when both hashes happen to collide."""
    normalized = segments_module.normalize_segment(
        {"council": "A", "committee": None, "meeting_date": "2026-02-17"}
    )
    assert normalized["dedupe_hash"] != normalized["dedupe_hash_legacy"], (
        "canonical and legacy hashes must differ when optional fields are None"
    )


def test_canonical_and_legacy_dedupe_hash_equal_when_no_optional_fields_are_none(segments_module):
    """P11-4 invariant: when all LEGACY_EMPTY_STRING_FIELDS have non-None values, the legacy
    hash substitution has no effect — canonical and legacy hashes must be identical."""
    normalized = segments_module.normalize_segment(
        {
            "council": "A",
            "committee": "Budget",
            "session": "301",
            "meeting_date": "2026-02-17",
            "content": "some text",
            "summary": "brief",
            "subject": "finance",
            "party": "democratic",
            "constituency": "downtown",
            "department": "treasury",
        }
    )
    assert normalized["dedupe_hash"] == normalized["dedupe_hash_legacy"], (
        "canonical and legacy hashes must be equal when no optional fields are None"
    )
