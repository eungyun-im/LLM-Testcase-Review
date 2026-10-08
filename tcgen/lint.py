"""Deterministic checks on candidate test cases. No LLM calls."""


def check_schema(cases):
    # TODO: required fields, types, expected in EXPECTED_VALUES
    raise NotImplementedError


def check_traceability(cases, spec):
    # TODO: every req_id exists in the spec
    raise NotImplementedError


def check_duplicates(cases):
    # TODO: same inputs and expected result
    raise NotImplementedError


def check_boundary_coverage(cases, spec):
    # TODO: for each declared boundary, a case at value - step, value, value + step
    raise NotImplementedError


def check_range(cases, spec):
    # TODO: inputs within declared min/max, unless the case targets invalid input
    raise NotImplementedError
