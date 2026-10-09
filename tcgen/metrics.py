"""Execution-based metrics: error rate, boundary recall, defect detection rate.

Every number here comes from running tests or inspecting their inputs. No
human rating is involved.
"""

TOLERANCE = 1e-6


def output_of(decide, test):
    """Output of an implementation for a test's inputs, as a string."""
    try:
        return decide(*test.inputs).value
    except Exception:
        return "ERROR"


def split_valid(tests, reference):
    """Separate tests whose expected result matches the reference from the wrong ones."""
    valid, wrong = [], []
    for test in tests:
        (valid if output_of(reference, test) == test.expected else wrong).append(test)
    return valid, wrong


def error_rate(tests, reference):
    """Share of generated tests whose expected result contradicts the reference."""
    if not tests:
        return 0.0
    _, wrong = split_valid(tests, reference)
    return len(wrong) / len(tests)


def _matches(value, target):
    return value is not None and abs(value - target) <= TOLERANCE


def _satisfies(test, conditions):
    for name, rule in conditions:
        value = test.value_of(name)
        if value is None:
            return False
        if "min" in rule and value < rule["min"] - TOLERANCE:
            return False
        if "max" in rule and value > rule["max"] + TOLERANCE:
            return False
    return True


def boundary_coverage(tests, spec):
    """Return (covered_simple, covered_strict, all_points).

    simple: some test has the point's value in that input.
    strict: that test's other inputs also let the boundary show in the output.
    """
    points = spec.points()
    simple, strict = [], []
    for point in points:
        hits = [t for t in tests if _matches(t.value_of(point.input), point.value)]
        if hits:
            simple.append(point)
        if any(_satisfies(t, point.strict_when) for t in hits):
            strict.append(point)
    return simple, strict, points


def boundary_recall(tests, spec):
    """Return (simple recall, strict recall)."""
    simple, strict, points = boundary_coverage(tests, spec)
    return len(simple) / len(points), len(strict) / len(points)


def detects(tests, defect):
    """True when at least one test fails on the defect version."""
    return any(output_of(defect, test) != test.expected for test in tests)


def detection(valid_tests, versions, excluded=()):
    """Run valid tests on every defect version.

    versions: mapping of ID to a decide function. excluded: IDs judged
    equivalent, removed from the denominator. Returns (rate, {id: detected}).
    """
    considered = {vid: decide for vid, decide in versions.items() if vid not in set(excluded)}
    detected = {vid: detects(valid_tests, decide) for vid, decide in considered.items()}
    rate = sum(detected.values()) / len(detected) if detected else 0.0
    return rate, detected


def partition_coverage(tests, spec):
    """Share of the input classes of the spec that at least one test falls into."""
    if not spec.partitions:
        return 0.0
    covered = {spec.partition_of(test) for test in tests}
    return sum(p["id"] in covered for p in spec.partitions) / len(spec.partitions)
