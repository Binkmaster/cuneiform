"""Tests for the scalar-representation side-channel leakage experiment.

The experiment's credibility rests on two things being true: every encoding
actually reconstructs the scalar it claims to (so we never measure the leakage
of the wrong number), and the residual-uncertainty metric matches an
independent brute-force count.  These tests check both, plus the headline
orderings the writeup relies on.
"""

import random

import pytest

from cuneiform.crypto.scalar_leakage import (
    binary_digits,
    naf_digits,
    base_window_digits,
    randomized_signed_binary,
    reconstruct,
    obs_binary_double_and_add,
    obs_constant_ladder,
    obs_naf,
    obs_window_hidden,
    obs_window_leaking,
    residual_uncertainty,
    dpa_distinct_traces,
    run_experiment,
    SCHEMES,
)


# --- representations reconstruct exactly ----------------------------------

@pytest.mark.parametrize("k", [1, 2, 7, 60, 61, 3599, 3600, 123456, 2**20 - 1])
def test_binary_reconstructs(k):
    assert reconstruct(binary_digits(k), 2) == k


@pytest.mark.parametrize("k", [1, 2, 7, 60, 61, 3599, 3600, 123456, 2**20 - 1])
def test_naf_reconstructs(k):
    assert reconstruct(naf_digits(k), 2) == k


@pytest.mark.parametrize("base", [16, 60])
@pytest.mark.parametrize("k", [1, 7, 60, 61, 3599, 3600, 123456])
def test_window_reconstructs(base, k):
    assert reconstruct(base_window_digits(k, base), base) == k


def test_naf_is_non_adjacent():
    for k in range(1, 5000):
        d = naf_digits(k)
        for i in range(len(d) - 1):
            assert not (d[i] != 0 and d[i + 1] != 0)


def test_naf_digits_are_signed_ternary():
    for k in range(1, 5000):
        assert set(naf_digits(k)) <= {-1, 0, 1}


def test_randomized_reconstructs():
    rng = random.Random(1)
    for k in [1, 7, 60, 61, 3599, 123456, 2**20 - 1]:
        for _ in range(25):
            assert reconstruct(randomized_signed_binary(k, rng), 2) == k


# --- metric matches an independent brute-force count ----------------------

def _brute_residual(n_bits, observable):
    """Independent reimplementation of the residual metric: group scalars by
    observable, average log2(group size). Kept deliberately naive."""
    import math
    from collections import Counter
    counts = Counter(observable(k)
                     for k in range(1 << (n_bits - 1), 1 << n_bits))
    total = 1 << (n_bits - 1)
    return sum(c * math.log2(c) for c in counts.values()) / total


@pytest.mark.parametrize("obs", [
    obs_binary_double_and_add,
    obs_constant_ladder,
    obs_naf,
    lambda k: obs_window_hidden(k, 16),
    lambda k: obs_window_hidden(k, 60),
    lambda k: obs_window_leaking(k, 60),
])
def test_metric_matches_bruteforce(obs):
    n = 12
    got = residual_uncertainty(n, obs)["mean_residual_bits"]
    assert got == pytest.approx(_brute_residual(n, obs))


# --- headline orderings the writeup asserts -------------------------------

def test_binary_double_and_add_leaks_everything():
    # Every scalar has a unique double-and-add trace: residual is ~0 bits.
    m = residual_uncertainty(12, obs_binary_double_and_add)
    assert m["mean_residual_bits"] == pytest.approx(0.0, abs=1e-9)
    assert m["leak_rate"] == pytest.approx(1.0, abs=1e-6)


def test_constant_ladder_leaks_almost_nothing():
    # Constant op-sequence hides everything but the bit length.
    m = residual_uncertainty(12, obs_constant_ladder)
    assert m["leak_rate"] < 0.05


def test_leaking_index_erases_the_base60_advantage():
    # base-60 window helps only while the lookup is hidden; if the table index
    # leaks, base-60 leaks the whole scalar just like binary double-and-add.
    hidden = residual_uncertainty(12, lambda k: obs_window_hidden(k, 60))
    leaking = residual_uncertainty(12, lambda k: obs_window_leaking(k, 60))
    assert hidden["mean_residual_bits"] > leaking["mean_residual_bits"] + 5
    assert leaking["leak_rate"] == pytest.approx(1.0, abs=1e-6)


def test_base60_not_better_than_base16():
    # Any radix > 2 window gets the same hidden-index protection; base 60 is
    # not special. Their leak rates should be close.
    b16 = residual_uncertainty(12, lambda k: obs_window_hidden(k, 16))
    b60 = residual_uncertainty(12, lambda k: obs_window_hidden(k, 60))
    assert abs(b16["leak_rate"] - b60["leak_rate"]) < 0.15


def test_naf_beats_binary_but_not_windowing():
    binary = residual_uncertainty(12, obs_binary_double_and_add)
    naf = residual_uncertainty(12, obs_naf)
    window = residual_uncertainty(12, lambda k: obs_window_hidden(k, 60))
    assert naf["mean_residual_bits"] > binary["mean_residual_bits"]
    assert window["mean_residual_bits"] > naf["mean_residual_bits"]


# --- DPA axis -------------------------------------------------------------

def test_randomized_gives_many_traces_for_one_secret():
    rng = random.Random(7)
    # A fixed secret should yield many distinct traces (defeats averaging).
    assert dpa_distinct_traces(0x9E3779B9, runs=200, rng=rng) > 20


# --- driver ---------------------------------------------------------------

def test_run_experiment_shape():
    r = run_experiment(n_bits=12, dpa_runs=50)
    assert len(r["schemes"]) == len(SCHEMES)
    assert r["dpa"]["randomized_mean_distinct_traces"] > 1
    # Binary double-and-add must be the worst (highest leak rate).
    worst = max(r["schemes"], key=lambda s: s["leak_rate"])
    assert "double-and-add" in worst["scheme"] or "LEAKING" in worst["scheme"]


def test_projection_not_zeroed_by_short_circuit():
    # A zero leak rate must project to the full key size, not collapse to 0.
    r = run_experiment(n_bits=12, dpa_runs=10)
    ladder = next(s for s in r["schemes"] if "ladder" in s["scheme"])
    assert ladder["projected_residual_at_crypto"] == pytest.approx(
        r["crypto_bits"] * (1 - ladder["leak_rate"]))
    assert ladder["projected_residual_at_crypto"] > 200
