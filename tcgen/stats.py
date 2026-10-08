"""Statistics for comparing conditions over independent repetitions."""

import statistics

from tcgen import store

ALPHA = 0.05


def mean_sd(values):
    values = list(values)
    if not values:
        return None, None
    return statistics.fmean(values), (statistics.stdev(values) if len(values) > 1 else 0.0)


def a12(x, y):
    """Vargha-Delaney effect size: probability that a value of x exceeds one of y.

    0.5 means no difference. Ties count half.
    """
    greater = sum(1 for a in x for b in y if a > b)
    equal = sum(1 for a in x for b in y if a == b)
    return (greater + 0.5 * equal) / (len(x) * len(y))


def holm(p_values):
    """Holm step-down adjustment. Takes and returns {name: p}."""
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    adjusted, running = {}, 0.0
    for rank, (name, p) in enumerate(ordered):
        running = max(running, min(1.0, (len(ordered) - rank) * p))
        adjusted[name] = running
    return adjusted


def wilcoxon_p(x, y):
    """Paired comparison (Wilcoxon signed-rank). 1.0 when every pair is equal."""
    from scipy.stats import wilcoxon

    if all(a == b for a, b in zip(x, y)):
        return 1.0
    return float(wilcoxon(x, y).pvalue)


def mann_whitney_p(x, y):
    """Unpaired comparison (Mann-Whitney U)."""
    from scipy.stats import mannwhitneyu

    return float(mannwhitneyu(x, y, alternative="two-sided").pvalue)


def compare(conn, system, metric, first, second, paired):
    """Compare two conditions on one metric. Paired comparisons match repetitions."""
    a = store.metric_values(conn, system, first, metric)
    b = store.metric_values(conn, system, second, metric)
    if paired:
        shared = sorted(set(a) & set(b))
        x, y = [a[r] for r in shared], [b[r] for r in shared]
    else:
        x, y = list(a.values()), list(b.values())
    if len(x) < 2 or len(y) < 2:
        return None
    return {
        "metric": metric,
        "first": first,
        "second": second,
        "n": (len(x), len(y)),
        "mean_first": statistics.fmean(x),
        "mean_second": statistics.fmean(y),
        "p": wilcoxon_p(x, y) if paired else mann_whitney_p(x, y),
        "a12": a12(x, y),
    }
