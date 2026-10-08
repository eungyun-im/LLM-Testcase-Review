import pytest

# TODO: each check gets a passing fixture and a failing fixture.


@pytest.mark.skip(reason="not implemented: schema check")
def test_schema_rejects_unknown_expected():
    pass


@pytest.mark.skip(reason="not implemented: traceability check")
def test_traceability_flags_unknown_requirement():
    pass


@pytest.mark.skip(reason="not implemented: duplicate check")
def test_duplicates_are_flagged():
    pass


@pytest.mark.skip(reason="not implemented: boundary coverage check")
def test_missing_boundary_is_flagged():
    pass
