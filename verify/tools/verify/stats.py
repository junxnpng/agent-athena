"""Small-sample statistics, stdlib only.

Clopper-Pearson exact binomial bounds, Cohen's kappa, a percentile bootstrap
driven by `random.Random(seed)`, and the Chapman capture-recapture estimator.
The exact bounds invert the binomial CDF by bisection instead of a beta quantile.
"""
from __future__ import annotations

import collections
import dataclasses
import math
import random
from typing import Callable, Hashable, Sequence

_BISECT_STEPS = 200


def _check(k: int, n: int, confidence: float) -> None:
    if n < 1 or not 0 <= k <= n:
        raise ValueError(f"need 0 <= k <= n and n >= 1 (k={k}, n={n})")
    if not 0 < confidence < 1:
        raise ValueError(f"confidence must be in (0, 1), got {confidence}")


def binom_cdf(k: int, n: int, p: float) -> float:
    """P(X <= k) for X ~ Binomial(n, p)."""
    if k < 0:
        return 0.0
    if k >= n or p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 0.0
    lp, lq = math.log(p), math.log1p(-p)
    return min(1.0, sum(math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
                                 + i * lp + (n - i) * lq) for i in range(k + 1)))


def _bisect(f: Callable[[float], float], target: float, increasing: bool) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(_BISECT_STEPS):
        mid = (lo + hi) / 2
        if (f(mid) < target) == increasing:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def upper_bound(k: int, n: int, confidence: float = 0.95) -> float:
    """One-sided exact upper bound: the p at which P(X <= k) = 1 - confidence."""
    _check(k, n, confidence)
    if k == n:
        return 1.0
    return _bisect(lambda p: binom_cdf(k, n, p), 1 - confidence, increasing=False)


def lower_bound(k: int, n: int, confidence: float = 0.95) -> float:
    """One-sided exact lower bound: the p at which P(X >= k) = 1 - confidence."""
    _check(k, n, confidence)
    if k == 0:
        return 0.0
    return _bisect(lambda p: 1 - binom_cdf(k - 1, n, p), 1 - confidence, increasing=True)


def clopper_pearson(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Two-sided exact interval, (1 - confidence) / 2 in each tail."""
    _check(k, n, confidence)
    tail = 1 - (1 - confidence) / 2
    return lower_bound(k, n, tail), upper_bound(k, n, tail)


def cohen_kappa(a: Sequence[Hashable], b: Sequence[Hashable]) -> float | None:
    """Kappa of two raters over paired items; None when chance agreement is 1."""
    if len(a) != len(b):
        raise ValueError(f"kappa needs paired labels ({len(a)} vs {len(b)})")
    if not a:
        raise ValueError("kappa needs at least one paired item")
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = collections.Counter(a), collections.Counter(b)
    chance = sum(ca[label] * cb[label] for label in ca) / (n * n)
    if chance >= 1.0:
        return None
    return (observed - chance) / (1 - chance)


@dataclasses.dataclass(frozen=True)
class Bootstrap:
    point: float | None
    lo: float | None
    hi: float | None
    n_resamples: int
    n_valid: int          # resamples whose statistic was defined
    seed: int
    confidence: float


def _percentile(sorted_values: list[float], q: float) -> float:
    pos = q * (len(sorted_values) - 1)
    lo = math.floor(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def bootstrap(data: Sequence, statistic: Callable[[list], float | None], n_resamples: int = 2000,
              seed: int = 0, confidence: float = 0.95) -> Bootstrap:
    """Percentile interval of `statistic` over resamples with replacement.

    A resample whose statistic is None (undefined) is skipped and not counted in n_valid.
    """
    if not data:
        raise ValueError("bootstrap needs data")
    rng = random.Random(seed)
    items = list(data)
    values = []
    for _ in range(n_resamples):
        value = statistic([items[rng.randrange(len(items))] for _ in items])
        if value is not None:
            values.append(value)
    values.sort()
    tail = (1 - confidence) / 2
    lo = _percentile(values, tail) if values else None
    hi = _percentile(values, 1 - tail) if values else None
    return Bootstrap(statistic(items), lo, hi, n_resamples, len(values), seed, confidence)


def chapman(n1: int, n2: int, m: int) -> float:
    """Chapman's bias-corrected Lincoln-Petersen estimate of the population size."""
    if min(n1, n2, m) < 0 or m > min(n1, n2):
        raise ValueError(f"need 0 <= m <= min(n1, n2) (n1={n1}, n2={n2}, m={m})")
    return (n1 + 1) * (n2 + 1) / (m + 1) - 1
