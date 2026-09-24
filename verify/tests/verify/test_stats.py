"""Exact binomial bounds, Cohen's kappa, a seeded bootstrap and the Chapman estimator."""
from __future__ import annotations
import math

import pytest

from tools.verify import stats


@pytest.mark.parametrize("n,upper", [(7, 0.348), (20, 0.139), (34, 0.0843), (38, 0.0758)])
def test_zero_error_upper_bound_matches_the_plan(n, upper):
    # 0 errors, one-sided 95%: 1 - 0.05 ** (1 / n)
    assert stats.upper_bound(0, n) == pytest.approx(upper, abs=5e-4)
    assert stats.upper_bound(0, n) == pytest.approx(1 - 0.05 ** (1 / n), rel=1e-6)


def test_clopper_pearson_two_sided_known_values():
    lo, hi = stats.clopper_pearson(5, 20)
    # Reference values of the exact interval for 5/20 at 95%.
    assert lo == pytest.approx(0.0866, abs=5e-4)
    assert hi == pytest.approx(0.4910, abs=5e-4)


def test_clopper_pearson_edges():
    assert stats.clopper_pearson(0, 10)[0] == 0.0
    assert stats.clopper_pearson(10, 10)[1] == 1.0
    lo, hi = stats.clopper_pearson(0, 10)
    assert hi == pytest.approx(1 - 0.025 ** (1 / 10), rel=1e-6)


def test_bounds_are_monotone_in_k():
    his = [stats.upper_bound(k, 30) for k in range(31)]
    assert his == sorted(his) and his[-1] == 1.0
    assert stats.lower_bound(0, 30) == 0.0
    assert stats.lower_bound(30, 30) == pytest.approx(0.05 ** (1 / 30), rel=1e-6)


@pytest.mark.parametrize("k,n", [(-1, 5), (6, 5), (0, 0)])
def test_bounds_reject_bad_counts(k, n):
    with pytest.raises(ValueError):
        stats.clopper_pearson(k, n)


def test_confidence_must_be_a_probability():
    with pytest.raises(ValueError):
        stats.upper_bound(0, 10, confidence=1.0)


def test_kappa_known_value():
    # Classic 2x2 example: po = 0.7, pe = 0.5 -> kappa = 0.4
    a = ["y"] * 20 + ["y"] * 5 + ["n"] * 10 + ["n"] * 15
    b = ["y"] * 20 + ["n"] * 5 + ["y"] * 10 + ["n"] * 15
    assert stats.cohen_kappa(a, b) == pytest.approx(0.4)


def test_kappa_perfect_and_chance():
    labels = ["supports", "refutes", "insufficient"] * 4
    assert stats.cohen_kappa(labels, labels) == pytest.approx(1.0)
    assert stats.cohen_kappa(["a", "b", "a", "b"], ["a", "a", "b", "b"]) == pytest.approx(0.0)


def test_kappa_undefined_when_chance_agreement_is_one():
    assert stats.cohen_kappa(["a", "a"], ["a", "a"]) is None


def test_kappa_needs_paired_labels():
    with pytest.raises(ValueError, match="paired"):
        stats.cohen_kappa(["a"], ["a", "b"])
    with pytest.raises(ValueError):
        stats.cohen_kappa([], [])


def test_bootstrap_is_seeded_and_brackets_the_point():
    data = [0, 1] * 25
    mean = lambda xs: sum(xs) / len(xs)
    one = stats.bootstrap(data, mean, n_resamples=500, seed=7)
    two = stats.bootstrap(data, mean, n_resamples=500, seed=7)
    assert one == two
    assert one.point == 0.5 and one.lo <= 0.5 <= one.hi and one.n_valid == 500
    assert stats.bootstrap(data, mean, n_resamples=500, seed=8) != one


def test_bootstrap_skips_undefined_statistics():
    res = stats.bootstrap([("a", "a")] * 3, lambda xs: None, n_resamples=50, seed=1)
    assert res.n_valid == 0 and res.lo is None and res.hi is None and res.point is None


def test_bootstrap_of_paired_kappa():
    pairs = [("s", "s")] * 12 + [("i", "i")] * 6 + [("s", "i")] * 2
    kappa = lambda ps: stats.cohen_kappa([a for a, _ in ps], [b for _, b in ps])
    res = stats.bootstrap(pairs, kappa, n_resamples=300, seed=20260922)
    assert res.point == pytest.approx(kappa(pairs))
    assert 0 < res.n_valid <= 300 and res.lo <= res.point <= res.hi


def test_chapman():
    assert stats.chapman(44, 7, 5) == pytest.approx((45 * 8) / 6 - 1)
    assert stats.chapman(10, 10, 0) == pytest.approx(120.0)
    with pytest.raises(ValueError):
        stats.chapman(5, 5, 6)


def test_stats_is_stdlib_only():
    import pathlib
    src = pathlib.Path(stats.__file__).read_text(encoding="utf-8")
    for mod in ("numpy", "scipy", "statsmodels"):
        assert f"import {mod}" not in src and f"from {mod}" not in src
    assert not math.isnan(stats.upper_bound(0, 1))
