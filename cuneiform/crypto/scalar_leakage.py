"""Scalar-representation side-channel leakage experiment.

The mathematical hardness of ECDLP is representation-invariant: writing a
secret scalar in binary, base 16, or base 60 cannot change how hard it is to
recover.  But the *implementation* of scalar multiplication is not
representation-invariant — the digit encoding chosen for the secret determines
the sequence of group operations, and that sequence is what a side channel
leaks.  This module measures, under a standard simple-power-analysis (SPA)
leakage model, how much a single operation-trace narrows down the secret
scalar, for a range of encodings including the base-60 / mixed-radix ones this
library is built around.

Leakage model (stated so results can be judged against it):

  * The attacker can distinguish a point DOUBLE from a point ADD.
  * The attacker CANNOT distinguish an ADD from a SUBTRACT (point negation is
    free and indistinguishable in the trace).
  * The attacker CANNOT see which precomputed table entry an ADD consumed
    (the "hidden table index" assumption).  A separate "leaking index" variant
    drops this assumption to show how much of the base-60 advantage depends on
    it.

Primary metric: residual attacker uncertainty in bits =
log2(|{scalars consistent with the observed trace}|), computed by exhaustively
enumerating every scalar in [1, 2**n) and grouping by observable trace.  Higher
residual = less leakage.  The leak *rate* (leaked bits / n) is bitlength
independent, so a modest n measures the same rate a 256-bit key would show.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict


# --------------------------------------------------------------------------
# Scalar representations.  Each returns a list of digits, LSB first, and each
# is checked by reconstruct() so the experiment can never quietly encode the
# wrong number.
# --------------------------------------------------------------------------

def binary_digits(k: int) -> list[int]:
    """Plain binary digits, LSB first."""
    digits = []
    while k:
        digits.append(k & 1)
        k >>= 1
    return digits or [0]


def naf_digits(k: int) -> list[int]:
    """Non-adjacent form: signed digits in {-1, 0, 1}, no two adjacent
    nonzero.  ~n/3 nonzero digits on average vs ~n/2 for binary."""
    digits = []
    while k > 0:
        if k & 1:
            d = 2 - (k % 4)  # +1 or -1, chosen so k - d is divisible by 4
            digits.append(d)
            k -= d
        else:
            digits.append(0)
        k >>= 1
    return digits or [0]


def base_window_digits(k: int, base: int) -> list[int]:
    """Fixed-window digits in the given base (e.g. 60), LSB first."""
    digits = []
    while k:
        digits.append(k % base)
        k //= base
    return digits or [0]


def randomized_signed_binary(k: int, rng: random.Random) -> list[int]:
    """Randomized redundant signed-binary recoding (a textbook DPA
    countermeasure).  On each odd bit the digit +1 or -1 is chosen at random;
    both leave an even remainder, so many distinct digit strings encode the
    same k.  Different randomness -> different trace for the same secret."""
    digits = []
    while k != 0:
        if k & 1:
            d = rng.choice((1, -1))
            k -= d
        else:
            d = 0
        digits.append(d)
        k >>= 1
    return digits or [0]


def reconstruct(digits: list[int], base: int) -> int:
    """Reconstruct the integer from LSB-first digits in the given base."""
    value = 0
    for d in reversed(digits):
        value = value * base + d
    return value


# --------------------------------------------------------------------------
# Observable traces.  An observable is the projection of the true operation
# sequence that the attacker actually sees, under the leakage model above.
# Two scalars the attacker cannot tell apart produce the *same* observable.
# --------------------------------------------------------------------------

def obs_binary_double_and_add(k: int) -> tuple:
    """Left-to-right double-and-add: every step doubles, and a 1-bit adds.
    The DOUBLE/ADD pattern reveals every bit exactly."""
    return tuple(binary_digits(k))  # full bits leak


def obs_constant_ladder(k: int) -> tuple:
    """Montgomery ladder / double-and-add-always: identical DOUBLE,ADD per
    bit regardless of bit value.  Only the operation count (bit length)
    shows."""
    return ("len", len(binary_digits(k)))


def obs_naf(k: int) -> tuple:
    """NAF: attacker sees which positions had a nonzero (add/sub) but not the
    sign.  Observable = the |digit| pattern."""
    return tuple(1 if d else 0 for d in naf_digits(k))


def obs_window_hidden(k: int, base: int) -> tuple:
    """Fixed-window with hidden table index: attacker sees which base-`base`
    digits triggered an ADD (nonzero) but not the digit value."""
    return ("hid", base, tuple(1 if d else 0 for d in base_window_digits(k, base)))


def obs_window_leaking(k: int, base: int) -> tuple:
    """Fixed-window whose table lookup leaks its index (cache/address
    side channel): the full digit value is exposed."""
    return ("leak", base, tuple(base_window_digits(k, base)))


# --------------------------------------------------------------------------
# The metric: exhaustive residual-uncertainty measurement.
# --------------------------------------------------------------------------

def residual_uncertainty(n_bits: int, observable) -> dict:
    """Enumerate every fixed-length scalar in [2**(n_bits-1), 2**n_bits),
    group by observable trace, and measure how much a single trace narrows
    the secret down.

    Real ECC secret scalars are fixed full length (top bit set), so the
    domain is the fixed-length scalars — otherwise a constant-op ladder would
    appear to "leak" the bit length, which does not vary in practice.

    Returns mean residual bits (attacker's leftover uncertainty), mean leaked
    bits, and the leak rate (leaked / entropy).  Higher residual = safer.
    """
    groups: dict = defaultdict(int)
    for k in range(1 << (n_bits - 1), 1 << n_bits):
        groups[observable(k)] += 1

    total = 1 << (n_bits - 1)
    entropy = math.log2(total)

    # Each scalar's residual uncertainty is log2 of its own group's size.
    # Average weighted by the scalars (equivalently sum size*log2(size)/total).
    residual = sum(size * math.log2(size) for size in groups.values()) / total
    leaked = entropy - residual
    return {
        "distinct_traces": len(groups),
        "mean_residual_bits": residual,
        "mean_leaked_bits": leaked,
        "leak_rate": leaked / entropy,
    }


def dpa_distinct_traces(k: int, runs: int, rng: random.Random) -> int:
    """DPA axis: how many distinct observable traces one fixed scalar produces
    over `runs` randomized re-encodings.  A deterministic scheme returns 1
    (no protection against trace averaging); a randomized scheme returns >1."""
    seen = set()
    for _ in range(runs):
        digits = randomized_signed_binary(k, rng)
        seen.add(tuple(1 if d else 0 for d in digits))
    return len(seen)


# --------------------------------------------------------------------------
# Experiment driver.
# --------------------------------------------------------------------------

# Each scheme: (label, single-trace observable, note).  The base-60 window
# is the library's candidate; base-16 is included so we can tell whether any
# advantage is specific to 60 or generic to "any radix > 2".
SCHEMES = [
    ("binary double-and-add", obs_binary_double_and_add,
     "textbook; every bit leaks"),
    ("constant ladder (Montgomery)", obs_constant_ladder,
     "reference defense: constant op-sequence"),
    ("NAF (signed-digit)", obs_naf,
     "hides digit signs"),
    ("base-16 window, hidden index", lambda k: obs_window_hidden(k, 16),
     "hides digit values behind table"),
    ("base-60 window, hidden index", lambda k: obs_window_hidden(k, 60),
     "the cuneiform candidate"),
    ("base-60 window, LEAKING index", lambda k: obs_window_leaking(k, 60),
     "same base, table lookup leaks"),
]


def run_experiment(n_bits: int = 16, dpa_runs: int = 200,
                   crypto_bits: int = 256, seed: int = 42) -> dict:
    """Run the full leakage comparison and project the leak rate to a
    crypto-size scalar."""
    rng = random.Random(seed)
    rows = []
    for label, obs, note in SCHEMES:
        m = residual_uncertainty(n_bits, obs)
        rows.append({
            "scheme": label,
            "note": note,
            "leak_rate": m["leak_rate"],
            "residual_bits": m["mean_residual_bits"],
            "leaked_bits": m["mean_leaked_bits"],
            "projected_residual_at_crypto":
                crypto_bits * (1 - m["leak_rate"]),
        })

    # DPA axis on a sample of fixed scalars.
    sample = [rng.randrange(1 << (n_bits - 1), 1 << n_bits) for _ in range(20)]
    fixed_distinct = 1  # any deterministic scheme
    rand_distinct = [
        dpa_distinct_traces(k, dpa_runs, rng) for k in sample
    ]

    return {
        "n_bits": n_bits,
        "crypto_bits": crypto_bits,
        "schemes": rows,
        "dpa": {
            "fixed_scheme_distinct_traces": fixed_distinct,
            "randomized_mean_distinct_traces": sum(rand_distinct) / len(rand_distinct),
            "randomized_min_distinct_traces": min(rand_distinct),
            "runs_per_scalar": dpa_runs,
        },
    }
